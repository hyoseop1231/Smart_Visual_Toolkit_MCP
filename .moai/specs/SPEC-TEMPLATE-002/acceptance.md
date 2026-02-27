# SPEC-TEMPLATE-002: 인수 기준

## TAG BLOCK

```yaml
SPEC_ID: SPEC-TEMPLATE-002
Title: 템플릿 갤러리 UI 기능 인수 기준
Created: 2026-01-19
Status: Ready for Testing
Version: 1.0.0
```

## 인수 기준 개요

### 완료 정의 (Definition of Done)

**SPEC-TEMPLATE-002는 다음 조건이 모두 충족될 때 완료로 간주됩니다**:

1. 모든 필수 요구사항(REQ-TEMPLATE-001 ~ REQ-TEMPLATE-008)이 구현됨
2. 모든 테스트 시나리오가 통과함
3. 테스트 커버리지가 85% 이상임
4. TRUST 5 품질 게이트를 통과함
5. 성능 목표가 충족됨
6. API 및 사용자 문서가 완료됨

## 테스트 시나리오 (Test Scenarios)

### 배지 시스템 테스트

#### Scenario 1: 인기 템플릿 배지 표시

**Given**:
- 100개의 템플릿이 존재함
- 템플릿 A의 사용 횟수가 127회로 상위 10%에 해당함
- 현재 날짜가 2026-01-19임

**When**:
- 사용자가 템플릿 갤러리를 로드함

**Then**:
- 템플릿 A 카드에 "Popular" 배지가 표시됨
- 배지 색상과 스타일이 디자인 가이드를 준수함
- 배지 계산 시간이 100ms 이내임

**추적가능성**: REQ-TEMPLATE-001, REQ-TEMPLATE-004

---

#### Scenario 2: 신규 템플릿 배지 표시

**Given**:
- 템플릿 B가 2026-01-18(어제)에 생성됨
- 템플릿 C가 2026-01-10(9일 전)에 생성됨

**When**:
- 사용자가 템플릿 갤러리를 로드함

**Then**:
- 템플릿 B에 "New" 배지가 표시됨
- 템플릿 C에는 "New" 배지가 표시되지 않음
- 배지는 생성일로부터 정확히 7일간 표시됨

**추적가능성**: REQ-TEMPLATE-001, REQ-TEMPLATE-005

---

#### Scenario 3: 추천 템플릿 배지 표시

**Given**:
- 템플릿 D의 사용 횟수가 상위 30%에 해당함 (usage_percentile >= 70)
- 템플릿 D가 30일 이내에 업데이트됨

**When**:
- 사용자가 템플릿 갤러리를 로드함

**Then**:
- 템플릿 D에 "Recommended" 배지가 표시됨
- 추천 배지는 인기도와 최신성 조건을 모두 충족할 때만 표시됨

**추적가능성**: REQ-TEMPLATE-001

---

#### Scenario 4: 다중 배지 표시

**Given**:
- 템플릿 E가 상위 5% 사용량을 가짐 (Popular)
- 템플릿 E가 3일 전에 생성됨 (New)
- 템플릿 E가 최근 업데이트됨 (Recommended)

**When**:
- 사용자가 템플릿 갤러리를 로드함

**Then**:
- 템플릿 E에 세 개의 배지(Popular, New, Recommended)가 모두 표시됨
- 배지가 올바른 순서로 정렬됨 (Popular > New > Recommended)
- 배지가 서로 겹치지 않고 명확하게 구분됨

**추적가능성**: REQ-TEMPLATE-001

---

### 즐겨찾기 기능 테스트

#### Scenario 5: 즐겨찾기 추가

**Given**:
- 사용자가 로그인됨
- 템플릿 F가 사용자의 즐겨찾기에 없음
- `user_preferences.json`이 존재함

**When**:
- 사용자가 템플릿 F의 빈 하트 아이콘을 클릭함

**Then**:
- 템플릿 F가 사용자의 즐겨찾기 목록에 추가됨
- 하트 아이콘이 채워진 상태(❤️)로 변경됨
- `user_preferences.json`에 `template_f_id`가 저장됨
- 응답 시간이 50ms 이내임
- 페이지 새로고침 후에도 즐겨찾기 상태가 유지됨

**추적가능성**: REQ-TEMPLATE-002, REQ-TEMPLATE-006, REQ-TEMPLATE-008

---

#### Scenario 6: 즐겨찾기 제거

**Given**:
- 사용자가 로그인됨
- 템플릿 G가 이미 사용자의 즐겨찾기에 있음

**When**:
- 사용자가 템플릿 G의 채워진 하트 아이콘을 클릭함

**Then**:
- 템플릿 G가 사용자의 즐겨찾기 목록에서 제거됨
- 하트 아이콘이 빈 상태(🤍)로 변경됨
- `user_preferences.json`에서 `template_g_id`가 제거됨
- 응답 시간이 50ms 이내임

