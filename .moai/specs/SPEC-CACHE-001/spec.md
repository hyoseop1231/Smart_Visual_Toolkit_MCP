---
id: SPEC-CACHE-001
version: "1.0.0"
status: "draft"
created: "2026-01-17"
updated: "2026-01-17"
author: "Hyoseop"
priority: "HIGH"
lifecycle: "spec-anchored"
---

# SPEC-CACHE-001: 이미지 생성 캐싱 레이어

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-17 | Hyoseop | 초기 SPEC 작성 |

---

## 1. Environment (환경)

### 1.1 현재 시스템 컨텍스트

```
현재 구현 상태:
├── src/main.py                    # MCP 서버 (8개 도구)
│   ├── generate_image()           # 단일 이미지 생성
│   └── generate_images_batch()    # 배치 이미지 생성 (SPEC-IMG-001)
├── src/generators/image_gen.py    # ImageGenerator 클래스
│   ├── generate()                 # 동기 단일 생성
│   ├── _generate_single_async()   # 비동기 단일 생성
│   └── generate_batch()           # 배치 생성
└── src/resources/banana_styles.json # 15가지 스타일 정의

기술 스택:
├── Python 3.10+
├── FastMCP 0.1.0+
├── google-genai SDK (Imagen 4.0)
├── httpx (비동기 HTTP)
└── asyncio (동시성 처리)
```

### 1.2 현재 제한사항

| 제한사항 | 설명 | 영향 |
|---------|------|------|
| 캐싱 없음 | 동일 프롬프트 요청 시 매번 API 호출 | API 비용 증가, 응답 지연 |
| 중복 요청 | 동일한 이미지를 반복 생성 | 불필요한 리소스 소모 |
| 히스토리 없음 | 이전 생성 결과 조회 불가 | 사용자 경험 저하 |

### 1.3 외부 의존성

| 의존성 | 버전 | 제약사항 |
|--------|------|---------|
| Google Gemini API | Imagen 4.0 | 요청당 비용 발생 |
| Python functools | 표준 라이브러리 | lru_cache 사용 가능 |
| hashlib | 표준 라이브러리 | SHA-256 해시 생성 |

---

## 2. Assumptions (가정)

### 2.1 기술적 가정

| ID | 가정 | 신뢰도 | 검증 방법 |
|----|------|--------|----------|
| A-001 | 동일한 prompt + style + aspect_ratio 조합은 동일한 이미지를 생성함 | HIGH | API 특성 분석 |
| A-002 | Python hashlib로 충돌 없는 캐시 키 생성 가능 | HIGH | SHA-256 사용 |
| A-003 | 메모리 기반 LRU 캐시로 충분한 성능 확보 가능 | HIGH | functools.lru_cache 검증 |
| A-004 | 디스크 캐싱 시 파일 I/O 오버헤드가 API 호출보다 적음 | HIGH | 로컬 파일 시스템 |
| A-005 | 환경 변수를 통한 캐시 설정 관리가 적합함 | MEDIUM | 현재 설정 패턴 준수 |

### 2.2 비즈니스 가정

| ID | 가정 | 신뢰도 | 위험 시 대응 |
|----|------|--------|-------------|
| B-001 | 사용자가 동일 프롬프트를 반복 요청하는 경우가 많음 | MEDIUM | 캐시 적중률 모니터링 |
| B-002 | 캐시된 이미지는 일정 기간 유효함 | HIGH | TTL 기반 만료 구현 |
| B-003 | 디스크 공간보다 API 비용 절감이 더 중요함 | HIGH | 용량 제한 설정 |

### 2.3 5 Whys 분석 (근본 원인 분석)

**표면적 문제**: 동일한 이미지 요청 시 불필요한 API 호출 발생

1. **Why?** 이전에 생성한 이미지 결과를 저장하지 않음
2. **Why?** 캐싱 레이어가 구현되어 있지 않음
3. **Why?** 초기 MVP 개발 시 우선순위가 낮았음
4. **Why?** 기능 구현에 집중하여 최적화는 후순위로 설정됨
5. **근본 원인**: 반복 요청 최적화를 위한 캐싱 아키텍처 미설계

**해결 방향**: 프롬프트 기반 캐시 키 + 다계층 캐싱 (메모리 + 디스크)

---

## 3. Requirements (요구사항) - EARS 형식

