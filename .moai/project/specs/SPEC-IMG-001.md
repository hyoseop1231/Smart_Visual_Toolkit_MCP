# SPEC-IMG-001: 배치 이미지 생성 시스템

| 항목 | 내용 |
|------|------|
| **SPEC ID** | SPEC-IMG-001 |
| **제목** | 배치 이미지 생성 시스템 |
| **상태** | Draft |
| **작성일** | 2026-01-17 |
| **우선순위** | High |

---

## 1. 개요

### 1.1 목적

현재 Smart Visual Toolkit MCP 서버의 `generate_image()` 도구는 단일 이미지만 생성할 수 있습니다. 이 SPEC은 여러 이미지를 동시에 생성하는 배치 처리 기능을 정의합니다.

### 1.2 범위

- 배치 이미지 생성 MCP 도구 추가
- 비동기 이미지 생성 래퍼 구현
- 동시성 제어 (API rate limit 대응)
- 진행 상황 추적 기능
- 단위 테스트 및 통합 테스트

### 1.3 용어 정의

| 용어 | 정의 |
|------|------|
| **배치** | 여러 개의 이미지 생성 요청을 그룹으로 처리 |
| **동시성** | asyncio를 활용한 비동기 병렬 처리 |
| **Semaphore** | 동시 실행 수를 제한하는 동기화 프리미티브 |

---

## 2. 요구사항 (EARS 형식)

### 2.1 기능 요구사항

#### REQ-IMG-001: 배치 이미지 생성 도구

**WHEN** 사용자가 `generate_images_batch()` MCP 도구를 호출하고
**AND** 프롬프트 목록을 제공하면
**THEN** 시스템은 모든 이미지를 비동기로 생성하고
**AND** 각 이미지의 생성 결과를 포함한 목록을 반환한다

**인수:**
- `prompts`: 프롬프트 문자열 목록 (필수)
- `style_name`: 스타일 이름 (선택, 기본값: "Flat Corporate")
- `max_concurrent`: 최대 동시 생성 수 (선택, 기본값: 3)

#### REQ-IMG-002: 비동기 단일 이미지 생성

**WHEN** 내부적으로 배치 처리가 실행될 때
**THEN** 시스템은 기존 동기 `generate()` 메서드를 async 래퍼로 호출한다
**AND** 각 생성 작업은 독립적으로 오류를 처리한다

#### REQ-IMG-003: 동시성 제어

**WHEN** 배치 요청에 포함된 이미지 수가 `max_concurrent`를 초과하면
**THEN** 시스템은 `asyncio.Semaphore`를 사용하여 동시 실행 수를 제한한다
**AND** API rate limit 오류를 방지한다

#### REQ-IMG-004: 진행 상황 추적

**WHEN** 배치 이미지 생성이 진행 중일 때
**THEN** 시스템은 완료된 이미지 수와 전체 이미지 수를 로깅한다
**AND** 각 이미지 완료 시점에 로그를 출력한다

#### REQ-IMG-005: 부분 실패 처리

**WHEN** 배치 중 일부 이미지 생성이 실패하면
**THEN** 시스템은 나머지 이미지 생성을 계속 진행한다
**AND** 최종 결과에 성공/실패 상태를 각각 포함한다

#### REQ-IMG-006: 결과 형식

**WHEN** 배치 이미지 생성이 완료되면
**THEN** 시스템은 다음 형식의 결과를 반환한다:
```json
{
  "total": 5,
  "success_count": 4,
  "failure_count": 1,
  "results": [
    {"prompt": "...", "success": true, "local_path": "..."},
    {"prompt": "...", "success": false, "error": "..."}
  ]
}
```

### 2.2 비기능 요구사항

#### REQ-NFR-001: 성능

**WHEN** 5개의 이미지를 동시에 생성할 때 (max_concurrent=3)
**THEN** 전체 소요 시간은 순차 처리 대비 50% 이상 단축된다

#### REQ-NFR-002: 메모리 안정성

**WHEN** 대량 배치 (10개 이상)를 처리할 때
**THEN** 메모리 사용량은 선형적으로 증가하지 않는다
**AND** Semaphore로 동시 메모리 사용을 제한한다

#### REQ-NFR-003: 테스트 커버리지

**WHEN** 구현이 완료되면
**THEN** 신규 코드의 테스트 커버리지는 85% 이상이어야 한다

---

## 3. 설계

### 3.1 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                           │
└────────────────────────┬────────────────────────────────┘
                         │ generate_images_batch(prompts, ...)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server (main.py)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ @mcp.tool() generate_images_batch()              │   │
