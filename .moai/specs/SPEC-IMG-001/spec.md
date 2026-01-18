---
id: SPEC-IMG-001
version: "1.0.0"
status: "draft"
created: "2026-01-17"
updated: "2026-01-17"
author: "Hyoseop"
priority: "HIGH"
lifecycle: "spec-anchored"
---

# SPEC-IMG-001: 배치 이미지 생성 시스템

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-17 | Hyoseop | 초기 SPEC 작성 |

---

## 1. Environment (환경)

### 1.1 현재 시스템 컨텍스트

```
현재 구현 상태:
├── src/main.py                    # MCP 서버 (7개 도구)
├── src/generators/image_gen.py    # ImageGenerator 클래스
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
| 단일 이미지 생성 | `generate()` 메서드가 한 번에 1개 이미지만 생성 | 다중 이미지 요청 시 순차적 호출 필요 |
| 병렬 처리 미지원 | asyncio 기반 병렬 처리 없음 | API 호출 시간 누적 |
| 진행률 추적 없음 | 배치 작업의 진행 상황 확인 불가 | 사용자 경험 저하 |

### 1.3 외부 의존성

| 의존성 | 버전 | 제약사항 |
|--------|------|---------|
| Google Gemini API | Imagen 4.0 | Rate Limit: 분당 요청 제한 있음 |
| google-genai SDK | >= 0.2.0 | `generate_images()` 메서드 사용 |

---

## 2. Assumptions (가정)

### 2.1 기술적 가정

| ID | 가정 | 신뢰도 | 검증 방법 |
|----|------|--------|----------|
| A-001 | Google Imagen API가 동시 요청을 처리할 수 있음 | HIGH | API 문서 확인 완료 |
| A-002 | asyncio.gather()로 병렬 API 호출이 가능함 | HIGH | Python 표준 라이브러리 |
| A-003 | 각 이미지 생성 요청은 독립적임 | HIGH | 현재 구현 분석 완료 |
| A-004 | API Rate Limit이 배치 크기에 영향을 줄 수 있음 | MEDIUM | 테스트 필요 |

### 2.2 비즈니스 가정

| ID | 가정 | 신뢰도 | 위험 시 대응 |
|----|------|--------|-------------|
| B-001 | 사용자가 한 번에 최대 10개 이미지 생성 요청 | MEDIUM | 배치 크기 제한 구현 |
| B-002 | 부분 실패 시에도 성공한 이미지 반환 필요 | HIGH | 부분 성공 처리 로직 |
| B-003 | 진행률 정보가 사용자 경험에 중요 | MEDIUM | 진행률 콜백 지원 |

### 2.3 5 Whys 분석 (근본 원인 분석)

**표면적 문제**: 여러 이미지를 생성하려면 시간이 오래 걸림

1. **Why?** `generate_image()` 도구가 한 번에 하나의 이미지만 생성함
2. **Why?** `ImageGenerator.generate()` 메서드가 단일 이미지만 처리하도록 설계됨
3. **Why?** Google Imagen API 호출이 동기적으로 수행됨
4. **Why?** 초기 구현 시 단순성을 위해 순차 처리로 설계됨
5. **근본 원인**: 병렬 처리 아키텍처가 초기 설계에 포함되지 않음

**해결 방향**: asyncio 기반 병렬 처리 + 배치 API 설계

---

## 3. Requirements (요구사항) - EARS 형식

### 3.1 Ubiquitous Requirements (항상 적용)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-U-001** | 시스템은 **항상** 배치 요청의 모든 이미지에 대해 고유한 파일명을 생성해야 한다 | 파일 충돌 방지 |
| **REQ-U-002** | 시스템은 **항상** 각 이미지 생성 결과를 개별적으로 기록해야 한다 (성공/실패 상태 포함) | 추적성 보장 |
| **REQ-U-003** | 시스템은 **항상** 오류 발생 시 사용자 친화적 메시지를 반환해야 한다 | 사용성 |

### 3.2 Event-Driven Requirements (이벤트 기반)

| ID | WHEN (이벤트) | THEN (동작) |
|----|--------------|-------------|
| **REQ-E-001** | **WHEN** 사용자가 배치 요청을 제출하면 | **THEN** 시스템은 입력된 모든 프롬프트에 대해 병렬 처리를 시작해야 한다 |
| **REQ-E-002** | **WHEN** 개별 이미지 생성이 실패하면 | **THEN** 시스템은 해당 실패를 기록하고 나머지 이미지 생성을 계속해야 한다 |
| **REQ-E-003** | **WHEN** 모든 이미지 생성이 완료되면 | **THEN** 시스템은 전체 결과(성공/실패 개수, 결과 목록)를 반환해야 한다 |
| **REQ-E-004** | **WHEN** 빈 입력이 제공되면 | **THEN** 시스템은 적절한 오류 메시지를 반환해야 한다 |

### 3.3 State-Driven Requirements (상태 기반)

| ID | IF (조건) | THEN (동작) |
|----|----------|-------------|
| **REQ-S-001** | **IF** 배치 크기가 최대 허용치(10)를 초과하면 | **THEN** 시스템은 요청을 거부하고 크기 제한 오류를 반환해야 한다 |
| **REQ-S-002** | **IF** API 클라이언트가 초기화되지 않았으면 | **THEN** 시스템은 모든 이미지에 대해 초기화 실패 오류를 반환해야 한다 |
| **REQ-S-003** | **IF** 개별 스타일이 지정되지 않은 프롬프트가 있으면 | **THEN** 시스템은 기본 스타일(Flat Corporate)을 적용해야 한다 |

### 3.4 Unwanted Behavior Requirements (금지 사항)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-N-001** | 시스템은 **절대** 개별 실패로 인해 전체 배치를 취소**하지 않아야 한다** | 부분 성공 보장 |
| **REQ-N-002** | 시스템은 **절대** 최대 배치 크기 제한을 무시**하지 않아야 한다** | API 남용 방지 |
| **REQ-N-003** | 시스템은 **절대** 원본 사용자 입력을 수정**하지 않아야 한다** | 사용자 의도 존중 |

### 3.5 Optional Requirements (선택적 기능)

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| **REQ-O-001** | **가능하면** 실시간 진행률 콜백을 제공한다 | LOW |
| **REQ-O-002** | **가능하면** 배치 작업 취소 기능을 제공한다 | LOW |
| **REQ-O-003** | **가능하면** 동일 프롬프트에 대해 다양한 변형 이미지 생성을 지원한다 | MEDIUM |

---

## 4. Specifications (세부 명세)

### 4.1 새로운 MCP 도구: `generate_images_batch()`

```python
@mcp.tool()
async def generate_images_batch(
    prompts: List[Dict[str, str]],
    default_style: Optional[str] = None,
    max_concurrent: int = 5
) -> str:
    """
    여러 이미지를 병렬로 생성합니다.

    Args:
        prompts: 프롬프트 목록. 각 항목은 {"prompt": str, "style": Optional[str]} 형태
        default_style: 개별 스타일이 없는 프롬프트에 적용할 기본 스타일
        max_concurrent: 동시 생성 최대 수 (기본값: 5)

    Returns:
        생성 결과 요약 (성공/실패 개수, 파일 경로 목록)
    """
