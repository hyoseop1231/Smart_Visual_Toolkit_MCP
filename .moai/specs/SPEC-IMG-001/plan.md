---
spec_id: SPEC-IMG-001
document_type: "Implementation Plan"
version: "1.0.0"
created: "2026-01-17"
updated: "2026-01-17"
author: "Hyoseop"
complexity: "Medium"
---

# SPEC-IMG-001: 구현 계획

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-17 | Hyoseop | 초기 구현 계획 작성 |

---

## 1. 기술 스택

### 1.1 핵심 기술

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 기본 런타임 |
| asyncio | 표준 라이브러리 | 비동기 처리, 병렬 실행 |
| FastMCP | 0.1.0+ | MCP 서버 프레임워크 |
| google-genai | >= 0.2.0 | Imagen 4.0 API 클라이언트 |

### 1.2 개발 도구

| 도구 | 용도 |
|------|------|
| pytest | 단위 테스트 |
| pytest-asyncio | 비동기 테스트 |
| pytest-cov | 커버리지 측정 |

---

## 2. 구현 마일스톤 (우선순위 기반)

### 2.1 Primary Goal (핵심 목표)

| 순서 | 작업 | 산출물 | 완료 기준 |
|------|------|--------|----------|
| 1 | `_generate_single_async()` 메서드 구현 | 코드 | 단일 이미지 비동기 생성 성공 |
| 2 | `generate_batch()` 메서드 구현 | 코드 | 병렬 이미지 생성 동작 확인 |
| 3 | `generate_images_batch()` MCP 도구 구현 | 코드 | MCP 클라이언트에서 호출 가능 |

### 2.2 Secondary Goal (보조 목표)

| 순서 | 작업 | 산출물 | 완료 기준 |
|------|------|--------|----------|
| 4 | 입력 검증 로직 추가 | 코드 | 잘못된 입력에 대한 적절한 오류 반환 |
| 5 | 부분 실패 처리 로직 | 코드 | 일부 실패 시에도 나머지 결과 반환 |
| 6 | 결과 포맷팅 개선 | 코드 | 사용자 친화적 출력 |

### 2.3 Final Goal (최종 목표)

| 순서 | 작업 | 산출물 | 완료 기준 |
|------|------|--------|----------|
| 7 | 단위 테스트 작성 | 테스트 코드 | 핵심 기능 테스트 커버리지 85%+ |
| 8 | 통합 테스트 작성 | 테스트 코드 | E2E 시나리오 검증 |
| 9 | 문서화 | README 업데이트 | 사용 예시 및 API 문서 |

### 2.4 Optional Goal (선택적 목표)

| 순서 | 작업 | 산출물 | 조건 |
|------|------|--------|------|
| 10 | 진행률 콜백 지원 | 코드 | 시간 여유 시 |
| 11 | 배치 취소 기능 | 코드 | 사용자 요청 시 |

---

## 3. 기술적 접근 방식

### 3.1 비동기 처리 전략

```python
# 핵심 패턴: Semaphore + gather
async def generate_batch(...):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def task_with_limit(idx, item):
        async with semaphore:
            return await self._generate_single_async(...)

    tasks = [task_with_limit(i, p) for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**장점**:
- 동시 요청 수 제어로 API Rate Limit 준수
- `return_exceptions=True`로 부분 실패 허용
- 병렬 처리로 총 실행 시간 단축

### 3.2 기존 코드 재사용

```
기존 generate() 메서드
        │
        ▼
run_in_executor() 래핑
        │
        ▼
_generate_single_async()
        │
        ▼