### 3.1 Ubiquitous Requirements (항상 적용)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-U-001** | 시스템은 **항상** 캐시 키를 prompt + style + aspect_ratio 조합의 해시값으로 생성해야 한다 | 캐시 일관성 보장 |
| **REQ-U-002** | 시스템은 **항상** 캐시 적중/미스 통계를 기록해야 한다 | 성능 모니터링 |
| **REQ-U-003** | 시스템은 **항상** 캐시 작업 시 스레드 안전성을 보장해야 한다 | 동시성 문제 방지 |
| **REQ-U-004** | 시스템은 **항상** 원본 API 응답과 동일한 형식의 캐시 데이터를 반환해야 한다 | 기존 인터페이스 호환성 |

### 3.2 Event-Driven Requirements (이벤트 기반)

| ID | WHEN (이벤트) | THEN (동작) |
|----|--------------|-------------|
| **REQ-E-001** | **WHEN** 이미지 생성 요청이 들어오면 | **THEN** 시스템은 먼저 캐시에서 결과를 조회해야 한다 |
| **REQ-E-002** | **WHEN** 캐시에 결과가 존재하면 (HIT) | **THEN** 시스템은 API 호출 없이 캐시된 결과를 반환해야 한다 |
| **REQ-E-003** | **WHEN** 캐시에 결과가 없으면 (MISS) | **THEN** 시스템은 API를 호출하고 결과를 캐시에 저장해야 한다 |
| **REQ-E-004** | **WHEN** 캐시 항목의 TTL이 만료되면 | **THEN** 시스템은 해당 항목을 자동으로 제거해야 한다 |
| **REQ-E-005** | **WHEN** 캐시 용량이 최대 크기에 도달하면 | **THEN** 시스템은 LRU 정책에 따라 가장 오래된 항목을 제거해야 한다 |
| **REQ-E-006** | **WHEN** 수동 캐시 초기화 요청이 들어오면 | **THEN** 시스템은 모든 캐시 항목을 안전하게 삭제해야 한다 |

### 3.3 State-Driven Requirements (상태 기반)

| ID | IF (조건) | THEN (동작) |
|----|----------|-------------|
| **REQ-S-001** | **IF** 캐싱 기능이 비활성화되어 있으면 (CACHE_ENABLED=false) | **THEN** 시스템은 기존 방식대로 직접 API를 호출해야 한다 |
| **REQ-S-002** | **IF** 디스크 캐싱이 활성화되어 있으면 (CACHE_DISK_ENABLED=true) | **THEN** 시스템은 이미지 파일을 디스크에 영구 저장해야 한다 |
| **REQ-S-003** | **IF** 캐시된 이미지 파일이 손상되었거나 존재하지 않으면 | **THEN** 시스템은 해당 캐시 항목을 무효화하고 재생성해야 한다 |
| **REQ-S-004** | **IF** 메모리 캐시 크기가 0으로 설정되었으면 | **THEN** 시스템은 디스크 캐싱만 사용해야 한다 |

### 3.4 Unwanted Behavior Requirements (금지 사항)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-N-001** | 시스템은 **절대** 캐시 실패로 인해 이미지 생성 전체를 중단**하지 않아야 한다** | 가용성 보장 |
| **REQ-N-002** | 시스템은 **절대** 기존 `generate_image()` 또는 `generate_images_batch()` 인터페이스를 변경**하지 않아야 한다** | 하위 호환성 |
| **REQ-N-003** | 시스템은 **절대** 환경 변수 없이도 기본값으로 동작을 중단**하지 않아야 한다** | 기본 동작 보장 |
| **REQ-N-004** | 시스템은 **절대** 손상된 캐시 데이터를 반환**하지 않아야 한다** | 데이터 무결성 |

### 3.5 Optional Requirements (선택적 기능)

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| **REQ-O-001** | **가능하면** 캐시 통계 조회 MCP 도구(`get_cache_stats()`)를 제공한다 | MEDIUM |
| **REQ-O-002** | **가능하면** 특정 프롬프트의 캐시만 무효화하는 기능을 제공한다 | LOW |
| **REQ-O-003** | **가능하면** 캐시 워밍업(pre-population) 기능을 제공한다 | LOW |

---

## 4. Specifications (세부 명세)

### 4.1 캐시 키 생성 알고리즘

