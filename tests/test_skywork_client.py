"""
SPEC-SKYWORK-001: Skywork 클라이언트 단위 테스트

테스트 시나리오:
- TC-001: SkyworkConfig 서명 생성
- TC-002: URL 검증
- TC-003: SSE 연결 및 엔드포인트 발견
- TC-004: JSON-RPC 핸드셰이크
- TC-005: 도구 호출
- TC-006: 오류 처리 및 재시도
- TC-007: 리소스 정리
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skywork.client import (
    EndpointDiscoveryError,
    RPCError,
    SSEConnectionError,
    SkyworkClient,
    SkyworkClientError,
    SkyworkConfig,
    call_skywork_tool,
    validate_endpoint_url,
)


class TestSkyworkConfig:
    """TC-001: SkyworkConfig 테스트"""

    def test_generate_signature(self):
        """MD5 서명 생성 테스트"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        signature = config.generate_signature()

        # MD5 해시는 32자
        assert len(signature) == 32
        # 일관된 결과
        assert signature == config.generate_signature()

    def test_generate_signature_different_keys(self):
        """다른 키는 다른 서명 생성"""
        config1 = SkyworkConfig(secret_id="id1", secret_key="key1")
        config2 = SkyworkConfig(secret_id="id2", secret_key="key2")

        assert config1.generate_signature() != config2.generate_signature()

    def test_get_sse_url(self):
        """SSE URL 생성 테스트"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        url = config.get_sse_url()

        assert "https://api.skywork.ai/open/sse" in url
        assert "secret_id=test_id" in url
        assert "sign=" in url

    def test_default_values(self):
        """기본값 테스트"""
        config = SkyworkConfig(secret_id="id", secret_key="key")

        assert config.base_url == "https://api.skywork.ai/open/sse"
        assert config.endpoint_timeout == 10.0
        assert config.request_timeout == 300.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0


class TestValidateEndpointUrl:
    """TC-002: URL 검증 테스트"""

    def test_valid_same_host(self):
        """동일 호스트 URL은 유효"""
        base = "https://api.skywork.ai/open/sse"
        url = "https://api.skywork.ai/rpc/endpoint"

        assert validate_endpoint_url(url, base) is True

    def test_invalid_different_host(self):
        """다른 호스트 URL은 무효"""
        base = "https://api.skywork.ai/open/sse"
        url = "https://evil.com/rpc/endpoint"

        assert validate_endpoint_url(url, base) is False

    def test_invalid_scheme(self):
        """잘못된 스킴은 무효"""
        base = "https://api.skywork.ai/open/sse"
        url = "ftp://api.skywork.ai/rpc/endpoint"

        assert validate_endpoint_url(url, base) is False

    def test_http_scheme_allowed(self):
        """HTTP 스킴 허용"""
        base = "http://api.skywork.ai/open/sse"
        url = "http://api.skywork.ai/rpc/endpoint"

        assert validate_endpoint_url(url, base) is True

    def test_malformed_url(self):
        """잘못된 형식의 URL 처리"""
        base = "https://api.skywork.ai/open/sse"
        url = "not-a-valid-url"

        # 예외 없이 False 반환
        assert validate_endpoint_url(url, base) is False


class TestSkyworkClientExceptions:
    """예외 클래스 테스트"""

    def test_exception_hierarchy(self):
        """예외 상속 구조 확인"""
        assert issubclass(SSEConnectionError, SkyworkClientError)
        assert issubclass(EndpointDiscoveryError, SkyworkClientError)
        assert issubclass(RPCError, SkyworkClientError)

    def test_exception_messages(self):
        """예외 메시지 확인"""
        error = SSEConnectionError("Test error")
        assert str(error) == "Test error"


class TestSkyworkClientConnect:
    """TC-003: SSE 연결 테스트"""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """SSE 연결 성공 시나리오"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        # Mock SSE 응답 - aiter_lines는 async iterator를 직접 반환해야 함
        mock_response = MagicMock()
        mock_response.aiter_lines = lambda: async_iter(
            ["data: /rpc/endpoint123", "data: "]
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(
                return_value=AsyncContextManager(mock_response)
            )
            mock_client_class.return_value = mock_client

            await client.connect()

            assert client._endpoint == "https://api.skywork.ai/rpc/endpoint123"

        await client.close()

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """엔드포인트 발견 타임아웃"""
        config = SkyworkConfig(
            secret_id="test_id", secret_key="test_key", endpoint_timeout=0.1
        )
        client = SkyworkClient(config)

        # 빈 응답 (엔드포인트 없음)
        mock_response = MagicMock()
        mock_response.aiter_lines = lambda: async_iter([])

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(
                return_value=AsyncContextManager(mock_response)
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(SSEConnectionError) as exc_info:
                await client.connect()

            assert "Failed to connect after" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_connect_retry(self):
        """재시도 로직 테스트"""
        config = SkyworkConfig(
            secret_id="test_id",
            secret_key="test_key",
            max_retries=2,
            retry_delay=0.01,
            endpoint_timeout=0.1,
        )
        client = SkyworkClient(config)

        # 빈 응답 (항상 실패)
        mock_response = MagicMock()
        mock_response.aiter_lines = lambda: async_iter([])

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(
                return_value=AsyncContextManager(mock_response)
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(SSEConnectionError):
                await client.connect()

        await client.close()


class TestSkyworkClientRPC:
    """TC-004, TC-005: JSON-RPC 테스트"""

    @pytest.mark.asyncio
    async def test_send_rpc_success(self):
        """RPC 요청 성공"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        # 클라이언트 상태 설정
        client._client = AsyncMock()
        client._endpoint = "https://api.skywork.ai/rpc/test"

        # RPC 응답 시뮬레이션
        async def set_response():
            await asyncio.sleep(0.01)
            if 1 in client._futures:
                client._futures[1].set_result(
                    {"jsonrpc": "2.0", "id": 1, "result": "ok"}
                )

        asyncio.create_task(set_response())

        result = await client._send_rpc("test_method", {"key": "value"}, request_id=1)

        assert result["result"] == "ok"
        # futures 정리 확인
        assert 1 not in client._futures

        await client.close()

    @pytest.mark.asyncio
    async def test_send_rpc_not_connected(self):
        """연결되지 않은 상태에서 RPC 호출"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        with pytest.raises(RPCError) as exc_info:
            await client._send_rpc("test_method")

        assert "not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """도구 호출 성공"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        client._client = AsyncMock()
        client._endpoint = "https://api.skywork.ai/rpc/test"

        # 응답 시뮬레이션
        async def set_response():
            await asyncio.sleep(0.01)
            if 3 in client._futures:
                client._futures[3].set_result(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "result": {
                            "content": [
                                {"type": "text", "text": "Generated document content"}
                            ]
                        },
                    }
                )

        asyncio.create_task(set_response())

        result = await client.call_tool("gen_doc", "Create a report")

        assert result == "Generated document content"

        await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_empty_response(self):
        """빈 응답 처리"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        client._client = AsyncMock()
        client._endpoint = "https://api.skywork.ai/rpc/test"

        async def set_response():
            await asyncio.sleep(0.01)
            if 3 in client._futures:
                client._futures[3].set_result(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "result": {"content": []},
                    }
                )

        asyncio.create_task(set_response())

        result = await client.call_tool("gen_doc", "query")

        assert "no text content" in result

        await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_error_response(self):
        """오류 응답 처리"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        client._client = AsyncMock()
        client._endpoint = "https://api.skywork.ai/rpc/test"

        async def set_response():
            await asyncio.sleep(0.01)
            if 3 in client._futures:
                client._futures[3].set_result(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "error": {"code": -32000, "message": "Tool execution failed"},
                    }
                )

        asyncio.create_task(set_response())

        result = await client.call_tool("gen_doc", "query")

        assert "Error:" in result
        assert "Tool execution failed" in result

        await client.close()


class TestSkyworkClientCleanup:
    """TC-007: 리소스 정리 테스트"""

    @pytest.mark.asyncio
    async def test_close_cleans_resources(self):
        """close()가 모든 리소스를 정리"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")
        client = SkyworkClient(config)

        # 상태 설정
        client._client = AsyncMock()
        client._endpoint = "https://test.endpoint"
        client._futures = {1: asyncio.Future(), 2: asyncio.Future()}
        client._listener_task = asyncio.create_task(asyncio.sleep(10))

        await client.close()

        assert client._client is None
        assert client._endpoint is None
        assert len(client._futures) == 0
        assert client._listener_task is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """async with 컨텍스트 매니저"""
        config = SkyworkConfig(secret_id="test_id", secret_key="test_key")

        mock_response = MagicMock()
        mock_response.aiter_lines = lambda: async_iter(["data: /rpc/endpoint"])

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(
                return_value=AsyncContextManager(mock_response)
            )
            mock_client_class.return_value = mock_client

            async with SkyworkClient(config) as client:
                assert client._endpoint is not None

            # 종료 후 정리 확인
            assert client._endpoint is None


class TestCallSkyworkToolHelper:
    """call_skywork_tool 편의 함수 테스트"""

    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        """자격 증명 누락 시 오류"""
        with patch.dict("os.environ", {}, clear=True):
            result = await call_skywork_tool("gen_doc", "query")

        assert "Error:" in result
        assert "SKYWORK_SECRET_ID" in result

    @pytest.mark.asyncio
    async def test_with_provided_credentials(self):
        """제공된 자격 증명 사용 - 자격 증명이 올바르게 전달되는지 확인"""
        # skywork.client 모듈 내부의 httpx.AsyncClient를 패치해야 함
        mock_response = MagicMock()
        mock_response.aiter_lines = lambda: async_iter(["data: /rpc/endpoint"])

        with patch("skywork.client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(
                return_value=AsyncContextManager(mock_response)
            )
            # post 메서드도 mock해서 RPC 호출이 실패하도록 설정
            mock_client.post = AsyncMock(side_effect=Exception("RPC timeout"))
            mock_client_class.return_value = mock_client

            # 타임아웃 오류 예상 (RPC 호출이 실패하므로)
            result = await call_skywork_tool(
                "gen_doc", "query", secret_id="id", secret_key="key"
            )

            # 자격 증명 오류가 아닌 다른 오류임을 확인
            assert "SKYWORK_SECRET_ID" not in result
            assert "Error" in result  # RPC 오류 발생


# 헬퍼 함수들


async def async_iter(items):
    """비동기 이터레이터 헬퍼"""
    for item in items:
        yield item


class AsyncContextManager:
    """비동기 컨텍스트 매니저 헬퍼"""

    def __init__(self, mock_response):
        self.mock_response = mock_response

    async def __aenter__(self):
        return self.mock_response

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        pass
