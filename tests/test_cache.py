"""
SPEC-CACHE-001: 캐시 모듈 단위 테스트

테스트 시나리오:
- TC-001: 캐시 키 생성 일관성
- TC-002: 캐시 HIT 시나리오
- TC-003: 캐시 MISS 및 저장
- TC-004: TTL 만료
- TC-005: LRU 정책
- TC-006: 스레드 안전성
- TC-007: 캐시 무효화
- TC-008: 캐시 통계
"""

import time
import threading
import sys
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generators.cache import generate_cache_key, ImageCache, CacheEntry


class TestGenerateCacheKey:
    """TC-001: 캐시 키 생성 테스트"""

    def test_same_input_same_hash(self):
        """동일 입력은 동일 해시 생성"""
        key1 = generate_cache_key("a cat", "realistic", "16:9")
        key2 = generate_cache_key("a cat", "realistic", "16:9")
        assert key1 == key2

    def test_different_input_different_hash(self):
        """다른 입력은 다른 해시 생성"""
        key1 = generate_cache_key("a cat", "realistic", "16:9")
        key2 = generate_cache_key("a dog", "realistic", "16:9")
        assert key1 != key2

    def test_whitespace_normalization(self):
        """공백 정규화 동작"""
        key1 = generate_cache_key("  a cat  ", "realistic", "16:9")
        key2 = generate_cache_key("a cat", "realistic", "16:9")
        assert key1 == key2

    def test_case_normalization(self):
        """대소문자 정규화 동작"""
        key1 = generate_cache_key("A CAT", "REALISTIC", "16:9")
        key2 = generate_cache_key("a cat", "realistic", "16:9")
        assert key1 == key2

    def test_hash_length(self):
        """SHA-256 해시는 64자"""
        key = generate_cache_key("test", "style", "16:9")
        assert len(key) == 64

    def test_different_aspect_ratio(self):
        """다른 비율은 다른 해시 생성"""
        key1 = generate_cache_key("a cat", "realistic", "16:9")
        key2 = generate_cache_key("a cat", "realistic", "1:1")
        assert key1 != key2


class TestCacheEntry:
    """CacheEntry 데이터클래스 테스트"""

    def test_not_expired(self):
        """만료되지 않은 항목"""
        entry = CacheEntry(
            key="test",
            result={"success": True},
            created_at=time.time(),
            expires_at=time.time() + 3600,
        )
        assert entry.is_expired() is False

    def test_expired(self):
        """만료된 항목"""
        entry = CacheEntry(
            key="test",
            result={"success": True},
            created_at=time.time() - 7200,
            expires_at=time.time() - 3600,
        )
        assert entry.is_expired() is True


class TestImageCacheBasic:
    """TC-002, TC-003: 캐시 기본 동작 테스트"""

    def test_cache_miss_returns_none(self):
        """캐시 MISS 시 None 반환"""
        cache = ImageCache()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_set_and_get(self):
        """캐시 저장 후 조회"""
        cache = ImageCache()
        test_result = {"success": True, "url": "http://example.com/image.png"}

        cache.set("test_key", test_result)
        cached = cache.get("test_key")

        assert cached == test_result

    def test_cache_hit_returns_same_object(self):
        """캐시 HIT 시 동일 객체 반환"""
        cache = ImageCache()
        test_result = {"success": True, "data": "test"}

        cache.set("key1", test_result)
        result1 = cache.get("key1")
        result2 = cache.get("key1")

        assert result1 == result2
        assert result1 is result2  # 동일 참조


class TestImageCacheTTL:
    """TC-004: TTL 만료 테스트"""

    def test_expired_entry_returns_none(self):
        """TTL 만료된 항목은 None 반환"""
        cache = ImageCache(ttl_seconds=1)
        cache.set("key", {"data": "test"})

        # 캐시 직후 조회 가능
        assert cache.get("key") is not None

        # TTL 만료 후 조회 불가
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_expired_entry_removed_from_cache(self):
        """만료된 항목은 캐시에서 제거"""
        cache = ImageCache(ttl_seconds=1)
        cache.set("key", {"data": "test"})

        assert cache.size == 1

        time.sleep(1.1)
        cache.get("key")  # 만료 검사 트리거

        assert cache.size == 0