```python
import hashlib
from typing import Optional

def generate_cache_key(
    prompt: str,
    style: str,
    aspect_ratio: str = "16:9"
) -> str:
    """
    prompt + style + aspect_ratio 조합의 SHA-256 해시 생성

    Args:
        prompt: 이미지 생성 프롬프트
        style: 스타일 이름 (또는 기본값)
        aspect_ratio: 화면비 (기본값: 16:9)

    Returns:
        64자 16진수 해시 문자열
    """
    # 정규화: 소문자 변환, 공백 정리
    normalized_prompt = prompt.strip().lower()
    normalized_style = style.strip().lower()
    normalized_ratio = aspect_ratio.strip()

    # 구분자로 연결
    key_source = f"{normalized_prompt}|{normalized_style}|{normalized_ratio}"

    # SHA-256 해시 생성
    return hashlib.sha256(key_source.encode('utf-8')).hexdigest()
```

### 4.2 캐시 클래스 설계

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from collections import OrderedDict
import threading
import time
from pathlib import Path

@dataclass
class CacheEntry:
    """캐시 항목 데이터 구조"""
    key: str
    result: Dict[str, Any]  # 이미지 생성 결과
    created_at: float       # 생성 시간 (Unix timestamp)
    expires_at: float       # 만료 시간 (Unix timestamp)
    local_path: Optional[str] = None  # 디스크 캐시 경로

