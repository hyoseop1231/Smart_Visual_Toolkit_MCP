---
id: SPEC-CACHE-001
type: plan
version: "1.0.0"
created: "2026-01-17"
updated: "2026-01-17"
---

# SPEC-CACHE-001: 구현 계획

## 1. 마일스톤 개요

### 우선순위 기반 마일스톤

| 마일스톤 | 목표 | 우선순위 | 의존성 |
|---------|------|---------|--------|
| M1: 캐시 키 생성기 | 프롬프트 기반 해시 키 생성 | Primary | 없음 |
| M2: 메모리 캐시 | LRU 기반 인메모리 캐싱 | Primary | M1 |
| M3: TTL 관리 | 시간 기반 자동 만료 | Primary | M2 |
| M4: 캐시 통합 | ImageGenerator에 캐시 적용 | Primary | M3 |
| M5: 통계 수집 | Hit/Miss 통계 및 MCP 도구 | Secondary | M4 |
| M6: 디스크 캐싱 | 선택적 영속화 기능 | Secondary | M4 |
| M7: 무효화 전략 | 수동 및 선택적 캐시 삭제 | Optional | M4 |

---

## 2. 상세 구현 계획

### M1: 캐시 키 생성기 (Primary)

**목표**: prompt + style + aspect_ratio 조합의 일관된 해시 키 생성

**구현 항목**:

1. `src/generators/cache.py` 모듈 생성
2. `generate_cache_key()` 함수 구현
   - 입력 정규화 (소문자, 공백 정리)
   - SHA-256 해시 생성
   - 64자 16진수 문자열 반환

**기술적 접근**:
```python
# src/generators/cache.py
import hashlib

def generate_cache_key(prompt: str, style: str, aspect_ratio: str = "16:9") -> str:
    """캐시 키 생성 - SHA-256 해시 사용"""
    normalized = f"{prompt.strip().lower()}|{style.strip().lower()}|{aspect_ratio.strip()}"
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
```

**검증 기준**:
- 동일 입력 시 동일 해시 생성
- 다른 입력 시 다른 해시 생성
- 공백/대소문자 정규화 동작

---

### M2: 메모리 캐시 (Primary)

**목표**: LRU 정책 기반 인메모리 캐싱 시스템

**구현 항목**:

1. `CacheEntry` 데이터클래스 정의
2. `ImageCache` 클래스 구현
   - `OrderedDict` 기반 LRU 구현
   - `threading.RLock` 스레드 안전성
   - `max_size` 용량 제한

**기술적 접근**:
```python
from dataclasses import dataclass
from collections import OrderedDict
import threading

@dataclass
class CacheEntry:
    key: str
    result: Dict[str, Any]
    created_at: float
    expires_at: float

class ImageCache:
    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)  # LRU 업데이트
                return self._cache[key].result
            return None

    def set(self, key: str, result: Dict[str, Any]) -> None:
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # 가장 오래된 항목 제거
            self._cache[key] = CacheEntry(...)
```

**검증 기준**:
- LRU 정책 정상 동작
- 최대 크기 제한 준수
- 스레드 안전성 보장

---

### M3: TTL 관리 (Primary)

**목표**: 시간 기반 캐시 만료 자동화

**구현 항목**:

1. `CacheEntry.expires_at` 필드 활용
2. `get()` 호출 시 만료 검사
3. 만료된 항목 자동 제거

**기술적 접근**:
```python
import time

def get(self, key: str) -> Optional[Dict[str, Any]]:
    with self._lock:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() > entry.expires_at:
                # TTL 만료 - 항목 제거
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return entry.result
        return None

def set(self, key: str, result: Dict[str, Any]) -> None:
    with self._lock:
        now = time.time()
        self._cache[key] = CacheEntry(
            key=key,
            result=result,
            created_at=now,
            expires_at=now + self._ttl_seconds
        )
```

**검증 기준**:
- TTL 경과 후 항목 자동 만료
- 만료 검사 정확성

---

### M4: 캐시 통합 (Primary)

**목표**: ImageGenerator에 캐시 레이어 통합

**구현 항목**:

1. `ImageGenerator.__init__()` 캐시 초기화
2. `generate()` 메서드 캐시 로직 추가
3. `_generate_uncached()` 분리
4. 환경 변수 기반 설정

**기술적 접근**:
```python
class ImageGenerator:
    def __init__(self, styles_data):
        # 기존 초기화 ...

        # 캐시 설정
        self._cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        if self._cache_enabled:
            self._cache = ImageCache(
                max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
                ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600"))
            )

    def generate(self, prompt, style_name=None, aspect_ratio="16:9"):
        if not self._cache_enabled:
            return self._generate_uncached(prompt, style_name, aspect_ratio)

        cache_key = generate_cache_key(prompt, style_name or self.default_style, aspect_ratio)

        cached = self._cache.get(cache_key)
        if cached:
            return cached

        result = self._generate_uncached(prompt, style_name, aspect_ratio)
        if result.get("success"):
            self._cache.set(cache_key, result)
        return result
```

**검증 기준**:
- 기존 인터페이스 호환성
- 캐시 활성화/비활성화 정상 동작
- 환경 변수 설정 반영

---

### M5: 통계 수집 (Secondary)

**목표**: 캐시 성능 모니터링 및 MCP 도구 제공

**구현 항목**:

