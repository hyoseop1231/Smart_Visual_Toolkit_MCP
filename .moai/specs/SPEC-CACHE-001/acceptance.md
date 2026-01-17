---
id: SPEC-CACHE-001
type: acceptance
version: "1.0.0"
created: "2026-01-17"
updated: "2026-01-17"
---

# SPEC-CACHE-001: 수락 기준

## 1. 테스트 시나리오 개요

| ID | 시나리오 | 우선순위 | 요구사항 |
|----|---------|---------|---------|
| TC-001 | 캐시 키 생성 일관성 | HIGH | REQ-U-001 |
| TC-002 | 캐시 HIT 시나리오 | HIGH | REQ-E-001, REQ-E-002 |
| TC-003 | 캐시 MISS 및 저장 | HIGH | REQ-E-003 |
| TC-004 | TTL 만료 처리 | HIGH | REQ-E-004 |
| TC-005 | LRU 정책 동작 | HIGH | REQ-E-005 |
| TC-006 | 캐시 통계 수집 | MEDIUM | REQ-U-002, REQ-O-001 |
| TC-007 | 스레드 안전성 | HIGH | REQ-U-003 |
| TC-008 | 캐시 전체 초기화 | MEDIUM | REQ-E-006 |
| TC-009 | 캐시 비활성화 모드 | HIGH | REQ-S-001 |
| TC-010 | 디스크 캐싱 | MEDIUM | REQ-S-002 |
| TC-011 | 손상된 캐시 복구 | MEDIUM | REQ-S-003 |
| TC-012 | 캐시 오류 내성 | HIGH | REQ-N-001 |

---

## 2. 상세 테스트 시나리오

### TC-001: 캐시 키 생성 일관성

**목적**: 동일 입력에 대해 항상 동일한 캐시 키가 생성되는지 검증

**Given-When-Then**:

```gherkin
Feature: 캐시 키 생성
  As a 시스템
  I want to 일관된 캐시 키를 생성
  So that 동일 요청을 정확히 식별할 수 있다

  Scenario: 동일 입력 시 동일 키 생성
    Given 프롬프트가 "A beautiful sunset"
    And 스타일이 "Cyberpunk"
    And 화면비가 "16:9"
    When generate_cache_key()를 두 번 호출하면
    Then 두 결과가 동일해야 한다

  Scenario: 공백 및 대소문자 정규화
    Given 프롬프트가 "A Beautiful Sunset " (후행 공백, 대문자 포함)
    And 스타일이 " CYBERPUNK" (선행 공백, 대문자)
    When generate_cache_key()를 호출하면
    Then "a beautiful sunset|cyberpunk|16:9"의 해시와 동일해야 한다

  Scenario: 다른 입력 시 다른 키 생성
    Given 프롬프트 A가 "A beautiful sunset"
    And 프롬프트 B가 "A beautiful sunrise"
    When 각각 generate_cache_key()를 호출하면
    Then 두 결과가 달라야 한다
```

**테스트 코드**:

```python
# tests/test_cache.py
import pytest
from src.generators.cache import generate_cache_key

class TestCacheKeyGeneration:
    def test_same_input_same_key(self):
        key1 = generate_cache_key("A beautiful sunset", "Cyberpunk", "16:9")
        key2 = generate_cache_key("A beautiful sunset", "Cyberpunk", "16:9")
        assert key1 == key2

    def test_normalization(self):
        key1 = generate_cache_key("A Beautiful Sunset ", " CYBERPUNK", "16:9")
        key2 = generate_cache_key("a beautiful sunset", "cyberpunk", "16:9")
        assert key1 == key2

    def test_different_input_different_key(self):
        key1 = generate_cache_key("A beautiful sunset", "Cyberpunk", "16:9")
        key2 = generate_cache_key("A beautiful sunrise", "Cyberpunk", "16:9")
        assert key1 != key2

    def test_key_format(self):
        key = generate_cache_key("test", "style", "16:9")
        assert len(key) == 64  # SHA-256 hex digest
        assert key.isalnum()
```

---

### TC-002: 캐시 HIT 시나리오

**목적**: 캐시에 저장된 결과가 정상적으로 반환되는지 검증

**Given-When-Then**:

