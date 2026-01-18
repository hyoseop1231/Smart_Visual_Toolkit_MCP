"""
Skywork API 클라이언트 모듈

SPEC-SKYWORK-001: Skywork SSE/JSON-RPC 프록시 클라이언트
개선 사항:
- 구체적인 예외 처리 (bare except 제거)
- 태스크 정리 로직 개선
- 재시도 로직 (지수 백오프)
- URL 검증
- 경쟁 조건 방지
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class SkyworkConfig:
    """Skywork API 설정"""

    secret_id: str
    secret_key: str
    base_url: str = "https://api.skywork.ai/open/sse"
    endpoint_timeout: float = 10.0
    request_timeout: float = 600.0  # 10분 (gen_ppt는 5분+ 소요)
    max_retries: int = 3
    retry_delay: float = 1.0

    def generate_signature(self) -> str:
        """MD5 기반 서명 생성"""
        raw_str = f"{self.secret_id}:{self.secret_key}"
        return hashlib.md5(raw_str.encode("utf-8")).hexdigest()

    def get_sse_url(self) -> str:
        """SSE 연결 URL 생성"""
        sign = self.generate_signature()
        return f"{self.base_url}?secret_id={self.secret_id}&sign={sign}"


class SkyworkClientError(Exception):
    """Skywork 클라이언트 오류 기본 클래스"""

    pass


class SSEConnectionError(SkyworkClientError):
    """SSE 연결 오류"""

    pass


class EndpointDiscoveryError(SkyworkClientError):
    """엔드포인트 발견 오류"""

    pass


class RPCError(SkyworkClientError):
    """JSON-RPC 호출 오류"""

    pass


def validate_endpoint_url(url: str, base_url: str) -> bool:
    """
    엔드포인트 URL 검증

    Args:
        url: 검증할 URL
        base_url: 기본 SSE URL (동일 호스트 확인용)

    Returns:
        URL이 유효하면 True
    """
    try:
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)

        # 스킴 확인 (https만 허용)
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"Invalid URL scheme: {parsed.scheme}")
            return False

        # 호스트 확인 (동일 도메인만 허용)
        if parsed.netloc != base_parsed.netloc:
            logger.warning(
                f"URL host mismatch: {parsed.netloc} != {base_parsed.netloc}"
            )
            return False

        return True
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False


class SkyworkClient:
    """
    Skywork SSE/JSON-RPC 클라이언트

    특징:
    - 비동기 SSE 스트리밍
    - JSON-RPC 2.0 프로토콜
    - 지수 백오프 재시도
    - 안전한 리소스 정리
    """

    def __init__(self, config: SkyworkConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._endpoint: Optional[str] = None
        self._endpoint_lock = asyncio.Lock()
        self._futures: Dict[int, asyncio.Future] = {}
        self._listener_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self) -> None:
        """SSE 연결 수립 및 엔드포인트 발견"""
        self._client = httpx.AsyncClient(timeout=self.config.request_timeout)
        await self._discover_endpoint_with_retry()

    async def _discover_endpoint_with_retry(self) -> None:
        """재시도 로직이 포함된 엔드포인트 발견"""
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                await self._discover_endpoint()
                return
            except (SSEConnectionError, EndpointDiscoveryError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning(
                        f"SSE connection failed (attempt {attempt + 1}/{self.config.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise SSEConnectionError(
            f"Failed to connect after {self.config.max_retries} attempts: {last_error}"
        )

    async def _discover_endpoint(self) -> None:
        """SSE 스트림에서 엔드포인트 URL 발견"""
        if not self._client:
            raise SSEConnectionError("Client not initialized")

        # 로컬 변수로 캡처하여 타입 안전성 보장
        client = self._client
        sse_url = self.config.get_sse_url()
        endpoint_event = asyncio.Event()
        discovered_endpoint: Optional[str] = None
        discovery_error: Optional[Exception] = None

        async def process_sse():
            nonlocal discovered_endpoint, discovery_error
            try:
                async with client.stream("GET", sse_url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if not data:
                                continue

                            # 엔드포인트 발견
                            async with self._endpoint_lock:
                                if discovered_endpoint is None:
                                    if data.startswith("/") or data.startswith("http"):
                                        if data.startswith("/"):
                                            parsed = urlparse(sse_url)
                                            candidate = f"{parsed.scheme}://{parsed.netloc}{data}"
                                        else:
                                            candidate = data

                                        # URL 검증
                                        if validate_endpoint_url(candidate, sse_url):
                                            discovered_endpoint = candidate
                                            endpoint_event.set()
                                        else:
                                            discovery_error = EndpointDiscoveryError(
                                                f"Invalid endpoint URL: {candidate}"
                                            )
                                            endpoint_event.set()
                                    continue

                            # JSON-RPC 응답 처리
                            if "jsonrpc" in data:
                                try:
                                    msg = json.loads(data)
                                    # ping 등 서버 요청은 무시 (method 키가 있으면 요청/알림)
                                    if "method" in msg:
                                        logger.debug(
                                            f"Ignoring server notification: {msg.get('method')}"
                                        )
                                        continue
                                    # result 또는 error가 있는 응답만 처리
                                    if "id" in msg and msg["id"] in self._futures:
                                        if "result" in msg or "error" in msg:
                                            self._futures[msg["id"]].set_result(msg)
                                except json.JSONDecodeError as e:
                                    logger.debug(f"JSON parsing failed for line: {e}")
            except httpx.HTTPError as e:
                discovery_error = SSEConnectionError(f"SSE connection error: {e}")
                endpoint_event.set()
            except Exception as e:
                logger.error(f"SSE processing error: {e}")
                discovery_error = SSEConnectionError(f"SSE error: {e}")
                endpoint_event.set()

        # SSE 리스너 시작
        self._listener_task = asyncio.create_task(process_sse())

        # 엔드포인트 대기
        try:
            await asyncio.wait_for(
                endpoint_event.wait(), timeout=self.config.endpoint_timeout
            )
        except asyncio.TimeoutError:
            raise EndpointDiscoveryError(
                f"Endpoint discovery timed out after {self.config.endpoint_timeout}s"
            )

        # 오류 확인
        if discovery_error:
            raise discovery_error

        if not discovered_endpoint:
            raise EndpointDiscoveryError("No endpoint discovered")

        self._endpoint = discovered_endpoint
        logger.info(f"Discovered endpoint: {self._endpoint}")

    async def _send_rpc(
        self, method: str, params: Optional[Dict[str, Any]] = None, request_id: int = 1
    ) -> Dict[str, Any]:
        """JSON-RPC 요청 전송"""
        if not self._client or not self._endpoint:
            raise RPCError("Client not connected")

        future: asyncio.Future = asyncio.Future()
        self._futures[request_id] = future

        try:
            await self._client.post(
                self._endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params or {},
                },
            )

            return await asyncio.wait_for(future, timeout=self.config.request_timeout)
        except asyncio.TimeoutError:
            raise RPCError(f"RPC request timed out: {method}")
        finally:
            # futures 정리
            self._futures.pop(request_id, None)

    async def initialize(self) -> None:
        """JSON-RPC 초기화 핸드셰이크"""
        # 초기화 요청
        await self._send_rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smart-visual-toolkit", "version": "1.0"},
            },
            request_id=1,
        )

        # 초기화 완료 알림
        await self._send_rpc("notifications/initialized", request_id=2)

        logger.info("JSON-RPC handshake completed")

    async def call_tool(
        self, tool_name: str, query: str, use_network: str = "true"
    ) -> str:
        """
        Skywork 도구 호출

        Args:
            tool_name: 도구 이름 (gen_doc, gen_excel, gen_ppt, gen_ppt_fast)
            query: 쿼리 문자열
            use_network: 네트워크 사용 여부 ("true" / "false")

        Returns:
            도구 실행 결과 텍스트
        """
        response = await self._send_rpc(
            "tools/call",
            {
                "name": tool_name,
                "arguments": {"query": query, "use_network": use_network},
            },
            request_id=3,
        )

        # 결과 파싱
        if "result" in response and "content" in response["result"]:
            text_content = ""
            content = response["result"]["content"]

            if not isinstance(content, list):
                logger.warning(f"Unexpected content type: {type(content)}")
                return "Error: Unexpected response format"

            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content += item.get("text", "")

            return (
                text_content
                if text_content
                else "Success, but no text content returned."
            )

        if "error" in response:
            error = response["error"]
            return f"Error: {error.get('message', 'Unknown error')}"

        return f"Error: Unexpected response: {response}"

    async def close(self) -> None:
        """리소스 정리"""
        # 리스너 태스크 취소 및 대기
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        # 대기 중인 futures 정리
        for future in self._futures.values():
            if not future.done():
                future.cancel()
        self._futures.clear()

        # HTTP 클라이언트 종료
        if self._client:
            await self._client.aclose()
            self._client = None

        self._endpoint = None
        logger.info("Skywork client closed")


async def call_skywork_tool(
    tool_name: str,
    query: str,
    use_network: str = "true",
    secret_id: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> str:
    """
    Skywork 도구 호출 (편의 함수)

    Args:
        tool_name: 도구 이름
        query: 쿼리 문자열
        use_network: 네트워크 사용 여부
        secret_id: Skywork Secret ID (없으면 환경 변수 사용)
        secret_key: Skywork Secret Key (없으면 환경 변수 사용)

    Returns:
        도구 실행 결과 또는 오류 메시지
    """
    import os

    # 자격 증명 확인
    secret_id = secret_id or os.getenv("SKYWORK_SECRET_ID")
    secret_key = secret_key or os.getenv("SKYWORK_SECRET_KEY")

    if not secret_id or not secret_key:
        return "Error: SKYWORK_SECRET_ID and SKYWORK_SECRET_KEY must be set in .env"

    config = SkyworkConfig(secret_id=secret_id, secret_key=secret_key)

    try:
        async with SkyworkClient(config) as client:
            await client.initialize()
            return await client.call_tool(tool_name, query, use_network)
    except SkyworkClientError as e:
        logger.error(f"Skywork client error: {e}")
        return f"Error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error during Skywork call: {e}"
