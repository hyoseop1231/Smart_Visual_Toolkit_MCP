# SPEC-TEMPLATE-003: 인수 기준

## 메타데이터

| 항목 | 값 |
|------|-----|
| SPEC ID | SPEC-TEMPLATE-003 |
| 문서 유형 | Acceptance Criteria |
| 버전 | 1.0.0 |
| 작성일 | 2026-01-19 |
| 작성자 | Alfred (Orchestrator) |

---

## 1. 인수 개요

### 1.1 Definition of Done

모든 기능은 다음 기준을 충족해야 합니다:

1. **기능 완료**: 모든 필수 기능이 구현되고 동작
2. **테스트 통과**: 모든 테스트 케이스 통과
3. **품질 기준**: 코드 커버리지 85%+, 린터 오류 0개
4. **문서 완성**: API 문서, 사용자 가이드 완성
5. **성능 목표**: 응답 시간 < 100ms

### 1.2 인수 테스트 절차

```text
Phase 1: 단위 테스트 실행
    ↓
Phase 2: 통합 테스트 실행
    ↓
Phase 3: 성능 테스트 실행
    ↓
Phase 4: 사용자 인수 테스트
    ↓
Phase 5: 문서 검증
```

---

## 2. 기능별 인수 기준

### 2.1 템플릿 스타일 매핑 (REQ-TMPL-001 ~ REQ-TMPL-003)

#### TC-TMPL-001: 이미지 생성 템플릿 매핑

**Given:** 사용자가 "corporate" 템플릿을 선택하여 이미지 생성을 요청

**When:** 시스템이 이미지 생성 도구를 호출

**Then:**
- 시스템은 "corporate" 템플릿의 스타일 키워드를 Nano Banana 스타일로 매핑
- 매핑된 키워드 ["Corporate Memphis", "3D Render", "Confetti"]가 프롬프트에 포함
- Google Imagen API가 올바른 스타일로 이미지 생성

**검증 방법:**
```python
# Given
template_id = "corporate"

# When
mapper = TemplateMapper(template_dir)
keywords = mapper.get_style_keywords(template_id)

# Then
assert keywords == ["Corporate Memphis", "3D Render", "Confetti"]
```

---

#### TC-TMPL-002: 스타일 키워드 병합

**Given:** 사용자가 "minimal" 템플릿 선택 + 추가 스타일 "watercolor" 지정

**When:** 시스템이 스타일 병합을 수행

**Then:**
- 사용자 스타일 "watercolor"가 우선순위로 적용
- 템플릿 스타일 ["Minimal", "Monochrome", "Line Art"]이 기본값으로 병합
- 중복 키워드가 제거된 최종 키워드 리스트 생성

**검증 방법:**
```python
# Given
template_keywords = ["Minimal", "Monochrome", "Line Art"]
user_keywords = ["Watercolor", "Map", "Fantasy"]

# When
merger = StyleMerger()
merged = merger.merge_styles(template_keywords, user_keywords)

# Then
assert "Watercolor" in merged  # User keyword priority
assert "Minimal" in merged      # Template keyword included
assert len(merged) == len(set(merged))  # No duplicates
```

---

#### TC-TMPL-003: 스타일 매핑 테이블

**Given:** 시스템이 시작될 때

**When:** 스타일 매핑 테이블 로드

**Then:**
- 15개 Nano Banana 스타일 모두 매핑됨
- JSON 형식으로 저장되어 런타임에 로드 가능
- 매핑 테이블 캐싱으로 성능 최적화

**검증 방법:**
```python
# Given
mapper = TemplateMapper(template_dir)

# When
mapping = mapper.load_style_mapping()

# Then
assert len(mapping) == 15  # All 15 styles mapped
assert "corporate" in mapping
assert "minimal" in mapping
assert mapping["corporate"] == ["Corporate Memphis", "3D Render", "Confetti"]
```

---

### 2.2 레이아웃 파라미터 변환 (REQ-TMPL-004 ~ REQ-TMPL-006)

#### TC-TMPL-004: 문서 생성 레이아웃 파라미터

**Given:** 사용자가 "report" 템플릿으로 Word 문서 생성 요청

**When:** 시스템이 레이아웃 파라미터 변환

**Then:**
- 템플릿 레이아웃 파라미터가 Skywork API 형식으로 변환
- 변환된 파라미터가 gen_doc 호출에 포함
- Word 문서가 지정된 레이아웃으로 생성

**검증 방법:**
```python
# Given
template = {
    "type": "doc",
    "layout_params": {
        "sections": 3,
        "pageLayout": "standard",
        "style": "professional"
    }
}

# When
transformer = LayoutTransformer()
skywork_params = transformer.transform_for_word(template["layout_params"])

# Then
assert skywork_params["sections"] == 3
assert skywork_params["page_layout"] == "standard"
assert skywork_params["style"] == "professional"
```

