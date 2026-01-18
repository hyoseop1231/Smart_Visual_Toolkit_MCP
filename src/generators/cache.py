"""
이미지 생성 캐싱 모듈

SPEC-CACHE-001: 동일한 프롬프트/스타일/비율 조합에 대해
중복 API 호출을 방지하는 캐싱 레이어 구현

핵심 기능:
- SHA-256 기반 캐시 키 생성
- LRU (Least Recently Used) 정책
- TTL (Time-To-Live) 기반 만료
- 스레드 안전성 (RLock)
"""

import hashlib
import time
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Any, Optional


def generate_cache_key(
    prompt: str,
    style: str,
    aspect_ratio: str = "16:9",
    format: str = "png",
    quality: int = 95,
) -> str:
    """
    캐시 키 생성 - SHA-256 해시 사용

    입력값을 정규화하여 일관된 해시 키를 생성합니다.
    - 앞뒤 공백 제거
    - 소문자 변환 (prompt, style, format)
    - 파이프(|) 구분자로 연결

    Args:
        prompt: 이미지 생성 프롬프트
        style: 스타일 이름
        aspect_ratio: 화면 비율 (기본값: "16:9")
        format: 이미지 형식 (기본값: "png")
        quality: 이미지 품질 (기본값: 95)

    Returns:
        64자 16진수 해시 문자열
    """
    normalized_prompt = prompt.strip().lower()
    normalized_style = style.strip().lower()
    normalized_ratio = aspect_ratio.strip()
    normalized_format = format.strip().lower()

    key_source = (
        f"{normalized_prompt}|{normalized_style}|{normalized_ratio}|"
        f"{normalized_format}|{quality}"
    )
    return hashlib.sha256(key_source.encode("utf-8")).hexdigest()


def generate_cache_key_advanced(
    prompt: str,
    style: str,
    aspect_ratio: str = "16:9",
    format: str = "png",
    quality: int = 95,
    width: Optional[int] = None,
    height: Optional[int] = None,
    negative_prompt: Optional[str] = None,
    style_intensity: str = "normal",
    enhance_prompt: bool = True,
) -> str:
    """
    고급 기능용 캐시 키 생성

    generate_cache_key()를 확장하여 추가 파라미터들을 포함합니다.

    Args:
        prompt: 이미지 생성 프롬프트
        style: 스타일 이름
        aspect_ratio: 화면 비율 (기본값: "16:9")
        format: 이미지 형식 (기본값: "png")
        quality: 이미지 품질 (기본값: 95)
        width: 사용자 정의 너비 (선택)
        height: 사용자 정의 높이 (선택)
        negative_prompt: 네거티브 프롬프트 (선택)
        style_intensity: 스타일 강도 (기본값: "normal")
        enhance_prompt: 프롬프트 강화 활성화 (기본값: True)

    Returns:
        64자 16진수 해시 문자열
    """
    normalized_prompt = prompt.strip().lower()
    normalized_style = style.strip().lower()
    normalized_ratio = aspect_ratio.strip()
    normalized_format = format.strip().lower()

    # 선택적 파라미터 정규화
    width_str = str(width) if width else "none"
    height_str = str(height) if height else "none"
    normalized_negative = negative_prompt.strip().lower() if negative_prompt else "none"

    key_source = (
        f"{normalized_prompt}|{normalized_style}|{normalized_ratio}|"
        f"{normalized_format}|{quality}|{width_str}x{height_str}|"
        f"{normalized_negative}|{style_intensity}|{enhance_prompt}"
    )
    return hashlib.sha256(key_source.encode("utf-8")).hexdigest()


@dataclass
class CacheEntry:
    """캐시 항목 데이터 클래스"""

    key: str
    result: Dict[str, Any]
    created_at: float
    expires_at: float

    def is_expired(self) -> bool:
        """TTL 만료 여부 확인"""
        return time.time() > self.expires_at


class ImageCache:
    """
    LRU + TTL 기반 이미지 캐시

    특징:
    - OrderedDict를 사용한 LRU 구현
    - TTL 기반 자동 만료
    - RLock을 사용한 스레드 안전성
    - Hit/Miss 통계 수집
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        캐시 초기화

        Args:
            max_size: 최대 캐시 항목 수 (기본값: 100)
            ttl_seconds: 캐시 만료 시간(초) (기본값: 3600 = 1시간)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

        # 통계 카운터
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        캐시에서 항목 조회

        - 키가 존재하면 LRU 순서 업데이트 후 반환
        - TTL 만료된 항목은 삭제 후 None 반환
        - 키가 없으면 None 반환

        Args:
            key: 캐시 키 (generate_cache_key()로 생성)

        Returns:
            캐시된 결과 딕셔너리 또는 None
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # TTL 만료 검사
                if entry.is_expired():
                    del self._cache[key]
                    self._misses += 1
                    return None

                # LRU 순서 업데이트: 가장 최근 사용으로 이동
                self._cache.move_to_end(key)
                self._hits += 1
                return entry.result

            self._misses += 1
            return None

    def set(self, key: str, result: Dict[str, Any]) -> None:
        """
        캐시에 항목 저장

        - 용량 초과 시 LRU 정책으로 가장 오래된 항목 제거
        - TTL 설정과 함께 저장

        Args:
            key: 캐시 키
            result: 저장할 결과 딕셔너리
        """
        with self._lock:
            # 기존 항목이 있으면 삭제 (업데이트를 위해)
            if key in self._cache:
                del self._cache[key]

            # 용량 초과 시 가장 오래된 항목(first=False의 반대) 제거
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            # 새 항목 추가
            now = time.time()
            self._cache[key] = CacheEntry(
                key=key,
                result=result,
                created_at=now,
                expires_at=now + self._ttl_seconds,
            )

    def invalidate(self, key: str) -> bool:
        """
        특정 키의 캐시 무효화

        Args:
            key: 삭제할 캐시 키

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        전체 캐시 초기화

        Returns:
            삭제된 항목 수
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회

        Returns:
            통계 딕셔너리 (hits, misses, hit_rate_percent, cache_size, max_size)
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_size": len(self._cache),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl_seconds,
            }

    @property
    def size(self) -> int:
        """현재 캐시 크기"""
        with self._lock:
            return len(self._cache)
