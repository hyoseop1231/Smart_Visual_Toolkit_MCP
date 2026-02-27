# SPEC-TEMPLATE-001: 인수 기준 (Acceptance Criteria)

## TAG BLOCK

```yaml
spec:
  id: SPEC-TEMPLATE-001
  title: 통합 템플릿 갤러리 시스템
  status: Planned
  priority: HIGH

acceptance:
  test_scenarios: 25
  coverage_target: 85%
  quality_gates: TRUST 5
```

---

## 1. 인수 기준 개요 (Acceptance Criteria Overview)

### 1.1 정의 (Definition)

**인수 기준 (Acceptance Criteria)**: SPEC-TEMPLATE-001이 성공적으로 구현되었음을 확인하기 위한 구체적이고 측정 가능한 조건입니다.

### 1.2 테스트 전략 (Testing Strategy)

- **Given-When-Then 형식**: 모든 테스트 시나리오는 Gherkin 스타일로 작성
- **데이터 주도 테스트**: 다양한 입력 조건에 대한 테스트 케이스
- **회귀 테스트**: 기존 기능에 영향이 없는지 확인
- **품질 게이트**: TRUST 5 프레임워크 준수

---

## 2. 기능적 인수 기준 (Functional Acceptance Criteria)

### 2.1 템플릿 목록 조회 (REQ-T-101, REQ-T-104)

#### TC-T-101: 모든 템플릿 목록 조회

**Given** 시스템에 15개의 이미지 템플릿과 5개의 문서 템플릿이 등록되어 있고
**When** 사용자가 `list_templates()`를 호출하면
**Then** 시스템은 모든 20개 템플릿을 반환해야 하고
**And** 각 템플릿은 `template_id`, `name`, `content_type`, `description`을 포함해야 하고
**And** 응답 시간은 100ms 이하여야 한다

```python
# 테스트 코드 예시
def test_list_all_templates():
    # Given
    registry = TemplateRegistry()
    registry.load_all_templates()

    # When
    templates = registry.list_templates()

    # Then
    assert len(templates) == 20
    assert all(hasattr(t, 'template_id') for t in templates)
    assert all(hasattr(t, 'name') for t in templates)
```

#### TC-T-102: 콘텐츠 유형별 필터링

**Given** 시스템에 이미지, 문서, PPT, Excel 템플릿이 등록되어 있고
**When** 사용자가 `list_templates(content_type="image")`를 호출하면
**Then** 시스템은 이미지 템플릿만 반환해야 하고
**And** 다른 콘텐츠 유형의 템플릿은 포함하지 않아야 한다

```python
def test_list_templates_filtered_by_type():
    # Given
    registry = TemplateRegistry()
    registry.load_all_templates()

    # When
    image_templates = registry.list_templates(content_type=ContentType.IMAGE)

    # Then
    assert all(t.content_type == ContentType.IMAGE for t in image_templates)
```

#### TC-T-103: 카테고리별 필터링

**Given** 시스템에 "Business"와 "Creative" 카테고리의 템플릿이 등록되어 있고
**When** 사용자가 `list_templates(category="Business")`를 호출하면
**Then** 시스템은 "Business" 카테고리의 템플릿만 반환해야 한다

#### TC-T-104: 페이징 처리

**Given** 시스템에 100개 이상의 템플릿이 등록되어 있고
**When** 사용자가 `list_templates(limit=50, offset=0)`를 호출하면
**Then** 시스템은 처음 50개 템플릿을 반환해야 하고
**And** `list_templates(limit=50, offset=50)`를 호출하면 다음 50개를 반환해야 한다

---

### 2.2 템플릿 상세 조회

#### TC-T-201: 존재하는 템플릿 조회

**Given** 템플릿 ID "tpl-corp-memphis"가 등록되어 있고
**When** 사용자가 `get_template_details("tpl-corp-memphis")`를 호출하면
**Then** 시스템은 해당 템플릿의 상세 정보를 반환해야 하고
**And** 상세 정보는 모든 메타데이터 필드를 포함해야 한다

```python
def test_get_existing_template_details():
    # Given
    template_id = "tpl-corp-memphis"
    registry = TemplateRegistry()

    # When
    template = registry.get_template_details(template_id)

    # Then
    assert template.template_id == template_id
    assert template.name == "Corporate Memphis"
    assert template.content_type == ContentType.IMAGE
```

#### TC-T-202: 존재하지 않는 템플릿 조회

**Given** 템플릿 ID "tpl-nonexistent"가 등록되어 있지 않고
**When** 사용자가 `get_template_details("tpl-nonexistent")`를 호출하면
**Then** 시스템은 오류 메시지를 반환해야 하고
**And** 오류 메시지는 "Template not found"를 포함해야 한다