│  │   └── ImageGenerator.generate_batch()            │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           ImageGenerator (image_gen.py)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ async generate_batch(prompts, max_concurrent)    │   │
│  │   ├── asyncio.Semaphore(max_concurrent)          │   │
│  │   ├── asyncio.gather(*tasks)                     │   │
│  │   └── _generate_single_async(prompt)             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 클래스 다이어그램

```python
class ImageGenerator:
    # 기존 메서드
    def generate(self, prompt, style_name, aspect_ratio) -> Dict

    # 신규 메서드
    async def _generate_single_async(self, prompt, style_name, aspect_ratio) -> Dict
    async def generate_batch(self, prompts, style_name, max_concurrent) -> Dict
```

### 3.3 시퀀스 다이어그램

```
User       MCP Server      ImageGenerator     Google API
  │             │                │                │
  │──prompts───►│                │                │
  │             │──generate_batch()──►│           │
  │             │                │──Semaphore(3)──│
  │             │                │                │
  │             │                │◄──gather()────►│
  │             │                │   (3 concurrent)
  │             │                │                │
  │             │◄───results─────│                │
  │◄───JSON─────│                │                │
```

---

## 4. 인수 테스트 시나리오

### 4.1 정상 케이스

#### TC-001: 기본 배치 생성

```gherkin
Given GOOGLE_API_KEY 환경 변수가 설정되어 있고
And 3개의 프롬프트가 준비되어 있을 때
When generate_images_batch(prompts=["dog", "cat", "bird"]) 호출하면
Then 3개의 이미지가 모두 생성되고
And 각 이미지의 local_path가 반환된다
```

#### TC-002: 스타일 지정 배치

```gherkin
Given 2개의 프롬프트와 "Pixel Art" 스타일이 지정되어 있을 때
When generate_images_batch(prompts=["robot", "spaceship"], style_name="Pixel Art") 호출하면
Then 모든 이미지가 Pixel Art 스타일로 생성된다
```

#### TC-003: 동시성 제한

```gherkin
Given 6개의 프롬프트가 있고 max_concurrent=2로 설정되어 있을 때
When generate_images_batch() 호출하면
Then 동시에 최대 2개의 이미지만 생성되고
And 모든 이미지가 순차적으로 완료된다
```

### 4.2 예외 케이스

#### TC-004: 부분 실패

```gherkin
Given 3개의 프롬프트 중 하나가 API 오류를 발생시킬 때
When generate_images_batch() 호출하면
Then 2개는 성공하고 1개는 실패 상태로 반환된다
And failure_count가 1이다
```

#### TC-005: 빈 프롬프트 목록

```gherkin
Given 빈 프롬프트 목록이 제공되었을 때
When generate_images_batch(prompts=[]) 호출하면
Then 오류 메시지가 반환된다
And 이미지가 생성되지 않는다
```

#### TC-006: API 키 없음

```gherkin
Given GOOGLE_API_KEY가 설정되지 않았을 때
When generate_images_batch() 호출하면
Then 모든 이미지가 실패하고
And 적절한 오류 메시지가 반환된다
```

---

## 5. 구현 마일스톤

### M1: 핵심 기능 (Day 1-2)

- [ ] `_generate_single_async()` 메서드 구현
- [ ] `generate_batch()` 메서드 구현
- [ ] `generate_images_batch()` MCP 도구 추가
- [ ] 기본 로깅 추가

### M2: 테스트 (Day 3)

- [ ] 단위 테스트 작성 (pytest)
- [ ] Mock API 테스트
- [ ] 통합 테스트 작성
- [ ] 커버리지 85% 달성

### M3: 문서화 및 최적화 (Day 4)

- [ ] README 업데이트
- [ ] API 문서 추가
- [ ] 성능 최적화 (필요시)
- [ ] 코드 리뷰 및 리팩토링

---

## 6. 리스크 및 고려사항

| 리스크 | 영향 | 완화 방안 |
|--------|------|-----------|
| Google API rate limit | 대량 요청 시 429 오류 | Semaphore로 동시성 제한, 지수 백오프 구현 |
| 메모리 사용량 증가 | 대량 이미지 생성 시 OOM | 결과를 스트리밍으로 반환, 임시 파일 즉시 저장 |
| 네트워크 불안정 | 일부 요청 실패 | 재시도 로직, 부분 실패 허용 |

---

## 7. 참조

- [Google GenAI Python SDK](https://github.com/googleapis/python-genai)
- [asyncio.Semaphore 문서](https://docs.python.org/3/library/asyncio-sync.html)
- [FastMCP 문서](https://github.com/jlowin/fastmcp)