**추적가능성**: REQ-TEMPLATE-002, REQ-TEMPLATE-006, REQ-TEMPLATE-008

---

#### Scenario 7: 즐겨찾기 필터링

**Given**:
- 사용자가 10개의 템플릿을 즐겨찾기로 등록함
- 전체 템플릿 수가 100개임

**When**:
- 사용자가 "즐겨찾기만 표시" 필터를 활성화함

**Then**:
- 즐겨찾기한 10개의 템플릿만 표시됨
- 각 템플릿에 채워진 하트 아이콘이 표시됨
- 필터 비활성화 시 모든 템플릿이 다시 표시됨

**추적가능성**: REQ-TEMPLATE-002

---

#### Scenario 8: 즐겨찾기 지속성

**Given**:
- 사용자가 템플릿 H를 즐겨찾기로 등록함
- `user_preferences.json`에 저장됨

**When**:
- 사용자가 브라우저를 닫음
- 사용자가 다시 애플리케이션에 접속함

**Then**:
- 템플릿 H가 여전히 즐겨찾기로 표시됨
- 채워진 하트 아이콘이 유지됨
- `last_updated` 타임스탬프가 정확함

**추적가능성**: REQ-TEMPLATE-008

---

### 공유 기능 테스트

#### Scenario 9: URL 공유

**Given**:
- 템플릿 I가 존재함
- 템플릿 I의 ID가 `chart-line-001`임

**When**:
- 사용자가 템플릿 I의 공유 버튼을 클릭함
- "URL로 공유" 옵션을 선택함

**Then**:
- 공유 가능한 URL이 생성됨 (예: `https://example.com/templates/chart-line-001`)
- URL이 클립보드에 복사됨
- 성공 메시지가 표시됨
- URL을 통해 다른 사용자가 템플릿에 접근할 수 있음

**추적가능성**: REQ-TEMPLATE-003

---

#### Scenario 10: JSON 내보내기

**Given**:
- 템플릿 J가 존재함
- 템플릿 J의 메타데이터가 완전함

**When**:
- 사용자가 템플릿 J의 공유 버튼을 클릭함
- "JSON으로 내보내기" 옵션을 선택함

**Then**:
- 템플릿 J의 전체 설정이 JSON 형식으로 생성됨
- JSON이 다운로드되거나 클립보드에 복사됨
- JSON은 Pydantic 모델 스키마를 준수함
- JSON을 통해 템플릿을 복원할 수 있음

**추적가능성**: REQ-TEMPLATE-003

---

#### Scenario 11: YAML 내보내기

**Given**:
- 템플릿 K가 존재함

**When**:
- 사용자가 템플릿 K의 공유 버튼을 클릭함
- "YAML으로 내보내기" 옵션을 선택함

**Then**:
- 템플릿 K의 전체 설정이 YAML 형식으로 생성됨
- YAML이 다운로드되거나 클립보드에 복사됨
- YAML은 유효한 형식임
- YAML을 통해 템플릿을 복원할 수 있음

**추적가능성**: REQ-TEMPLATE-003

---

### 메트릭 추적 테스트

#### Scenario 12: 템플릿 사용 시 메트릭 기록

**Given**:
- 템플릿 L의 초기 `usage_count`가 50임
- 템플릿 L의 `updated_at`이 2026-01-15임

**When**:
- 사용자가 템플릿 L을 선택하여 적용함

**Then**:
- 템플릿 L의 `usage_count`가 51로 증가함
- 템플릿 L의 `updated_at`이 현재 시간으로 갱신됨
- 메타데이터 파일에 변경사항이 저장됨

**추적가능성**: REQ-TEMPLATE-007

---

#### Scenario 13: 동시 사용 시 메트릭 정확성

**Given**:
- 템플릿 M의 초기 `usage_count`가 100임
- 5명의 사용자가 동시에 템플릿 M을 사용함

**When**:
- 모든 사용자가 거의 동시에 템플릿 M을 적용함

**Then**:
- 템플릿 M의 최종 `usage_count`가 105임
- 모든 증가가 정확히 기록됨 (경합 조건 없음)
- 데이터 무결성이 유지됨

**추적가능성**: REQ-TEMPLATE-007

---

### 통합 시나리오 테스트

#### Scenario 14: 완전한 사용자 워크플로우

**Given**:
- 사용자가 처음으로 템플릿 갤러리에 접속함
- 50개의 템플릿이 존재함

**When**:
- 사용자가 갤러리를 탐색함
- "Popular" 배지가 있는 템플릿 N을 발견함
- 템플릿 N을 즐겨찾기에 추가함
- 템플릿 N을 적용하여 메트릭을 기록함
- 템플릿 N을 친구에게 공유함

