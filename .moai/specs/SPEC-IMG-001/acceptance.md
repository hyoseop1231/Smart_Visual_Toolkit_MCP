---
spec_id: SPEC-IMG-001
document_type: "Acceptance Criteria"
version: "1.0.0"
created: "2026-01-17"
updated: "2026-01-17"
author: "Hyoseop"
test_scenario_count: 12
---

# SPEC-IMG-001: 인수 기준

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-17 | Hyoseop | 초기 인수 기준 작성 |

---

## 1. 핵심 인수 기준 (Given-When-Then)

### TC-001: 성공적인 배치 이미지 생성

**요구사항 참조**: REQ-E-001, REQ-E-003

```gherkin
Feature: 배치 이미지 생성
  배치 이미지 생성 시스템 사용자로서
  여러 이미지를 한 번에 생성하고 싶다
  생산성을 높이기 위해

  Scenario: 여러 프롬프트로 이미지 배치 생성
    Given Google API 클라이언트가 정상적으로 초기화되어 있고
    And 다음 프롬프트 목록이 주어졌을 때:
      | prompt                          | style              |
      | A futuristic city at sunset     | Cyberpunk          |
      | A peaceful mountain landscape   | Watercolor Map     |
      | Abstract data visualization     | Isometric Infographic |
    When generate_images_batch 도구를 호출하면
    Then 응답에 "total": 3이 포함되어야 하고
    And 응답에 "succeeded": 3이 포함되어야 하고
    And 응답에 "failed": 0이 포함되어야 하고
    And 각 결과에 "local_path"가 포함되어야 하고
    And 각 파일이 output/images/ 디렉토리에 존재해야 한다
```

**검증 방법**:
- 단위 테스트: `test_batch_generation_success()`
- 수동 테스트: MCP 클라이언트에서 도구 호출

---

### TC-002: 부분 실패 처리

**요구사항 참조**: REQ-E-002, REQ-N-001

```gherkin
Feature: 부분 실패 시 나머지 이미지 생성 계속
  배치 작업 중 일부가 실패해도
  나머지 이미지는 정상적으로 생성되어야 한다

  Scenario: 일부 이미지 생성 실패 시 부분 성공 반환
    Given Google API 클라이언트가 초기화되어 있고
    And 다음 프롬프트 목록이 주어졌을 때:
      | prompt                    | style          | expected_result |
      | A valid image prompt      | Flat Corporate | success         |
      | [MOCK_FAIL] Invalid       | Cyberpunk      | failure         |
      | Another valid prompt      | Pixel Art      | success         |
    When generate_images_batch 도구를 호출하면
    Then 응답에 "total": 3이 포함되어야 하고
    And 응답에 "succeeded": 2가 포함되어야 하고
    And 응답에 "failed": 1이 포함되어야 하고
    And 실패한 항목에 "error" 필드가 포함되어야 하고
    And 성공한 항목에 "local_path"가 포함되어야 한다
```

**검증 방법**:
- 단위 테스트: `test_batch_partial_failure()`
- 모킹: API 호출 중 일부 실패 시뮬레이션

---

### TC-003: 빈 입력 검증

**요구사항 참조**: REQ-E-004

```gherkin
Feature: 빈 프롬프트 목록 처리
  빈 입력이 주어졌을 때
  시스템은 적절한 메시지를 반환해야 한다

  Scenario: 빈 프롬프트 목록으로 호출
    Given Google API 클라이언트가 초기화되어 있고
    And 빈 프롬프트 목록 []이 주어졌을 때
    When generate_images_batch 도구를 호출하면
    Then 응답에 "No prompts provided" 메시지가 포함되어야 하고
    And 응답에 오류가 아닌 안내 메시지가 포함되어야 한다
```

**검증 방법**:
- 단위 테스트: `test_batch_empty_input()`

---

### TC-004: 배치 크기 초과 검증

**요구사항 참조**: REQ-S-001, REQ-N-002

```gherkin
Feature: 배치 크기 제한 적용
  API 남용 방지를 위해
  최대 배치 크기를 초과하면 거부해야 한다

  Scenario: 최대 배치 크기(10) 초과
    Given Google API 클라이언트가 초기화되어 있고
    And 15개의 프롬프트가 포함된 목록이 주어졌을 때
    When generate_images_batch 도구를 호출하면
    Then 응답에 "exceeds maximum limit" 오류가 포함되어야 하고
    And 이미지 생성이 시작되지 않아야 한다
```

**검증 방법**:
- 단위 테스트: `test_batch_size_limit()`

---

### TC-005: 기본 스타일 적용

**요구사항 참조**: REQ-S-003