---

#### TC-TMPL-005: 레이아웃 제약조건 검증

**Given:** 템플릿이 "최대 10페이지" 제약조건 정의

**When:** 사용자가 15페이지 생성 요청

**Then:**
- 시스템이 제약조건 위반 감지
- 명확한 에러 메시지 반환
- 생성 요청 거부

**검증 방법:**
```python
# Given
template = {
    "constraints": {
        "max_pages": 10
    }
}
params = {"page_count": 15}

# When
validator = ConstraintValidator()
result = validator.validate_page_count(
    params["page_count"],
    template["constraints"]["max_pages"]
)

# Then
assert result == False  # Constraint violated
# API should reject with clear error message
```

---

#### TC-TMPL-006: 파라미터 변환 규칙

**Given:** 내부 템플릿 파라미터가 camelCase 형식

**When:** 시스템이 Skywork API 형식(snake_case)으로 변환

**Then:**
- `pageCount` → `page_count`
- `themeName` → `theme_name`
- 데이터 타입 올바르게 변환

**검증 방법:**
```python
# Given
internal_params = {
    "pageCount": 10,
    "themeName": "modern",
    "columns": 2
}

# When
converter = ParameterConverter()
api_params = converter.convert_params(internal_params, format="api")

# Then
assert "page_count" in api_params
assert "theme_name" in api_params
assert api_params["page_count"] == 10
assert api_params["theme_name"] == "modern"
```

---

### 2.3 하위 호환성 (REQ-TMPL-007 ~ REQ-TMPL-008)

#### TC-TMPL-007: 템플릿 없는 호출 지원

**Given:** 사용자가 템플릿 파라미터 없이 기존 방식으로 이미지 생성 요청

**When:** 시스템이 이미지 생성 처리

**Then:**
- 기존 방식과 동일하게 동작
- 추가 파라미터 없이 성공
- 결과물이 기존과 동일

**검증 방법:**
```python
# Given - Old way (no template)
prompt = "A serene mountain landscape"

# When
result = await generate_image(prompt)  # No template parameter

# Then
assert result["success"] == True
assert "image_url" in result
# Should behave exactly as before template system
```

---

#### TC-TMPL-008: API 스키마 검증

**Given:** 템플릿 파라미터가 API 제출 전에 검증됨

**When:** 잘못된 파라미터 이름이 포함된 요청

**Then:**
- 시스템이 스키마 위반 감지
- API 호출 전에 거부
- 명확한 에러 메시지 반환

**검증 방법:**
```python
# Given
invalid_params = {
    "invalid_param": "value",  # Not in API schema
    "page_count": 10
}

# When
validator = SchemaValidator()
result = validator.validate(invalid_params, skywork_schema)

# Then
assert result.is_valid == False
assert "invalid_param" in result.errors
# API call should NOT be made
```

---

### 2.4 비기능 요구사항 (REQ-TMPL-009 ~ REQ-TMPL-010)

#### TC-TMPL-009: 성능

**Given:** 템플릿 적용이 필요한 이미지 생성 요청

**When:** 시스템이 템플릿 로드, 파라미터 변환, 검증 수행

**Then:** 전체 오버헤드가 100ms 이내

**검증 방법:**
```python
# Given
template_id = "corporate"
import time

# When
start = time.time()
mapper = TemplateMapper(template_dir)
template = mapper.load_template(template_id)
merger = StyleMerger()
merged = merger.merge_styles(template["style_keywords"], [])
transformer = LayoutTransformer()
params = transformer.transform_for_doc(template["layout_params"])
end = time.time()

# Then
assert (end - start) < 0.1  # Less than 100ms
```

---

#### TC-TMPL-010: 오류 처리

**Given:** 템플릿 로드 실패 또는 파라미터 변환 실패

**When:** 오류가 발생

**Then:**
- 명확한 에러 메시지 반환
- 기본 스타일/레이아웃으로 대체
- 로그에 상세 정보 기록
- 사용자 경험 중단 최소화

**검증 방법:**
```python
# Given - Invalid template ID
invalid_template_id = "nonexistent_template"

# When
try:
    mapper = TemplateMapper(template_dir)
    template = mapper.load_template(invalid_template_id)
except Exception as e:
    # Then
    assert "template not found" in str(e).lower()
    assert e.__cause__ is not None  # Root cause logged
```

---

## 3. 통합 인수 테스트

### 3.1 엔드투엔드 시나리오

#### SCENARIO-E2E-001: 템플릿 기반 이미지 생성

**사용자 스토리:** 사용자는 "Cyberpunk" 스타일 템플릿을 선택하여 기술 블로그 헤더 이미지를 생성합니다.

**Given:**
- 시스템이 정상적으로 시작
- "cyberpunk" 템플릿이 존재
- Google API 키가 설정됨