**Then**:
- 모든 단계가 성공적으로 완료됨
- 즐겨찾기가 저장됨
- 메트릭이 증가함
- 공유 링크가 생성됨
- 전체 워크플로우가 2초 이내에 완료됨

**추적가능성**: REQ-TEMPLATE-001, REQ-TEMPLATE-002, REQ-TEMPLATE-003, REQ-TEMPLATE-007

---

## 성능 테스트 (Performance Tests)

### PT-01: 배지 계산 성능

**목표**: 1,000개의 템플릿에 대한 배지 계산이 500ms 이내에 완료되어야 함

**Given**:
- 1,000개의 템플릿이 존재함
- 각 템플릿에 사용 메트릭이 있음

**When**:
- 시스템이 모든 템플릿의 배지를 계산함

**Then**:
- 계산 시간이 500ms 이내임
- 각 템플릿당 평균 0.5ms 이내
- 메모리 사용량이 50MB 이하임

---

### PT-02: 목록 로드 성능

**목표**: 템플릿 목록 로드가 500ms 이내에 완료되어야 함

**Given**:
- 500개의 템플릿이 존재함
- 배지 계산이 필요함

**When**:
- 사용자가 템플릿 갤러리를 로드함

**Then**:
- 전체 로드 시간이 500ms 이내임
- 로딩 상태가 적절히 표시됨
- 스크롤이 부드러움

---

### PT-03: 즐겨찾기 토글 성능

**목표**: 즐겨찾기 토글이 50ms 이내에 완료되어야 함

**Given**:
- 사용자가 즐겨찾기를 토글하려 함

**When**:
- 사용자가 즐겨찾기 버튼을 클릭함

**Then**:
- 토글 요청이 50ms 이내에 처리됨
- UI가 즉시 업데이트됨
- 저장소 업데이트가 비동기로 완료됨

---

## 보안 테스트 (Security Tests)

### ST-01: 사용자 선호도 파일 접근 제어

**목표**: 사용자 선호도 파일이 적절하게 보호되어야 함

**Given**:
- `user_preferences.json`이 사용자 홈 디렉토리에 있음

**When**:
- 다른 사용자가 파일에 접근하려 함

**Then**:
- 파일 권한이 사용자 전용으로 설정됨 (600)
- 다른 사용자가 파일을 읽을 수 없음
- 민감 정보가 암호화됨 (필요시)

---

### ST-02: 공유 URL 보안

**목표**: 공유 URL이 적절하게 보호되어야 함

**Given**:
- 사용자가 템플릿 공유 URL을 생성함

**When**:
- 공유 URL이 생성됨

**Then**:
- URL에 예측 불가능한 토큰이 포함됨 (선택사항)
- URL에 만료 기간이 설정됨 (선택사항)
- 인증되지 않은 사용자는 URL로 접근할 수 없음 (필요시)

---

## 접근성 테스트 (Accessibility Tests)

### AT-01: 키보드 네비게이션

**목표**: 모든 기능이 키보드로 접근 가능해야 함

**Given**:
- 사용자가 마우스를 사용하지 않음

**When**:
- 사용자가 Tab 키로 탐색함
- Enter/Space 키로 상호작용함

**Then**:
- 모든 인터랙티브 요소에 초점이 맞춰짐
- Enter/Space 키로 버튼이 작동함
- 초점 순서가 논리적임
- 시각적 초점 표시기가 명확함

---

### AT-02: 스크린 리더 호환성

**목표**: 스크린 리더로 모든 콘텐츠를 이해할 수 있어야 함

**Given**:
- 사용자가 스크린 리더를 사용함

**When**:
- 사용자가 템플릿 갤러리를 탐색함

**Then**:
- 모든 배지가 적절히 설명됨
- 버튼 상태(즐겨찾기 추가됨/제거됨)가 명확함
- ARIA 라벨이 제공됨
- 이미지에 대체 텍스트가 제공됨

---

## 품질 게이트 (Quality Gates)

### TRUST 5 기준

**Test-first (테스트 우선)**:
- [ ] 테스트 커버리지 85% 이상
- [ ] 모든 핵심 기능에 단위 테스트 존재
- [ ] 통합 테스트가 주요 워크플로우를 커버

**Readable (가독성)**:
- [ ] Ruff 린터 통과 (0 경고)
- [ ] 함수 이름이 명확함
- [ ] 코드 복잡도가 허용 범위 내

**Unified (통일성)**:
- [ ] Black 포매터 적용
- [ ] 일관된 import 순서
- [ ] 일관된 명명 규칙

**Secured (보안)**:
- [ ] OWASP Top 10 취약점 없음
- [ ] 사용자 데이터 적절히 보호
- [ ] 입력 검증 완료