---

### 2.3 템플릿 적용 (REQ-T-102, REQ-T-201)

#### TC-T-301: 유효한 템플릿 적용 (이미지)

**Given** 템플릿 ID "tpl-corp-memphis"가 등록되어 있고
**When** 사용자가 `apply_template(template_id="tpl-corp-memphis", prompt="business meeting", content_type="image")`를 호출하면
**Then** 시스템은 템플릿 파라미터를 이미지 생성 API에 적용해야 하고
**And** 생성된 이미지는 "Corporate Memphis" 스타일을 따라야 하고
**And** 템플릿 사용 횟수가 증가해야 한다

```python
def test_apply_image_template():
    # Given
    template_id = "tpl-corp-memphis"
    prompt = "business meeting"

    # When
    result = apply_template(
        template_id=template_id,
        prompt=prompt,
        content_type=ContentType.IMAGE
    )

    # Then
    assert result["success"] is True
    assert "Corporate Memphis" in result["prompt"]
```

#### TC-T-302: 기본 템플릿 적용

**Given** 템플릿이 선택되지 않았고
**When** 사용자가 이미지 생성 요청을 하면
**Then** 시스템은 해당 콘텐츠 유형의 기본 템플릿을 적용해야 하고
**And** 이미지의 기본 템플릿은 "Flat Corporate"여야 한다

```python
def test_default_template_applied():
    # Given - no template selected
    prompt = "test image"

    # When
    result = generate_image(prompt=prompt)  # No template_id

    # Then
    assert result["success"] is True
    assert "Flat Corporate" in result.get("style", "")
```

#### TC-T-303: 호환되지 않는 템플릿 거부 (REQ-T-203)

**Given** 템플릿 "tpl-corp-memphis"가 `content_type="image"`로 등록되어 있고
**When** 사용자가 `apply_template(template_id="tpl-corp-memphis", content_type="document")`를 호출하면
**Then** 시스템은 호환성 오류를 반환해야 하고
**And** 오류 메시지는 "Template is not compatible with content type"을 포함해야 한다

```python
def test_incompatible_template_rejected():
    # Given
    template_id = "tpl-corp-memphis"  # IMAGE type

    # When
    result = apply_template(
        template_id=template_id,
        prompt="test",
        content_type=ContentType.DOCUMENT
    )

    # Then
    assert result["success"] is False
    assert "not compatible" in result["error"].lower()
```

#### TC-T-304: Skywork 문서 템플릿 적용 (REQ-T-102, Phase 4)

**Given** 템플릿 "tpl-doc-report"가 등록되어 있고
**When** 사용자가 `gen_doc(query="quarterly report", template_id="tpl-doc-report")`를 호출하면
**Then** 시스템은 템플릿 파라미터를 Skywork API에 전달해야 하고
**And** 생성된 문서는 템플릿 형식을 따라야 한다

---

### 2.4 템플릿 관리

#### TC-T-401: 템플릿 사용 로깅 (REQ-T-103)

**Given** 템플릿 "tpl-corp-memphis"가 등록되어 있고
**When** 사용자가 템플릿을 적용하여 콘텐츠를 생성하면
**Then** 시스템은 템플릿 사용 로그를 기록해야 하고
**And** 로그는 사용 시간, 템플릿 ID, 사용자를 포함해야 한다

```python
def test_template_usage_logging():
    # Given
    template_id = "tpl-corp-memphis"
    initial_count = get_template_usage_count(template_id)

    # When
    apply_template(template_id=template_id, prompt="test", content_type=ContentType.IMAGE)

    # Then
    final_count = get_template_usage_count(template_id)
    assert final_count == initial_count + 1
```

#### TC-T-402: 미리보기 없는 템플릿 처리 (REQ-T-202)

**Given** 템플릿 "tpl-custom"에 미리보기가 없고
**When** 사용자가 `get_template_details("tpl-custom")`를 호출하면
**Then** 시스템은 템플릿 메타데이터와 플레이스홀더를 반환해야 하고
**And** 플레이스홀더는 "No preview available" 메시지를 포함해야 한다

#### TC-T-403: 템플릿 로딩 실패 처리 (REQ-T-204)

**Given** 템플릿 파일이 손상되었고
**When** 시스템이 시작될 때
**Then** 시스템은 로깅에 오류를 기록해야 하고
**And** 기본 템플릿으로 대체해야 하고
**And** 시스템 시작은 계속되어야 한다

---

### 2.5 선택적 기능 (REQ-T-401 ~ REQ-T-404)

#### TC-T-501: 템플릿 즐겨찾기 추가 (REQ-T-401)