**When:**
- 사용자가 `generate_image` 도구 호출
- `prompt`: "futuristic city skyline at night"
- `template`: "cyberpunk"

**Then:**
- 시스템이 템플릿 로드 성공
- 스타일 키워드 ["Cyberpunk", "Blue", "Circuit"]이 프롬프트에 병합
- Google Imagen API 호출 성공
- 사이버펑크 스타일 이미지 생성됨
- 응답 시간 < 100ms (템플릿 오버헤드)

**검증 체크리스트:**
- [ ] 템플릿 로드 성공
- [ ] 스타일 매핑 정확
- [ ] API 호출 성공
- [ ] 이미지 URL 반환
- [ ] 성능 목표 달성

---

#### SCENARIO-E2E-002: 템플릿 기반 Word 문서 생성

**사용자 스토리:** 사용자는 "report" 템플릿을 선택하여 분기 보고서 Word 문서를 생성합니다.

**Given:**
- 시스템이 정상적으로 시작
- "report" 템플릿이 존재
- Skywork 자격증명이 설정됨

**When:**
- 사용자가 `gen_doc` 도구 호출
- `query`: "2024 Q4 financial report"
- `template`: "report"

**Then:**
- 시스템이 템플릿 로드 성공
- 레이아웃 파라미터 변환 성공
- Skywork API 호출 성공
- 지정된 레이아웃으로 Word 문서 생성됨
- 다운로드 URL 반환

**검증 체크리스트:**
- [ ] 템플릿 로드 성공
- [ ] 레이아웃 파라미터 정확
- [ ] API 호출 성공
- [ ] 문서 URL 반환
- [ ] 레이아웃 적용됨

---

#### SCENARIO-E2E-003: 사용자 스타일 우선 병합

**사용자 스토리:** 사용자는 "minimal" 템플릿을 선택하지만, 추가 스타일 "watercolor"를 지정하여 두 스타일이 혼합된 이미지를 생성합니다.

**Given:**
- 시스템이 정상적으로 시작
- "minimal" 템플릿이 존재

**When:**
- 사용자가 `generate_image` 도구 호출
- `prompt`: "peaceful mountain landscape"
- `template`: "minimal"
- `style_keywords`: ["Watercolor", "Map", "Fantasy"]

**Then:**
- 시스템이 템플릿 스타일 ["Minimal", "Monochrome", "Line Art"] 로드
- 사용자 스타일 ["Watercolor", "Map", "Fantasy"] 우선 적용
- 중복 없이 병합된 키워드 리스트 생성
- 혼합 스타일 이미지 생성됨

**검증 체크리스트:**
- [ ] 템플릿 스타일 로드
- [ ] 사용자 스타일 우선 적용
- [ ] 중복 제거
- [ ] 병합된 키워드 사용
- [ ] 혼합 스타일 이미지 생성

---

#### SCENARIO-E2E-004: 하위 호환성 확인

**사용자 스토리:** 기존 사용자는 템플릿 시스템 도입 전과 동일한 방식으로 이미지를 생성합니다.

**Given:**
- 시스템이 정상적으로 시작
- 기존 사용자가 템플릿 파라미터 없이 호출

**When:**
- 사용자가 `generate_image` 도구 호출
- `prompt`: "A beautiful sunset over the ocean"
- `template`: 없음 (None)

**Then:**
- 시스템이 기존 방식대로 동작
- 추가 파라미터 처리 없음
- 기존과 동일한 결과 반환
- 성능 저하 없음

**검증 체크리스트:**
- [ ] 템플릿 없는 호출 성공
- [ ] 기존과 동일한 결과
- [ ] 성능 저하 없음
- [ ] 에러 없음

---

#### SCENARIO-E2E-005: 제약조건 위반 처리

**사용자 스토리:** 사용자가 템플릿 제약조건을 초과하는 페이지 수로 문서 생성을 시도합니다.

**Given:**
- 시스템이 정상적으로 시작
- "brief" 템플릿이 "최대 5페이지" 제약조건 정의

**When:**
- 사용자가 `gen_ppt` 도구 호출
- `query`: "comprehensive product presentation"
- `template`: "brief"
- `page_count`: 10 (제약조건 초과)

**Then:**
- 시스템이 제약조건 위반 감지
- 명확한 에러 메시지 반환: "Template 'brief' allows maximum 5 pages, but 10 requested"
- API 호출 없이 요청 거부
- 사용자가 제약조건을 이해하고 수정 가능

**검증 체크리스트:**
- [ ] 제약조건 검증 동작
- [ ] 명확한 에러 메시지
- [ ] API 호출 방지
- [ ] 사용자 친화적 메시지

---

## 4. 품질 게이트

### 4.1 코드 품질