generate_batch()에서 병렬 호출
```

**장점**:
- 기존 검증된 로직 재사용
- 코드 중복 최소화
- 유지보수성 향상

### 3.3 오류 처리 전략

| 오류 유형 | 처리 방식 | 사용자 피드백 |
|----------|----------|--------------|
| API 초기화 실패 | 전체 배치 실패 | 명확한 오류 메시지 |
| 개별 이미지 실패 | 해당 항목만 실패 처리 | 실패 원인 포함 |
| Rate Limit | 재시도 없이 실패 기록 | Rate Limit 오류 표시 |
| 타임아웃 | 해당 항목만 실패 처리 | 타임아웃 메시지 |

---

## 4. 아키텍처 설계 방향

### 4.1 레이어 구조

```
┌─────────────────────────────────────────────┐
│              MCP Interface Layer            │
│         generate_images_batch() 도구         │
├─────────────────────────────────────────────┤
│             Business Logic Layer            │
│           ImageGenerator 클래스              │
│         generate_batch() 메서드              │
├─────────────────────────────────────────────┤
│              Infrastructure Layer           │
│     Google GenAI SDK, asyncio, logging      │
└─────────────────────────────────────────────┘
```

### 4.2 책임 분리

| 레이어 | 책임 |
|--------|------|
| MCP Interface | 입력 검증, 출력 포맷팅, 도구 등록 |
| Business Logic | 배치 처리 로직, 병렬화, 결과 집계 |
| Infrastructure | API 호출, 파일 저장, 로깅 |

---

## 5. 영향 받는 파일

### 5.1 수정 대상 파일

| 파일 경로 | 변경 내용 | 영향도 |
|----------|----------|--------|
| `src/generators/image_gen.py` | `_generate_single_async()`, `generate_batch()` 메서드 추가 | HIGH |
| `src/main.py` | `generate_images_batch()` MCP 도구 추가 | HIGH |

### 5.2 신규 생성 파일

| 파일 경로 | 내용 |
|----------|------|
| `tests/test_batch_generation.py` | 배치 생성 단위 테스트 |
| `tests/conftest.py` | 테스트 픽스처 (필요시) |

### 5.3 참조 파일 (변경 없음)

| 파일 경로 | 참조 이유 |
|----------|----------|
| `src/resources/banana_styles.json` | 스타일 정의 참조 |

---

## 6. 의존성 분석

### 6.1 내부 의존성

| 의존 대상 | 사용 방식 | 영향도 |
|----------|----------|--------|
| `ImageGenerator.generate()` | 내부 호출 (재사용) | HIGH |
| `STYLES` 딕셔너리 | 스타일 검증 | LOW |
| `output_dir` 경로 | 파일 저장 | LOW |

### 6.2 외부 의존성

| 라이브러리 | 버전 | 용도 | 대안 |
|-----------|------|------|------|
| `asyncio` | 표준 라이브러리 | 비동기 처리 | 없음 (필수) |
| `google-genai` | >= 0.2.0 | 이미지 생성 API | 없음 |

### 6.3 호환성 매트릭스

| Python 버전 | asyncio 지원 | 호환 여부 |
|------------|-------------|----------|
| 3.10 | 완전 지원 | 호환 |
| 3.11 | 완전 지원 (개선) | 호환 |
| 3.12 | 완전 지원 (개선) | 호환 |
| 3.13 | 완전 지원 | 호환 |

---

## 7. 위험 평가 및 완화 전략

### 7.1 기술적 위험

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| **API Rate Limit 초과** | MEDIUM | HIGH | Semaphore로 동시 요청 제한 (기본 5개) |
| **메모리 사용량 증가** | LOW | MEDIUM | 스트리밍 저장, 즉시 파일 쓰기 |
| **타임아웃** | MEDIUM | MEDIUM | 개별 타임아웃 설정, 부분 실패 허용 |
| **네트워크 불안정** | LOW | HIGH | 재시도 로직 (선택적) |

### 7.2 비즈니스 위험

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|----------|
| **대량 요청으로 인한 비용 증가** | MEDIUM | HIGH | 배치 크기 제한 (최대 10개) |
| **사용자 혼란** | LOW | LOW | 명확한 결과 메시지 |

### 7.3 Rate Limit 고려사항

```python
# Google Imagen API Rate Limit (예상)
# - 분당 요청 수: ~60 RPM (확인 필요)
# - 일일 요청 수: 제한 있음

# 완화 전략:
# 1. max_concurrent 기본값 5로 설정
# 2. 배치 크기 최대 10개 제한
# 3. 사용자가 max_concurrent 조정 가능 (최대 5)
```

### 7.4 메모리 사용량 고려

```python
# 이미지 1개당 예상 메모리:
# - PNG 이미지: 1-5 MB
# - 10개 배치: 최대 50 MB

# 완화 전략:
# 1. 이미지 생성 즉시 파일로 저장
# 2. 메모리에 이미지 바이트 유지하지 않음
# 3. 결과에는 파일 경로만 포함
```

---

## 8. 테스트 전략

### 8.1 단위 테스트

| 테스트 대상 | 테스트 케이스 | 검증 항목 |
|------------|-------------|----------|
| `_generate_single_async()` | 정상 생성 | 반환 형식, 파일 생성 |
| `_generate_single_async()` | 실패 처리 | 예외 처리, 오류 형식 |
| `generate_batch()` | 빈 입력 | 빈 결과 반환 |
| `generate_batch()` | 정상 배치 | 병렬 실행, 결과 집계 |
| `generate_batch()` | 부분 실패 | 성공/실패 분리 |

### 8.2 통합 테스트

| 시나리오 | 입력 | 예상 출력 |
|---------|------|----------|
| MCP 도구 호출 | 3개 프롬프트 | 3개 결과 |
| 배치 크기 초과 | 15개 프롬프트 | 오류 메시지 |
| 스타일 혼합 | 개별 + 기본 스타일 | 올바른 스타일 적용 |

### 8.3 테스트 환경

```python
# pytest-asyncio 필요
# pip install pytest-asyncio

# conftest.py
import pytest

@pytest.fixture
def mock_genai_client():
    """Google GenAI 클라이언트 모킹"""
    ...

@pytest.fixture
def image_generator(mock_genai_client):
    """테스트용 ImageGenerator 인스턴스"""
    ...
```

---

## 9. 배포 고려사항

### 9.1 하위 호환성

- 기존 `generate_image()` 도구는 변경 없이 유지
- 새로운 `generate_images_batch()` 도구 추가
- 기존 사용자 워크플로우 영향 없음

### 9.2 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `GOOGLE_API_KEY` | 예 | - | Google API 키 |
| `BATCH_MAX_SIZE` | 아니오 | 10 | 최대 배치 크기 (선택적) |
| `BATCH_MAX_CONCURRENT` | 아니오 | 5 | 최대 동시 요청 수 (선택적) |

### 9.3 로깅 전략

```python
# 배치 작업 로깅
logging.info(f"Starting batch generation: {len(prompts)} images")
logging.info(f"Batch complete: {succeeded}/{total} succeeded")
logging.warning(f"Batch partial failure: {failed} images failed")
logging.error(f"Batch generation error: {error}")
```

---

## 10. 추적성 태그

```
SPEC-IMG-001 | plan.md
생성일: 2026-01-17
마지막 수정: 2026-01-17
상태: Draft
```