**Given** 사용자가 로그인되어 있고
**When** 사용자가 `add_template_favorite(template_id="tpl-corp-memphis")`를 호출하면
**Then** 시스템은 템플릿을 사용자의 즐겨찾기에 추가해야 하고
**And** `list_templates(favorites_only=True)`는 해당 템플릿을 포함해야 한다

#### TC-T-502: 사용자 정의 템플릿 생성 (REQ-T-402)

**Given** 사용자가 새로운 템플릿을 정의하고
**When** 사용자가 `create_custom_template(name="My Style", content_type="image", parameters={...})`를 호출하면
**Then** 시스템은 템플릿을 `templates_custom.json`에 저장해야 하고
**And** 템플릿은 `is_custom=True`로 표시되어야 하고
**And** 템플릿을 적용할 수 있어야 한다

```python
def test_create_custom_template():
    # Given
    custom_template = {
        "name": "My Custom Style",
        "content_type": "image",
        "parameters": {"style_keywords": "custom, unique"}
    }

    # When
    result = create_custom_template(**custom_template)

    # Then
    assert result["success"] is True
    assert result["template_id"].startswith("tpl-custom-")
```

#### TC-T-503: 템플릿 내보내기/가져오기 (REQ-T-403)

**Given** 사용자가 템플릿을 내보내고
**When** 사용자가 `export_template(template_id="tpl-corp-memphis", format="json")`를 호출하면
**Then** 시스템은 템플릿 정의를 JSON 파일로 반환해야 하고
**And** `import_template()`으로 해당 파일을 가져올 수 있어야 한다

---

## 3. 비기능적 인수 기준 (Non-Functional Acceptance Criteria)

### 3.1 성능 (Performance)

#### TC-NF-101: 템플릿 목록 조회 성능

**Given** 시스템에 100개의 템플릿이 있고
**When** `list_templates()`가 호출되면
**Then** 응답 시간은 100ms 이하여야 한다

```python
def test_list_templates_performance():
    # Given
    registry = TemplateRegistry()
    # Load 100 templates

    # When
    start_time = time.time()
    templates = registry.list_templates()
    duration = (time.time() - start_time) * 1000  # ms

    # Then
    assert duration < 100
```

#### TC-NF-102: 템플릿 적용 성능

**Given** 템플릿이 캐시되어 있고
**When** `apply_template()`가 호출되면
**Then** 템플릿 파라미터 변환은 50ms 이내에 완료되어야 한다 (API 호출 시간 제외)

#### TC-NF-103: 캐시 적중률

**Given** 동일한 템플릿이 반복 조회되고
**When** 10번 연속 조회가 수행되면
**Then** 캐시 적중률은 90% 이상이어야 한다

### 3.2 보안 (Security)

#### TC-NF-201: 파라미터 인젝션 방지

**Given** 악의적인 사용자가 템플릿 파라미터에 인젝션 코드를 포함시키고
**When** `create_custom_template()`가 호출되면
**Then** 시스템은 파라미터를 검증하고 거부해야 한다

```python
def test_prevent_parameter_injection():
    # Given
    malicious_params = {
        "style_keywords": "'; DROP TABLE templates; --"
    }

    # When
    result = create_custom_template(
        name="Malicious",
        content_type="image",
        parameters=malicious_params
    )

    # Then
    assert result["success"] is False
    assert "invalid" in result["error"].lower() or "malicious" in result["error"].lower()
```

#### TC-NF-202: 민감 정보 포함 방지

**Given** 사용자가 템플릿 파라미터에 API 키를 포함시키고
**When** 템플릿이 저장되면
**Then** 민감 정보는 마스킹되거나 거부되어야 한다

### 3.3 호환성 (Compatibility)

#### TC-NF-301: 하위 호환성 - style_name 파라미터

**Given** 기존 코드가 `style_name="Corporate Memphis"`를 사용하고
**When** `generate_image(prompt="test", style_name="Corporate Memphis")`가 호출되면
**Then** 시스템은 정상적으로 이미지를 생성해야 하고
**And** 결과는 템플릿을 사용한 것과 동일해야 한다

```python
def test_backward_compatibility_style_name():
    # Given
    prompt = "test image"
    style_name = "Corporate Memphis"

    # When - using old parameter
    result_old = generate_image(prompt=prompt, style_name=style_name)

    # And - using new template_id
    result_new = generate_image(
        prompt=prompt,
        template_id="tpl-corp-memphis"
    )

    # Then - results should be equivalent
    assert result_old["success"] == result_new["success"]
```

#### TC-NF-302: 기존 스타일 마이그레이션