| 항목 | 기준 | 측정 도구 | 상태 |
|------|------|----------|------|
| 테스트 커버리지 | 85%+ | pytest-cov | ⏳ |
| 린터 오류 | 0개 | ruff | ⏳ |
| 타입 검증 | 통과 | mypy | ⏳ |
| 보안 취약점 | 0개 | bandit | ⏳ |

### 4.2 성능 기준

| 항목 | 목표 | 측정 방법 | 상태 |
|------|------|----------|------|
| 템플릿 로드 | < 10ms | Benchmark | ⏳ |
| 파라미터 변환 | < 50ms | Benchmark | ⏳ |
| 전체 오버헤드 | < 100ms | End-to-end | ⏳ |
| 메모리 사용 | < 50MB | Profiler | ⏳ |

### 4.3 기능 기준

| 항목 | 기준 | 검증 방법 | 상태 |
|------|------|----------|------|
| 스타일 매핑 | 15개 스타일 모두 매핑 | Unit test | ⏳ |
| 레이아웃 변환 | 모든 파라미터 정확 변환 | Integration test | ⏳ |
| 하위 호환성 | 기존 호출 100% 동작 | Regression test | ⏳ |
| 오류 처리 | 모든 에러 케이스 처리 | Error test | ⏳ |

---

## 5. 인수 절차

### 5.1 Phase 1: 단위 테스트

```bash
# 템플릿 시스템 단위 테스트
pytest tests/templates/test_mapper.py -v
pytest tests/templates/test_merger.py -v
pytest tests/templates/test_transformer.py -v
pytest tests/templates/test_validator.py -v
pytest tests/templates/test_converter.py -v

# 커버리지 확인
pytest --cov=src/templates --cov-report=html
```

**합격 기준:**
- [ ] 모든 테스트 통과
- [ ] 커버리지 85%+ 달성

---

### 5.2 Phase 2: 통합 테스트

```bash
# 이미지 생성 통합 테스트
pytest tests/integration/test_template_image.py -v

# 문서 생성 통합 테스트
pytest tests/integration/test_template_word.py -v
pytest tests/integration/test_template_excel.py -v
pytest tests/integration/test_template_ppt.py -v

# 하위 호환성 테스트
pytest tests/integration/test_backward_compat.py -v
```

**합격 기준:**
- [ ] 모든 통합 테스트 통과
- [ ] 기존 기능 회귀 없음

---

### 5.3 Phase 3: 성능 테스트

```bash
# 성능 벤치마킹
pytest tests/benchmarks/test_template_performance.py -v
```

**합격 기준:**
- [ ] 템플릿 로드 < 10ms
- [ ] 파라미터 변환 < 50ms
- [ ] 전체 오버헤드 < 100ms

---

### 5.4 Phase 4: 사용자 인수 테스트

**수동 테스트 시나리오:**
1. Claude Code에서 `generate_image` 호출 (template 파라미터 포함)
2. Claude Code에서 `gen_doc` 호출 (template 파라미터 포함)
3. Claude Code에서 `gen_excel` 호출 (template 파라미터 포함)
4. Claude Code에서 `gen_ppt` 호출 (template 파라미터 포함)
5. 템플릿 없는 기존 호출 테스트

**합격 기준:**
- [ ] 모든 수동 테스트 성공
- [ ] 결과물이 예상과 일치
- [ ] 에러 메시지 명확함

---

### 5.5 Phase 5: 문서 검증

**검증 항목:**
- [ ] API 문서 완성
- [ ] 사용자 가이드 완성
- [ ] 예제 템플릿 3개 이상 제공
- [ ] README.md 업데이트
- [ ] 주요 코드에 docstring 포함

---

## 6. 인수 체크리스트

### 최종 인수 결정

- [ ] Phase 1: 단위 테스트 통과
- [ ] Phase 2: 통합 테스트 통과
- [ ] Phase 3: 성능 테스트 통과
- [ ] Phase 4: 사용자 인수 테스트 통과
- [ ] Phase 5: 문서 검증 완료
- [ ] 품질 게이트 모든 기준 충족
- [ ] 하위 호환성 100% 확인
- [ ] 보안 취약점 0개 확인

### 승인 서명

| 역할 | 이름 | 날짜 | 서명 | 상태 |
|------|------|------|------|------|
| 개발자 | Alfred | 2026-01-19 | ✓ | ⏳ |
| 검토자 | Hyoseop | - | - | ⏳ |
| 최종 승인자 | - | - | - | ⏳ |

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-19 | 초안 작성 | Alfred |

---

## 추적성 태그

```
TAG: SPEC-TEMPLATE-003
TAG: ACCEPTANCE-CRITERIA
TAG: TEST-SCENARIOS
TAG: QUALITY-GATES
TAG: E2E-TESTS
TAG: DEFINITION-OF-DONE
```