class TestImageCacheLRU:
    """TC-005: LRU 정책 테스트"""

    def test_lru_eviction(self):
        """max_size 초과 시 가장 오래된 항목 제거"""
        cache = ImageCache(max_size=3)

        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        cache.set("key3", {"data": 3})

        # 용량 초과 - key1 제거 예상
        cache.set("key4", {"data": 4})

        assert cache.get("key1") is None  # 제거됨
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_lru_access_updates_order(self):
        """접근 시 LRU 순서 업데이트"""
        cache = ImageCache(max_size=3)

        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        cache.set("key3", {"data": 3})

        # key1 접근 - LRU 순서에서 가장 최근으로 이동
        cache.get("key1")

        # 새 항목 추가 - key2가 제거되어야 함 (key1이 아님)
        cache.set("key4", {"data": 4})

        assert cache.get("key1") is not None  # 유지됨
        assert cache.get("key2") is None  # 제거됨
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None


class TestImageCacheThreadSafety:
    """TC-006: 스레드 안전성 테스트"""

    def test_concurrent_writes(self):
        """동시 쓰기 테스트"""
        cache = ImageCache(max_size=1000)
        errors = []

        def write_items(start, count):
            try:
                for i in range(start, start + count):
                    cache.set(f"key_{i}", {"data": i})
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=write_items, args=(0, 100)),
            threading.Thread(target=write_items, args=(100, 100)),
            threading.Thread(target=write_items, args=(200, 100)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert cache.size <= 1000

    def test_concurrent_reads_writes(self):
        """동시 읽기/쓰기 테스트"""
        cache = ImageCache(max_size=100)
        errors = []

        # 초기 데이터 설정
        for i in range(50):
            cache.set(f"key_{i}", {"data": i})

        def reader():
            try:
                for i in range(100):
                    cache.get(f"key_{i % 50}")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50, 100):
                    cache.set(f"key_{i}", {"data": i})
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestImageCacheInvalidation:
    """TC-007: 캐시 무효화 테스트"""

    def test_invalidate_existing_key(self):
        """존재하는 키 무효화"""
        cache = ImageCache()
        cache.set("key1", {"data": "test"})

        result = cache.invalidate("key1")

        assert result is True
        assert cache.get("key1") is None

    def test_invalidate_nonexistent_key(self):
        """존재하지 않는 키 무효화"""
        cache = ImageCache()

        result = cache.invalidate("nonexistent")

        assert result is False

    def test_clear_all(self):
        """전체 캐시 초기화"""
        cache = ImageCache()
        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        cache.set("key3", {"data": 3})

        count = cache.clear()

        assert count == 3
        assert cache.size == 0
        assert cache.get("key1") is None


class TestImageCacheStats:
    """TC-008: 캐시 통계 테스트"""

    def test_hit_miss_counting(self):
        """Hit/Miss 카운팅"""
        cache = ImageCache()
        cache.set("key1", {"data": "test"})

        cache.get("key1")  # HIT
        cache.get("key1")  # HIT
        cache.get("key2")  # MISS

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3

    def test_hit_rate_calculation(self):
        """Hit Rate 계산"""
        cache = ImageCache()
        cache.set("key1", {"data": "test"})

        cache.get("key1")  # HIT
        cache.get("key2")  # MISS

        stats = cache.get_stats()

        assert stats["hit_rate_percent"] == 50.0

    def test_stats_after_clear(self):
        """Clear 후 통계 초기화"""
        cache = ImageCache()
        cache.set("key1", {"data": "test"})
        cache.get("key1")

        cache.clear()
        stats = cache.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total_requests"] == 0

    def test_stats_includes_config(self):
        """통계에 설정 정보 포함"""
        cache = ImageCache(max_size=50, ttl_seconds=1800)
        stats = cache.get_stats()

        assert stats["max_size"] == 50
        assert stats["ttl_seconds"] == 1800


class TestImageCacheEdgeCases:
    """엣지 케이스 테스트"""

    def test_update_existing_key(self):
        """기존 키 업데이트"""
        cache = ImageCache()
        cache.set("key1", {"version": 1})
        cache.set("key1", {"version": 2})

        result = cache.get("key1")
        assert result["version"] == 2

    def test_empty_cache_stats(self):
        """빈 캐시 통계"""
        cache = ImageCache()
        stats = cache.get_stats()

        assert stats["hit_rate_percent"] == 0.0
        assert stats["cache_size"] == 0

    def test_unicode_in_cache_key(self):
        """유니코드 캐시 키"""
        key1 = generate_cache_key("고양이 이미지", "사실적", "16:9")
        key2 = generate_cache_key("고양이 이미지", "사실적", "16:9")

        assert key1 == key2
        assert len(key1) == 64