**Given** 기존 `banana_styles.json`에 15개 스타일이 있고
**When** 마이그레이션 스크립트가 실행되면
**Then** 모든 15개 스타일이 새 템플릿 형식으로 변환되어야 하고
**And** 각 템플릿은 유효성 검증을 통과해야 한다

---

## 4. 품질 게이트 (Quality Gates)

### 4.1 TRUST 5 준수

**Test-first (테스트 우선):**
- [ ] 모든 요구사항에 대한 테스트 시나리오 작성
- [ ] 테스트 커버리지 85% 이상 달성

**Readable (가독성):**
- [ ] 함수/변수 네이밍 명확성
- [ ] 코드 복잡도 제어 (cyclomatic complexity < 10)
- [ ] 타입 힌트 포함

**Unified (통일성):**
- [ ] Black 포맷팅 준수
- [ ] 일관된 임포트 구조
- [ ] 일관된 로깅 패턴

**Secured (보안):**
- [ ] 파라미터 검증
- [ ] 인젝션 방지
- [ ] 민감 정보 보호

**Trackable (추적 가능):**
- [ ] Git 커밋 메시지 규칙 준수
- [ ] 변경 로그 기록
- [ ] 템플릿 사용 로그

### 4.2 테스트 커버리지

| 모듈 | 커버리지 목표 | 측정 도구 |
|------|---------------|-----------|
| `templates/models.py` | 90% | pytest-cov |
| `templates/repository.py` | 85% | pytest-cov |
| `templates/registry.py` | 85% | pytest-cov |
| `templates/validators.py` | 90% | pytest-cov |
| MCP 도구 | 80% | pytest-cov |
| **전체** | **85%** | pytest-cov |

### 4.3 릴리스 체크리스트

- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] 테스트 커버리지 85% 이상
- [ ] 보안 검증 통과
- [ ] 하위 호환성 확인
- [ ] 성능 벤치마크 통과
- [ ] 문서 완료 (API 문서, 사용자 가이드)
- [ ] 마이그레이션 가이드 작성

---

## 5. Definition of Done (완료 정의)

SPEC-TEMPLATE-001은 다음 조건이 모두 충족될 때 완료된 것으로 간주합니다:

### 5.1 필수 조건 (Must Have)

- [x] **Phase 1 완료**: 데이터 모델 및 리포지토리 구현
- [x] **Phase 2 완료**: 템플릿 레지스트리 및 마이그레이션
- [x] **Phase 3 완료**: MCP 도구 구현
- [x] **Phase 4 완료**: Skywork API 통합
- [ ] 모든 기능적 인수 기준 (TC-T-*) 통과
- [ ] 테스트 커버리지 85% 달성
- [ ] TRUST 5 품질 게이트 통과

### 5.2 선택적 조건 (Should Have)

- [ ] Phase 5 완료: 사용자 정의 템플릿 기능
- [ ] 모든 비기능적 인수 기준 (TC-NF-*) 통과
- [ ] 성능 벤치마크 달성
- [ ] 사용자 문서 완료

### 5.3 추가 조건 (Could Have)

- [ ] 템플릿 미리보기 자동 생성
- [ ] 템플릿 카테고리 관리 UI
- [ ] 템플릿 사용 분석 대시보드

---

## 6. 테스트 실행 가이드 (Test Execution Guide)

### 6.1 로컬 테스트

```bash
# 단위 테스트 실행
pytest tests/unit/test_templates.py -v

# 통합 테스트 실행
pytest tests/integration/test_template_tools.py -v

# 커버리지 확인
pytest --cov=src/templates --cov-report=html

# 특정 테스트 시나리오 실행
pytest -k "test_apply_image_template" -v
```

### 6.2 수동 테스트 시나리오

**시나리오 1: 기본 템플릿으로 이미지 생성**
```
1. Obsidian Smart Composer에서 다음 프롬프트 입력:
   "Generate an image of a business meeting"
2. 시스템이 "Flat Corporate" 기본 템플릿을 적용하는지 확인
3. 생성된 이미지의 스타일 확인
```

**시나리오 2: 템플릿 목록 조회**
```
1. Obsidian Smart Composer에서 다음 프롬프트 입력:
   "List all available templates for document generation"
2. 시스템이 문서 템플릿 목록을 반환하는지 확인
3. 각 템플릿의 메타데이터가 표시되는지 확인
```

**시나리오 3: 템플릿 적용**
```
1. Obsidian Smart Composer에서 다음 프롬프트 입력:
   "Generate a PPT presentation using the Business template"
2. 시스템이 템플릿을 적용하는지 확인
3. 생성된 PPT가 템플릿 형식을 따르는지 확인
```

---

**버전**: 1.0.0
**최종 수정**: 2025-01-19
**다음 검토**: Phase 1 완료 후