```gherkin
Feature: 기본 스타일 자동 적용
  스타일이 지정되지 않은 프롬프트에
  기본 스타일을 자동으로 적용해야 한다

  Scenario: 개별 스타일 미지정 시 기본 스타일 적용
    Given Google API 클라이언트가 초기화되어 있고
    And 다음 프롬프트 목록이 주어졌을 때:
      | prompt                    | style          |
      | A sunset over the ocean   | null           |
      | A forest path             | Pixel Art      |
    And default_style이 "Cyberpunk"로 설정되어 있을 때
    When generate_images_batch 도구를 호출하면
    Then 첫 번째 이미지는 "Cyberpunk" 스타일로 생성되어야 하고
    And 두 번째 이미지는 "Pixel Art" 스타일로 생성되어야 한다
```

**검증 방법**:
- 단위 테스트: `test_default_style_application()`

---

### TC-006: API 클라이언트 미초기화

**요구사항 참조**: REQ-S-002

```gherkin
Feature: API 클라이언트 미초기화 처리
  API 클라이언트가 초기화되지 않았을 때
  명확한 오류를 반환해야 한다

  Scenario: GOOGLE_API_KEY 미설정 시 오류 반환
    Given GOOGLE_API_KEY 환경 변수가 설정되지 않았고
    And Google API 클라이언트가 None일 때
    And 유효한 프롬프트 목록이 주어졌을 때
    When generate_images_batch 도구를 호출하면
    Then 모든 항목에 "Client is not initialized" 오류가 포함되어야 하고
    And 이미지 파일이 생성되지 않아야 한다
```

**검증 방법**:
- 단위 테스트: `test_client_not_initialized()`

---

### TC-007: 고유 파일명 생성

**요구사항 참조**: REQ-U-001

```gherkin
Feature: 고유 파일명 생성
  배치 내 모든 이미지는
  고유한 파일명을 가져야 한다

  Scenario: 동일 스타일로 여러 이미지 생성 시 파일명 고유성
    Given Google API 클라이언트가 초기화되어 있고
    And 동일한 스타일("Flat Corporate")로 3개의 프롬프트가 주어졌을 때
    When generate_images_batch 도구를 호출하면
    Then 3개의 서로 다른 파일 경로가 반환되어야 하고
    And 각 파일명에 타임스탬프가 포함되어야 한다
```

**검증 방법**:
- 단위 테스트: `test_unique_filenames()`

---

### TC-008: 동시 실행 제한

**요구사항 참조**: (성능 요구사항)

```gherkin
Feature: 동시 실행 수 제한
  API Rate Limit 보호를 위해
  동시 실행 수를 제한해야 한다

  Scenario: max_concurrent 파라미터로 동시 실행 제한
    Given Google API 클라이언트가 초기화되어 있고
    And 10개의 프롬프트가 주어졌을 때
    And max_concurrent가 3으로 설정되어 있을 때
    When generate_images_batch 도구를 호출하면
    Then 동시에 최대 3개의 API 호출만 실행되어야 하고
    And 모든 10개 이미지가 최종적으로 처리되어야 한다
```

**검증 방법**:
- 통합 테스트: `test_concurrent_limit()`
- Semaphore 동작 검증

---

## 2. 에러 처리 시나리오

### TC-009: API Rate Limit 처리

```gherkin
Feature: API Rate Limit 오류 처리
  API Rate Limit에 도달했을 때
  해당 이미지만 실패 처리하고 나머지는 계속 진행

  Scenario: Rate Limit 오류 발생 시 부분 실패
    Given Google API 클라이언트가 초기화되어 있고
    And 5개의 프롬프트가 주어졌을 때
    And 3번째 요청에서 Rate Limit 오류가 발생할 때
    When generate_images_batch 도구를 호출하면
    Then 3번째 항목만 실패로 표시되어야 하고
    And 실패 항목의 오류에 "rate limit" 정보가 포함되어야 하고
    And 나머지 4개는 정상 처리되어야 한다
```

---

### TC-010: 타임아웃 처리

```gherkin
Feature: 개별 요청 타임아웃 처리
  개별 이미지 생성이 타임아웃되어도
  다른 이미지 생성에 영향을 주지 않아야 한다

  Scenario: 일부 요청 타임아웃 시 부분 성공
    Given Google API 클라이언트가 초기화되어 있고
    And 3개의 프롬프트가 주어졌을 때
    And 2번째 요청이 타임아웃될 때
    When generate_images_batch 도구를 호출하면
    Then 2번째 항목만 실패로 표시되어야 하고
    And 1번째와 3번째는 정상 처리되어야 한다
```

---

### TC-011: 잘못된 스타일명 처리