1. Hit/Miss 카운터 구현
2. `get_stats()` 메서드 추가
3. `get_cache_stats()` MCP 도구 (선택적)

**기술적 접근**:
```python
class ImageCache:
    def __init__(self, ...):
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        # ... 기존 로직 ...
        if found:
            self._hits += 1
            return entry.result
        else:
            self._misses += 1
            return None

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_size": len(self._cache),
                "max_size": self._max_size
            }
```

**검증 기준**:
- 정확한 통계 수집
- Hit Rate 계산 정확성

---

### M6: 디스크 캐싱 (Secondary)

**목표**: 선택적 영속화로 서버 재시작 시 캐시 유지

**구현 항목**:

1. `CACHE_DISK_ENABLED` 환경 변수 지원
2. 캐시 저장 시 디스크 동기화
3. 서버 시작 시 디스크 캐시 로드

**기술적 접근**:
```python
import json
from pathlib import Path

class ImageCache:
    def set(self, key: str, result: Dict[str, Any]) -> None:
        # ... 메모리 캐시 저장 ...

        if self._disk_enabled:
            self._save_to_disk(key, entry)

    def _save_to_disk(self, key: str, entry: CacheEntry) -> None:
        cache_file = self._disk_path / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                "key": entry.key,
                "result": entry.result,
                "created_at": entry.created_at,
                "expires_at": entry.expires_at
            }, f)

    def _load_from_disk(self) -> None:
        if not self._disk_enabled:
            return
        for cache_file in self._disk_path.glob("*.json"):
            # 로드 및 TTL 검증
```

**검증 기준**:
- 디스크 저장/로드 정상 동작
- TTL 만료된 디스크 캐시 무시

---

### M7: 무효화 전략 (Optional)

**목표**: 수동 및 선택적 캐시 관리

**구현 항목**:

1. `invalidate(key)` 특정 키 무효화
2. `clear()` 전체 캐시 초기화
3. `clear_cache()` MCP 도구 (선택적)

**기술적 접근**:
```python
def invalidate(self, key: str) -> bool:
    with self._lock:
        if key in self._cache:
            del self._cache[key]
            if self._disk_enabled:
                cache_file = self._disk_path / f"{key}.json"
                cache_file.unlink(missing_ok=True)
            return True
        return False

def clear(self) -> int:
    with self._lock:
        count = len(self._cache)
        self._cache.clear()
        if self._disk_enabled:
            for f in self._disk_path.glob("*.json"):
                f.unlink()
        self._hits = 0
        self._misses = 0
        return count
```

---

## 3. 위험 관리

### 식별된 위험

| 위험 | 영향도 | 발생 확률 | 대응 전략 |
|------|--------|----------|----------|
| 메모리 부족 | HIGH | LOW | max_size 제한, LRU 정책 |
| 캐시 일관성 문제 | MEDIUM | LOW | 해시 키 정규화 |
| 스레드 데드락 | HIGH | LOW | RLock 사용, 코드 리뷰 |
| 디스크 공간 부족 | MEDIUM | MEDIUM | 용량 모니터링, 정리 정책 |
| 손상된 캐시 파일 | LOW | LOW | 유효성 검사, 재생성 |

---

## 4. 기술적 결정 사항

### TD-001: 표준 라이브러리만 사용

**결정**: Redis, diskcache 등 외부 라이브러리 대신 Python 표준 라이브러리만 사용

**근거**:
- 추가 의존성 최소화
- 배포 복잡성 감소
- 현재 규모에 적합한 성능

**대안 고려**:
- `functools.lru_cache`: 함수 레벨 캐싱만 지원 (불충분)
- `diskcache`: 외부 의존성 추가 (불필요)
- `redis`: 별도 서버 필요 (과도함)

### TD-002: SHA-256 해시 알고리즘

**결정**: 캐시 키 생성에 SHA-256 사용

**근거**:
- 충돌 확률 극히 낮음
- Python 표준 라이브러리 지원
- 64자 고정 길이 키

### TD-003: OrderedDict 기반 LRU

**결정**: `collections.OrderedDict`로 LRU 직접 구현

**근거**:
- TTL과 LRU 동시 지원 필요
- 커스텀 만료 로직 통합 용이
- 통계 수집 통합 가능

---

## 5. 파일 변경 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `src/generators/cache.py` | 신규 | 캐시 모듈 전체 구현 |
| `src/generators/image_gen.py` | 수정 | 캐시 통합 |
| `src/main.py` | 수정 | 캐시 통계 MCP 도구 추가 (선택적) |
| `.env.example` | 수정 | 캐시 환경 변수 추가 |
| `tests/test_cache.py` | 신규 | 캐시 단위 테스트 |
| `tests/test_image_gen_cache.py` | 신규 | 통합 테스트 |

---

## 6. 다음 단계

1. **M1-M4 구현** → Primary 목표 완료
2. **테스트 작성** → acceptance.md 시나리오 기반
3. **M5-M6 구현** → Secondary 목표 (선택적)
4. **문서화** → README 업데이트, 환경 변수 가이드

---

## 7. Traceability Tags

- **SPEC**: SPEC-CACHE-001
- **Requirements**: REQ-U-001 ~ REQ-U-004, REQ-E-001 ~ REQ-E-006, REQ-S-001 ~ REQ-S-004, REQ-N-001 ~ REQ-N-004
- **Related SPEC**: SPEC-IMG-001 (배치 이미지 생성)