class ImageCache:
    """
    이미지 생성 결과 캐싱 시스템

    Features:
    - LRU 기반 메모리 캐시
    - TTL 기반 자동 만료
    - 선택적 디스크 영속화
    - 스레드 안전 동작
    - 통계 수집
    """

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
        disk_enabled: bool = False,
        disk_path: Optional[str] = None
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._disk_enabled = disk_enabled
        self._disk_path = Path(disk_path) if disk_path else Path("output/cache")

        # 통계
        self._hits = 0
        self._misses = 0

        if self._disk_enabled:
            self._disk_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시 조회 (HIT/MISS 통계 포함)"""
        ...

    def set(self, key: str, result: Dict[str, Any]) -> None:
        """캐시 저장 (LRU 정책 적용)"""
        ...

    def invalidate(self, key: str) -> bool:
        """특정 키 무효화"""
        ...

    def clear(self) -> int:
        """전체 캐시 초기화"""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        ...
```

### 4.3 환경 변수 설정

| 환경 변수 | 기본값 | 설명 |
|----------|--------|------|
| `CACHE_ENABLED` | `true` | 캐싱 기능 활성화 여부 |
| `CACHE_MAX_SIZE` | `100` | 메모리 캐시 최대 항목 수 |
| `CACHE_TTL_SECONDS` | `3600` | 캐시 항목 TTL (초) |
| `CACHE_DISK_ENABLED` | `false` | 디스크 영속화 활성화 여부 |
| `CACHE_DISK_PATH` | `output/cache` | 디스크 캐시 저장 경로 |

### 4.4 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Client (Claude Code 등)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │ generate_image() / generate_images_batch()
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       main.py (MCP Server)                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              generate_image() / generate_images_batch()          │ │
│  │                              │                                   │ │
│  │                              ▼                                   │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │                    ImageGenerator                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │                  Cache Layer                             │ │ │ │
│  │  │  │                                                          │ │ │ │
│  │  │  │   1. generate_cache_key(prompt, style, aspect_ratio)     │ │ │ │
│  │  │  │                         │                                 │ │ │ │
│  │  │  │                         ▼                                 │ │ │ │
│  │  │  │   2. cache.get(key)                                      │ │ │ │
│  │  │  │          │                                                │ │ │ │
│  │  │  │          ├─── HIT ──► Return cached result               │ │ │ │
│  │  │  │          │                                                │ │ │ │
│  │  │  │          └─── MISS ─┐                                     │ │ │ │
│  │  │  │                     ▼                                     │ │ │ │
│  │  │  │   3. Call Imagen API                                     │ │ │ │
│  │  │  │                     │                                     │ │ │ │
│  │  │  │                     ▼                                     │ │ │ │
│  │  │  │   4. cache.set(key, result)                              │ │ │ │
│  │  │  │                     │                                     │ │ │ │
│  │  │  │                     ▼                                     │ │ │ │
│  │  │  │   5. Return result                                       │ │ │ │
│  │  │  └──────────────────────────────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   Memory Cache (LRU)    │          │    Disk Cache           │
│                         │          │    (Optional)           │
│  ┌───────────────────┐  │          │  ┌───────────────────┐  │
│  │ OrderedDict       │  │          │  │ output/cache/     │  │
│  │ key → CacheEntry  │  │  ───►    │  │ {hash}.json       │  │
│  │ max_size: 100     │  │  sync    │  │ {hash}.png        │  │
│  │ ttl: 3600s        │  │          │  └───────────────────┘  │
│  └───────────────────┘  │          │                         │
└─────────────────────────┘          └─────────────────────────┘
```

### 4.5 캐시 통합 위치

```python
# src/generators/image_gen.py 수정

class ImageGenerator:
    def __init__(self, styles_data: Dict[str, Any]):
        # ... 기존 초기화 코드 ...

        # 캐시 초기화
        self._cache = ImageCache(
            max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
            disk_enabled=os.getenv("CACHE_DISK_ENABLED", "false").lower() == "true",
            disk_path=os.getenv("CACHE_DISK_PATH", "output/cache")
        )
        self._cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    def generate(self, prompt: str, style_name: Optional[str] = None,
                 aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """캐싱이 적용된 이미지 생성"""

        # 캐싱 비활성화 시 기존 로직 사용
        if not self._cache_enabled:
            return self._generate_uncached(prompt, style_name, aspect_ratio)

        # 1. 캐시 키 생성
        style = style_name or self.default_style
        cache_key = generate_cache_key(prompt, style, aspect_ratio)

        # 2. 캐시 조회
        cached_result = self._cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT: {cache_key[:16]}...")
            return cached_result

        # 3. API 호출 (캐시 미스)
        logger.info(f"Cache MISS: {cache_key[:16]}...")
        result = self._generate_uncached(prompt, style_name, aspect_ratio)

        # 4. 성공 시 캐시 저장
        if result.get("success"):
            self._cache.set(cache_key, result)

        return result

    def _generate_uncached(self, prompt: str, style_name: Optional[str] = None,
                           aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """기존 generate() 로직 (캐싱 없음)"""
        # ... 기존 Imagen API 호출 코드 ...
```

---

## 5. 추적성 (Traceability)

### 5.1 요구사항 → 구현 매핑

| 요구사항 ID | 구현 위치 | 테스트 시나리오 |
|------------|----------|----------------|
| REQ-U-001 | `generate_cache_key()` | TC-001 |
| REQ-U-002 | `ImageCache.get_stats()` | TC-006 |
| REQ-U-003 | `threading.RLock` 사용 | TC-007 |
| REQ-U-004 | `ImageCache.get()` 반환 형식 | TC-002 |
| REQ-E-001 | `ImageGenerator.generate()` 시작부 | TC-001 |
| REQ-E-002 | `ImageCache.get()` HIT 분기 | TC-002 |
| REQ-E-003 | `ImageCache.set()` 호출 | TC-003 |
| REQ-E-004 | `CacheEntry.expires_at` 검사 | TC-004 |
| REQ-E-005 | `OrderedDict` LRU 정책 | TC-005 |
| REQ-E-006 | `ImageCache.clear()` | TC-008 |
| REQ-S-001 | `CACHE_ENABLED` 환경 변수 | TC-009 |
| REQ-S-002 | `CACHE_DISK_ENABLED` 분기 | TC-010 |
| REQ-S-003 | 파일 존재 검증 로직 | TC-011 |
| REQ-N-001 | try-except 캐시 오류 처리 | TC-012 |
| REQ-N-002 | 인터페이스 변경 없음 | 코드 리뷰 |

### 5.2 관련 SPEC

| 관련 SPEC | 관계 | 설명 |
|-----------|------|------|
| SPEC-IMG-001 | 선행 | 배치 이미지 생성 기능 (캐싱 통합 대상) |

---

## 6. Constitution 참조

### 6.1 기술 스택 준수

| 항목 | Constitution 정의 | 본 SPEC 준수 |
|------|------------------|--------------|
| Python 버전 | 3.10+ | 준수 (dataclasses, typing 사용) |
| 표준 라이브러리 | functools, hashlib | 준수 |
| 환경 변수 관리 | python-dotenv | 준수 |
| 로깅 | logging 모듈 | 준수 |

### 6.2 금지 패턴

- 외부 캐싱 라이브러리 사용 금지 (표준 라이브러리만 사용)
- 전역 상태 변경 금지 (클래스 인스턴스 내부에서만 상태 관리)
- 기존 MCP 도구 인터페이스 변경 금지