```

### 4.2 입력 스키마

```json
{
  "prompts": [
    {
      "prompt": "A futuristic city skyline at sunset",
      "style": "Cyberpunk"
    },
    {
      "prompt": "A peaceful mountain landscape",
      "style": null
    },
    {
      "prompt": "Abstract data visualization",
      "style": "Isometric Infographic"
    }
  ],
  "default_style": "Flat Corporate",
  "max_concurrent": 5
}
```

### 4.3 출력 스키마

```json
{
  "success": true,
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    {
      "index": 0,
      "success": true,
      "prompt": "A futuristic city skyline at sunset",
      "style": "Cyberpunk",
      "local_path": "/path/to/gen_cyberpunk_20260117_123456.png"
    },
    {
      "index": 1,
      "success": true,
      "prompt": "A peaceful mountain landscape",
      "style": "Flat Corporate",
      "local_path": "/path/to/gen_flat_corporate_20260117_123457.png"
    },
    {
      "index": 2,
      "success": false,
      "prompt": "Abstract data visualization",
      "style": "Isometric Infographic",
      "error": "API rate limit exceeded"
    }
  ]
}
```

### 4.4 ImageGenerator 확장: `generate_batch()` 메서드

```python
async def generate_batch(
    self,
    prompts: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    asyncio.gather()를 사용하여 여러 이미지를 병렬로 생성합니다.

    병렬 처리 전략:
    1. Semaphore로 동시 요청 수 제한
    2. 각 요청은 독립적으로 실행
    3. 개별 실패는 전체에 영향을 주지 않음
    """
```

### 4.5 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Client (Claude Code 등)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ generate_images_batch() 호출
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       main.py (MCP Server)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               generate_images_batch() 도구                 │  │
│  │  - 입력 검증 (배치 크기, 프롬프트 형식)                      │  │
│  │  - 기본 스타일 적용                                        │  │
│  │  - ImageGenerator.generate_batch() 호출                   │  │
│  │  - 결과 포맷팅 및 반환                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  image_gen.py (ImageGenerator)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   generate_batch() 메서드                  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           asyncio.Semaphore(max_concurrent)         │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                           │                               │  │
│  │          ┌────────────────┼────────────────┐              │  │
│  │          ▼                ▼                ▼              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │ _generate_  │  │ _generate_  │  │ _generate_  │        │  │
│  │  │ single_     │  │ single_     │  │ single_     │        │  │
│  │  │ async()     │  │ async()     │  │ async()     │        │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │  │
│  │         │                │                │               │  │
│  │  ┌──────▼────────────────▼────────────────▼──────┐        │  │
│  │  │             asyncio.gather(*tasks)            │        │  │
│  │  │          (return_exceptions=True)             │        │  │
│  │  └───────────────────────────────────────────────┘        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ 병렬 API 호출
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Google Gemini Imagen 4.0 API                  │
│                (imagen-4.0-fast-generate-001 모델)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 추적성 (Traceability)

### 5.1 요구사항 → 구현 매핑

| 요구사항 ID | 구현 위치 | 테스트 시나리오 |
|------------|----------|----------------|
| REQ-U-001 | `ImageGenerator._generate_single_async()` | TC-007 |
| REQ-U-002 | `generate_batch()` 결과 포맷 | TC-001, TC-002 |
| REQ-U-003 | 오류 처리 로직 | TC-003, TC-004, TC-006 |
| REQ-E-001 | `ImageGenerator.generate_batch()` | TC-001 |
| REQ-E-002 | `_generate_single_async()` try-except | TC-002 |
| REQ-E-003 | `generate_images_batch()` 반환 포맷 | TC-001, TC-002 |
| REQ-E-004 | 입력 검증 로직 | TC-003 |
| REQ-S-001 | 배치 크기 검증 | TC-004 |
| REQ-S-002 | API 클라이언트 검증 | TC-006 |
| REQ-S-003 | 기본 스타일 적용 | TC-005 |
| REQ-N-001 | `asyncio.gather(return_exceptions=True)` | TC-002 |
| REQ-N-002 | 배치 크기 검증 | TC-004 |
| REQ-N-003 | 입력 처리 로직 | 코드 리뷰 |

### 5.2 관련 SPEC

| 관련 SPEC | 관계 | 설명 |
|-----------|------|------|
| - | - | 첫 번째 SPEC |

---

## 6. Constitution 참조

### 6.1 기술 스택 준수

| 항목 | Constitution 정의 | 본 SPEC 준수 |
|------|------------------|--------------|
| Python 버전 | 3.10+ | 준수 (async/await 지원) |
| 프레임워크 | FastMCP | 준수 (`@mcp.tool()` 데코레이터) |
| API | Google Gemini Imagen 4.0 | 준수 |
| 비동기 | asyncio, httpx | 준수 |

### 6.2 금지 패턴

- 동기 API 호출로 인한 블로킹 금지 (asyncio 사용)
- 전역 상태 변경 금지 (각 요청 독립적 처리)