```gherkin
Feature: 캐시 조회 (HIT)
  As a 시스템
  I want to 캐시된 결과를 반환
  So that API 호출을 절약할 수 있다

  Scenario: 캐시된 이미지 반환
    Given 캐시에 "sunset_key"에 대한 결과가 저장되어 있음
    And 결과에 success=True, local_path="/path/to/image.png" 포함
    When cache.get("sunset_key")를 호출하면
    Then 저장된 결과가 반환되어야 한다
    And API 호출이 발생하지 않아야 한다

  Scenario: 캐시 조회 시 LRU 순서 업데이트
    Given 캐시에 key_a, key_b, key_c가 순서대로 저장됨
    When cache.get("key_a")를 호출하면
    Then key_a가 가장 최근 사용 항목으로 이동해야 한다
```

**테스트 코드**:

```python
class TestCacheHit:
    def test_cache_hit_returns_stored_result(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)

        result = {"success": True, "local_path": "/path/to/image.png"}
        cache.set("test_key", result)

        cached = cache.get("test_key")
        assert cached == result

    def test_cache_hit_updates_lru_order(self):
        cache = ImageCache(max_size=3, ttl_seconds=3600)

        cache.set("key_a", {"id": "a"})
        cache.set("key_b", {"id": "b"})
        cache.set("key_c", {"id": "c"})

        # key_a 조회 → 가장 최근으로 이동
        cache.get("key_a")

        # 새 항목 추가 시 key_b가 제거되어야 함 (key_a는 보존)
        cache.set("key_d", {"id": "d"})

        assert cache.get("key_a") is not None
        assert cache.get("key_b") is None  # LRU로 제거됨
```

---

### TC-003: 캐시 MISS 및 저장

**목적**: 캐시 미스 시 API 호출 후 결과가 저장되는지 검증

**Given-When-Then**:

```gherkin
Feature: 캐시 저장 (MISS)
  As a 시스템
  I want to API 결과를 캐시에 저장
  So that 다음 요청에서 재사용할 수 있다

  Scenario: 캐시 미스 후 저장
    Given 캐시에 "new_key"에 대한 결과가 없음
    When cache.get("new_key")를 호출하면
    Then None이 반환되어야 한다
    When API 호출 후 결과를 cache.set("new_key", result)로 저장하면
    Then 다음 cache.get("new_key")에서 결과가 반환되어야 한다
```

**테스트 코드**:

```python
class TestCacheMiss:
    def test_cache_miss_returns_none(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)

        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_set_then_get(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)

        # MISS
        assert cache.get("test_key") is None

        # API 호출 시뮬레이션 및 저장
        api_result = {"success": True, "local_path": "/path/image.png"}
        cache.set("test_key", api_result)

        # HIT
        cached = cache.get("test_key")
        assert cached == api_result
```

---

### TC-004: TTL 만료 처리

**목적**: TTL이 만료된 캐시 항목이 자동으로 제거되는지 검증

**Given-When-Then**:

```gherkin
Feature: TTL 만료
  As a 시스템
  I want to 만료된 캐시 항목을 제거
  So that 오래된 데이터가 반환되지 않는다

  Scenario: TTL 만료 후 캐시 미스
    Given 캐시에 TTL 1초로 "temp_key" 결과가 저장됨
    When 2초 후 cache.get("temp_key")를 호출하면
    Then None이 반환되어야 한다 (만료됨)
```

**테스트 코드**:

```python
import time

class TestCacheTTL:
    def test_ttl_expiration(self):
        cache = ImageCache(max_size=10, ttl_seconds=1)  # 1초 TTL

        cache.set("temp_key", {"data": "value"})

        # 즉시 조회 - HIT
        assert cache.get("temp_key") is not None

        # 2초 대기 후 조회 - MISS (만료)
        time.sleep(2)
        assert cache.get("temp_key") is None

    def test_ttl_not_expired(self):
        cache = ImageCache(max_size=10, ttl_seconds=60)

        cache.set("temp_key", {"data": "value"})
        time.sleep(0.1)  # 짧은 대기

        # 아직 만료되지 않음
        assert cache.get("temp_key") is not None
```

---

### TC-005: LRU 정책 동작

**목적**: 캐시 최대 크기 도달 시 LRU 정책이 적용되는지 검증

**Given-When-Then**:

```gherkin
Feature: LRU 정책
  As a 시스템
  I want to 가장 오래된 항목을 제거
  So that 메모리 사용량을 제한할 수 있다

  Scenario: 최대 크기 초과 시 LRU 제거
    Given 캐시 최대 크기가 3
    And key_a, key_b, key_c가 순서대로 저장됨
    When key_d를 저장하면
    Then key_a가 제거되어야 한다 (LRU)
    And key_b, key_c, key_d는 남아있어야 한다
```

**테스트 코드**:

```python
class TestCacheLRU:
    def test_lru_eviction(self):
        cache = ImageCache(max_size=3, ttl_seconds=3600)

        cache.set("key_a", {"id": "a"})
        cache.set("key_b", {"id": "b"})
        cache.set("key_c", {"id": "c"})

        # 4번째 항목 추가 → key_a 제거 예상
        cache.set("key_d", {"id": "d"})

        assert cache.get("key_a") is None  # 제거됨
        assert cache.get("key_b") is not None
        assert cache.get("key_c") is not None
        assert cache.get("key_d") is not None

    def test_lru_access_updates_order(self):
        cache = ImageCache(max_size=3, ttl_seconds=3600)

        cache.set("key_a", {"id": "a"})
        cache.set("key_b", {"id": "b"})
        cache.set("key_c", {"id": "c"})

        # key_a 조회 → 가장 최근으로 이동
        cache.get("key_a")

        # key_d 추가 → key_b가 LRU로 제거됨
        cache.set("key_d", {"id": "d"})

        assert cache.get("key_a") is not None  # 조회로 인해 보존
        assert cache.get("key_b") is None  # LRU로 제거
```

---

### TC-006: 캐시 통계 수집

**목적**: Hit/Miss 통계가 정확하게 수집되는지 검증

**Given-When-Then**:

```gherkin
Feature: 캐시 통계
  As a 사용자
  I want to 캐시 성능 통계를 확인
  So that 캐시 효율성을 모니터링할 수 있다

  Scenario: Hit/Miss 카운트
    Given 빈 캐시
    When 캐시 미스 2회, 캐시 히트 3회 발생하면
    Then stats.hits == 3, stats.misses == 2
    And stats.hit_rate_percent == 60.0
```

**테스트 코드**:

```python
class TestCacheStats:
    def test_hit_miss_counting(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)

        # MISS 2회
        cache.get("key1")  # MISS
        cache.get("key2")  # MISS

        # 저장
        cache.set("key1", {"data": "1"})
        cache.set("key2", {"data": "2"})

        # HIT 3회
        cache.get("key1")  # HIT
        cache.get("key2")  # HIT
        cache.get("key1")  # HIT

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate_percent"] == 60.0

    def test_stats_format(self):
        cache = ImageCache(max_size=100, ttl_seconds=3600)
        cache.set("key", {"data": "value"})
        cache.get("key")

        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "total_requests" in stats
        assert "hit_rate_percent" in stats
        assert "cache_size" in stats
        assert "max_size" in stats
```

---

### TC-007: 스레드 안전성

**목적**: 동시 접근 시 데이터 무결성이 보장되는지 검증

**Given-When-Then**:

```gherkin
Feature: 스레드 안전성
  As a 시스템
  I want to 동시 접근을 안전하게 처리
  So that 데이터 손상이 발생하지 않는다

  Scenario: 동시 쓰기
    Given 10개의 스레드가 동시에 캐시에 쓰기 시도
    When 모든 쓰기 완료 후
    Then 캐시 상태가 일관성을 유지해야 한다
    And 데드락이 발생하지 않아야 한다
```

**테스트 코드**:

```python
import threading
import concurrent.futures

class TestCacheThreadSafety:
    def test_concurrent_writes(self):
        cache = ImageCache(max_size=100, ttl_seconds=3600)

        def write_cache(i):
            cache.set(f"key_{i}", {"index": i})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_cache, i) for i in range(100)]
            concurrent.futures.wait(futures)

        # 모든 쓰기 완료 후 일관성 확인
        stats = cache.get_stats()
        assert stats["cache_size"] == 100

    def test_concurrent_read_write(self):
        cache = ImageCache(max_size=100, ttl_seconds=3600)

        # 초기 데이터
        for i in range(50):
            cache.set(f"key_{i}", {"index": i})

        errors = []

        def read_write(i):
            try:
                cache.get(f"key_{i % 50}")
                cache.set(f"new_key_{i}", {"index": i})
            except Exception as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(read_write, i) for i in range(200)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
```

---

### TC-008: 캐시 전체 초기화