```gherkin
Feature: 잘못된 스타일명 처리
  존재하지 않는 스타일이 지정되었을 때
  기본 스타일로 대체하여 처리

  Scenario: 존재하지 않는 스타일명 지정
    Given Google API 클라이언트가 초기화되어 있고
    And style이 "NonExistentStyle"로 설정된 프롬프트가 주어졌을 때
    When generate_images_batch 도구를 호출하면
    Then 이미지가 기본 스타일("Flat Corporate")로 생성되어야 한다
```

---

### TC-012: 혼합 화면비 처리

```gherkin
Feature: 다양한 화면비 지원
  배치 내 각 이미지에
  다른 화면비를 적용할 수 있어야 한다

  Scenario: 혼합 화면비로 배치 생성
    Given Google API 클라이언트가 초기화되어 있고
    And 다음 프롬프트 목록이 주어졌을 때:
      | prompt              | style          | aspect_ratio |
      | Social media post   | Flat Corporate | 1:1          |
      | YouTube thumbnail   | Cyberpunk      | 16:9         |
      | Mobile story        | Pixel Art      | 9:16         |
    When generate_images_batch 도구를 호출하면
    Then 각 이미지가 지정된 화면비로 생성되어야 한다
```

---

## 3. 품질 게이트 기준

### 3.1 테스트 커버리지

| 측정 항목 | 최소 기준 | 목표 |
|----------|----------|------|
| 라인 커버리지 | 80% | 90% |
| 브랜치 커버리지 | 75% | 85% |
| 함수 커버리지 | 90% | 100% |

### 3.2 성능 기준

| 측정 항목 | 기준값 | 측정 조건 |
|----------|--------|----------|
| 단일 이미지 생성 | < 30초 | 정상 네트워크 환경 |
| 5개 이미지 배치 | < 60초 | max_concurrent=5 |
| 10개 이미지 배치 | < 120초 | max_concurrent=5 |

### 3.3 안정성 기준

| 측정 항목 | 기준값 |
|----------|--------|
| 연속 성공률 | > 95% (정상 API 조건) |
| 부분 실패 복구율 | 100% (실패 항목 외 모두 성공) |
| 메모리 누수 | 없음 |

---

## 4. Definition of Done (완료 정의)

### 4.1 코드 완료 기준

- [ ] `_generate_single_async()` 메서드 구현 완료
- [ ] `generate_batch()` 메서드 구현 완료
- [ ] `generate_images_batch()` MCP 도구 구현 완료
- [ ] 입력 검증 로직 구현 완료
- [ ] 오류 처리 로직 구현 완료

### 4.2 테스트 완료 기준

- [ ] 모든 TC-001 ~ TC-012 시나리오 통과
- [ ] 라인 커버리지 80% 이상
- [ ] 모든 에지 케이스 테스트 통과

### 4.3 문서화 완료 기준

- [ ] README.md 업데이트 (새 도구 사용법)
- [ ] 코드 주석 추가 (핵심 로직)
- [ ] 인라인 docstring 작성

### 4.4 검증 완료 기준

- [ ] MCP 클라이언트에서 도구 호출 테스트
- [ ] 5개 이미지 배치 생성 성공
- [ ] 부분 실패 시 정상 동작 확인
- [ ] 로그 메시지 확인

---

## 5. 테스트 실행 가이드

### 5.1 단위 테스트 실행

```bash
# 테스트 의존성 설치
uv add --dev pytest pytest-asyncio pytest-cov

# 전체 테스트 실행
uv run pytest tests/ -v

# 커버리지 포함 실행
uv run pytest tests/ --cov=src --cov-report=html

# 특정 테스트만 실행
uv run pytest tests/test_batch_generation.py -v
```

### 5.2 통합 테스트 실행

```bash
# MCP 서버 실행
uv run src/main.py

# 다른 터미널에서 MCP 클라이언트 테스트
# (Claude Code, Obsidian 등에서 도구 호출)
```

### 5.3 수동 테스트 체크리스트

| 항목 | 테스트 방법 | 예상 결과 |
|------|-----------|----------|
| 기본 배치 생성 | 3개 프롬프트로 호출 | 3개 이미지 파일 생성 |
| 스타일 혼합 | 다양한 스타일 지정 | 각 스타일 적용 확인 |
| 부분 실패 | 잘못된 프롬프트 포함 | 일부만 실패, 나머지 성공 |
| 크기 초과 | 15개 프롬프트 | 오류 메시지 반환 |

---

## 6. 추적성 태그

```
SPEC-IMG-001 | acceptance.md
생성일: 2026-01-17
마지막 수정: 2026-01-17
테스트 시나리오 수: 12
상태: Draft
```