**Trackable (추적가능)**:
- [ ] 모든 요구사항에 추적가능성 태그 존재
- [ ] Git 커밋 메시지가 명확함
- [ ] 변경 로그 유지됨

---

## 자동화 테스트 전략

### 단위 테스트 (pytest)

```python
# tests/test_badge_calculator.py
def test_calculate_popular_badge():
    """상위 10% 사용량 템플릿에 Popular 배지 부여"""
    templates = create_test_templates(100, usage_distribution=[90, 10])
    top_template = templates[0]

    badges = calculate_template_badges(top_template, templates)

    assert "Popular" in badges

def test_calculate_new_badge():
    """7일 이내 생성된 템플릿에 New 배지 부여"""
    template = create_test_template(created_days_ago=3)

    badges = calculate_template_badges(template, [template])

    assert "New" in badges

# tests/test_favorites.py
def test_toggle_favorite_add():
    """즐겨찾기 추가 테스트"""
    prefs = UserPreferences(favorite_templates=[])

    updated = toggle_favorite(prefs, "template-001")

    assert "template-001" in updated.favorite_templates

def test_toggle_favorite_remove():
    """즐겨찾기 제거 테스트"""
    prefs = UserPreferences(favorite_templates=["template-001"])

    updated = toggle_favorite(prefs, "template-001")

    assert "template-001" not in updated.favorite_templates
```

### 통합 테스트

```python
# tests/test_integration.py
async def test_full_workflow():
    """완전한 사용자 워크플로우 테스트"""
    # 1. 템플릿 목록 로드
    response = await client.get("/api/templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) > 0

    # 2. 즐겨찾기 추가
    template_id = templates[0]["id"]
    response = await client.post(f"/api/templates/{template_id}/favorite")
    assert response.status_code == 200
    assert template_id in response.json()["favorite_templates"]

    # 3. 공유 URL 생성
    response = await client.post(f"/api/templates/{template_id}/share")
    assert response.status_code == 200
    assert "url" in response.json()
```

### E2E 테스트 (Playwright)

```typescript
// tests/e2e/template-gallery.spec.ts
test('complete user workflow', async ({ page }) => {
  await page.goto('/templates');

  // 배지 표시 확인
  await expect(page.locator('.badge-popular')).toBeVisible();

  // 즐겨찾기 토글
  await page.click('[data-testid="favorite-button"]');
  await expect(page.locator('.heart-filled')).toBeVisible();

  // 공유 버튼 클릭
  await page.click('[data-testid="share-button"]');
  await expect(page.locator('.share-dialog')).toBeVisible();
});
```

---

## 테스트 실행 방법

### 로컬 테스트 실행

```bash
# 단위 테스트
pytest tests/unit/ -v --cov=src --cov-report=html

# 통합 테스트
pytest tests/integration/ -v

# E2E 테스트
playwright test tests/e2e/

# 전체 테스트 스위트
pytest tests/ -v --cov=src --cov-report=term-missing
```

### CI/CD 파이프라인

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml
      - name: Check coverage
        run: |
          coverage=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); print(root.attrib['line-rate'])")
          if (( $(echo "$coverage < 0.85" | bc -l) )); then exit 1; fi
```

---

## 인수 체크리스트

### 기능적 요구사항

- [ ] REQ-TEMPLATE-001: 배지가 올바르게 표시됨
- [ ] REQ-TEMPLATE-002: 즐겨찾기 토글이 작동함
- [ ] REQ-TEMPLATE-003: 공유 기능이 작동함
- [ ] REQ-TEMPLATE-004: Popular 배지가 상위 10%에 표시됨
- [ ] REQ-TEMPLATE-005: New 배지가 7일 이내 템플릿에 표시됨
- [ ] REQ-TEMPLATE-006: 즐겨찾기 상태가 올바르게 표시됨
- [ ] REQ-TEMPLATE-007: 메트릭이 추적됨
- [ ] REQ-TEMPLATE-008: 선호도가 지속됨

### 비기능적 요구사항

- [ ] 성능 목표 충족 (500ms, 100ms, 50ms)
- [ ] 테스트 커버리지 85% 이상
- [ ] TRUST 5 품질 게이트 통과
- [ ] 보안 테스트 통과
- [ ] 접근성 테스트 통과

### 문서화

- [ ] API 문서 완료
- [ ] 사용자 가이드 완료
- [ ] 개발자 문서 완료
- [ ] 코드 주석 추가

---

## 참조 (References)

- SPEC-TEMPLATE-002/spec.md: 요구사항 상세
- SPEC-TEMPLATE-002/plan.md: 구현 계획
- TRUST 5 Framework: 품질 기준
- pytest Documentation: https://docs.pytest.org/
- Playwright Documentation: https://playwright.dev/