**목적**: 캐시 초기화 기능이 정상 동작하는지 검증

**테스트 코드**:

```python
class TestCacheClear:
    def test_clear_removes_all_entries(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)

        for i in range(5):
            cache.set(f"key_{i}", {"data": i})

        assert cache.get_stats()["cache_size"] == 5

        cleared_count = cache.clear()

        assert cleared_count == 5
        assert cache.get_stats()["cache_size"] == 0

    def test_clear_resets_stats(self):
        cache = ImageCache(max_size=10, ttl_seconds=3600)
        cache.set("key", {"data": "value"})
        cache.get("key")  # HIT
        cache.get("missing")  # MISS

        cache.clear()

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
```

---

### TC-009: 캐시 비활성화 모드

**목적**: CACHE_ENABLED=false 시 캐싱이 우회되는지 검증

**테스트 코드**:

```python
import os
from unittest.mock import patch

class TestCacheDisabled:
    def test_disabled_cache_calls_api_directly(self):
        with patch.dict(os.environ, {"CACHE_ENABLED": "false"}):
            generator = ImageGenerator(styles_data)

            # 캐시 비활성화 상태에서 동일 요청 2회
            result1 = generator.generate("test prompt", "Cyberpunk")
            result2 = generator.generate("test prompt", "Cyberpunk")

            # 캐시가 없으므로 매번 API 호출 (모킹으로 확인)
            # 실제 테스트에서는 API 호출 횟수 검증
```

---

### TC-010: 디스크 캐싱

**목적**: 디스크 영속화가 정상 동작하는지 검증

**테스트 코드**:

```python
import tempfile
from pathlib import Path

class TestDiskCache:
    def test_disk_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ImageCache(
                max_size=10,
                ttl_seconds=3600,
                disk_enabled=True,
                disk_path=tmpdir
            )

            cache.set("persistent_key", {"data": "value"})

            # 디스크에 파일 생성 확인
            cache_file = Path(tmpdir) / "persistent_key.json"
            # 실제 구현에 따라 파일명 형식 조정

    def test_disk_cache_load_on_startup(self):
        # 서버 재시작 시 디스크 캐시 로드 검증
        pass
```

---

### TC-011: 손상된 캐시 복구

**목적**: 손상된 캐시 데이터 처리 검증

**테스트 코드**:

```python
class TestCacheRecovery:
    def test_corrupted_disk_cache_ignored(self):
        # 손상된 JSON 파일이 있을 때 오류 없이 무시되는지 검증
        pass

    def test_missing_image_file_invalidates_cache(self):
        # 캐시된 이미지 파일이 삭제된 경우 재생성 트리거
        pass
```

---

### TC-012: 캐시 오류 내성

**목적**: 캐시 오류가 전체 동작에 영향을 주지 않는지 검증

**테스트 코드**:

```python
class TestCacheErrorTolerance:
    def test_cache_error_fallback_to_api(self):
        # 캐시 저장 실패 시에도 API 결과 정상 반환
        pass

    def test_cache_read_error_fallback(self):
        # 캐시 읽기 실패 시 API 호출로 폴백
        pass
```

---

## 3. 품질 게이트

### 필수 조건

| 조건 | 기준 | 상태 |
|------|------|------|
| 단위 테스트 통과 | TC-001 ~ TC-012 모두 통과 | Pending |
| 테스트 커버리지 | 85% 이상 | Pending |
| 린터 경고 없음 | ruff 검사 통과 | Pending |
| 기존 테스트 통과 | 회귀 테스트 | Pending |

### Definition of Done

- [ ] 모든 Primary 마일스톤 (M1-M4) 구현 완료
- [ ] TC-001 ~ TC-009 테스트 통과
- [ ] 85% 이상 테스트 커버리지
- [ ] 기존 `generate_image()`, `generate_images_batch()` 인터페이스 호환성 유지
- [ ] 환경 변수 문서화 (.env.example 업데이트)
- [ ] 코드 리뷰 완료

---

## 4. Traceability Tags

- **SPEC**: SPEC-CACHE-001
- **Plan**: plan.md
- **Requirements**: REQ-U-001 ~ REQ-U-004, REQ-E-001 ~ REQ-E-006, REQ-S-001 ~ REQ-S-004, REQ-N-001 ~ REQ-N-004, REQ-O-001 ~ REQ-O-003
