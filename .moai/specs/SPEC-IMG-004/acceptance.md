# SPEC-IMG-004: 고급 이미지 제어 및 프롬프트 최적화
## Acceptance Criteria

---

## 1. 테스트 시나리오 (Test Scenarios)

### TC-ADV-001: 명시적 해상도로 이미지 생성

**Given**: 사용자가 1920x1080 해상도를 요청하고
**And**: 유효한 프롬프트 "A modern office workspace"를 제공하고
**And**: 스타일 "Corporate Memphis"를 선택한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 1920x1080 해상도의 이미지를 생성해야 하고
**And**: 생성된 이미지의 실제 너비는 1920픽셀이어야 하고
**And**: 생성된 이미지의 실제 높이는 1080픽셀이어야 하고
**And**: 결과 메시지에 "resolution_adjusted": false가 포함되어야 한다

---

### TC-ADV-002: 프롬프트 자동 강화

**Given**: 사용자가 프롬프트 "A business meeting"을 제공하고
**And**: 스타일 "Corporate Memphis"를 선택하고
**And**: `enhance_prompt=true`를 설정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 원본 프롬프트에 스타일 키워드를 추가해야 하고
**And**: 강화된 프롬프트에는 "flat design" 또는 "clean vector"가 포함되어야 하고
**And**: 결과 메시지에 "enhancement_applied": true가 포함되어야 하고
**And**: "applied_keywords" 배열에 추가된 키워드가 나열되어야 한다

---

### TC-ADV-003: 네거티브 프롬프트 적용

**Given**: 사용자가 프롬프트 "A portrait photo"를 제공하고
**And**: 네거티브 프롬프트 "blurry, low quality, distorted"를 지정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 네거티브 프롬프트를 API에 전달해야 하고
**And**: 생성된 이미지에는 흐릿하거나 왜곡된 요소가 없어야 하고
**And**: 결과 메시지에 사용된 네거티브 프롬프트가 포함되어야 한다

---

### TC-ADV-004: 스타일 강도 제어

**Given**: 사용자가 스타일 "Cyberpunk"를 선택하고
**And**: `style_intensity="strong"`을 설정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 "strong" 강도에 해당하는 4-6개 키워드를 추가해야 하고
**And**: 강화된 프롬프트에는 "neon", "futuristic", "high contrast" 등의 키워드가 포함되어야 하고
**And**: 결과 메시지에 "style_intensity": "strong"가 표시되어야 한다

**Given**: 사용자가 `style_intensity="weak"`을 설정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 "weak" 강도에 해당하는 1-2개 키워드만 추가해야 하고
**And**: 결과 메시지에 적용된 키워드 수가 1-2개여야 한다

---

### TC-ADV-005: 프롬프트 길이 검증 및 트리밍

**Given**: 사용자가 1200자 길이의 프롬프트를 제공하고
**And**: API 제한이 1000자이다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 프롬프트를 1000자로 트리밍해야 하고
**And:** 결과 메시지에 "was_trimmed": true가 포함되어야 하고
**And:** "original_length": 1200 및 "final_length": 1000가 표시되어야 하고
**And:** 사용자에게 트리밍 경고 메시지가 표시되어야 한다

---

### TC-ADV-006: 지원되지 않는 해상도 자동 조정

**Given**: 사용자가 4000x3000 해상도를 요청하고
**And:** API 최대 해상도는 2048x2048이다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 요청을 2048x1536으로 조정해야 하고 (비율 유지)
**And:** 결과 메시지에 "was_adjusted": true가 포함되어야 하고
**And:** "adjustment_reason": "Exceeded maximum resolution"가 표시되어야 하고
**And:** 최종 해상도가 API 제한 내여야 한다

---

### TC-ADV-007: 네거티브 프롬프트와 스타일 결합

**Given**: 사용자가 스타일 "Flat Corporate"를 선택하고
**And:** 네거티브 프롬프트 "3D render, realistic"을 지정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 스타일의 기본 네거티브 키워드와 사용자 입력을 병합해야 하고
**And:** 최종 네거티브 프롬프트에 "3D render", "realistic"이 포함되어야 하고
**And:** 생성된 이미지가 평면 스타일이어야 하며 (입체감 없음)
**And:** 사실적 렌더링이 없어야 한다

---

### TC-ADV-008: 프롬프트 강화 비활성화

**Given**: 사용자가 프롬프트 "A detailed description"를 제공하고
**And:** 스타일 "Isometric Infographic"를 선택하고
**And:** `enhance_prompt=false`를 설정한다

**When**: `generate_image_advanced()` 도구를 호출한다

**Then**: 시스템은 원본 프롬프트를 그대로 사용해야 하고
**And:** 스타일 키워드가 추가되지 않아야 하고
**And:** 결과 메시지에 "enhancement_applied": false가 포함되어야 하고
**And:** "enhanced" 프롬프트가 "original"과 동일해야 한다

---

## 2. Definition of Done

### 2.1 기능 완료 기준

- [ ] 모든 Primary 시나리오(TC-ADV-001 ~ TC-ADV-004) 통과
- [ ] 해상도 제어가 정상 작동
- [ ] 프롬프트 강화가 의도대로 작동
- [ ] 네거티브 프롬프트가 효과적으로 적용
- [ ] 스타일 강도 제어가 3단계(weak/normal/strong) 모두 작동

### 2.2 품질 게이트

- [ ] 단위 테스트 커버리지 85% 이상
- [ ] 모든 테스트 시나리오 통과
- [ ] Zero ruff linter 경고
- [ ] Zero mypy type errors
- [ ] API 문서 완비 (모든 매개변수 설명)

### 2.3 비기능 요구사항

- [ ] 프롬프트 전처리 시간 < 20ms
- [ ] 해상도 검증 시간 < 5ms
- [ ] 기존 `generate_image()` 도구 영향 없음 (역호환)
- [ ] 메모리 사용량 증가 < 50MB

### 2.4 문서화

- [ ] README 업데이트 (고급 기능 섹션)
- [ ] API 예제 코드 작성
- [ ] 마이그레이션 가이드 (기존 사용자용)
- [ ] 스타일 강도 가이드라인

---

## 3. 품질 검증 체크리스트

### 3.1 EARS 준수 여부

| 요구사항 유형 | 검증 항목 | 상태 |
|-------------|----------|------|
| Ubiquitous | 모든 호출에서 해상도 검증 수행 | ⬜ |
| Ubiquitous | 프롬프트 길이 항상 검증 | ⬜ |
| Event-Driven | 해상도 요청 시 정확한 해상도 생성 | ⬜ |
| Event-Driven | 프롬프트 강화 요청 시 키워드 추가 | ⬜ |
| Event-Driven | 네거티브 프롬프트 제공 시 적용 | ⬜ |
| Event-Driven | 스타일 강도 지정 시 해당 강도 적용 | ⬜ |
| State-Driven | 해상도 미지정 시 1024x1024 사용 | ⬜ |
| State-Driven | 강도 미지정 시 "normal" 사용 | ⬜ |
| State-Driven | 강화 비활성화 시 원본 프롬프트 사용 | ⬜ |
| Unwanted | 네거티브 프롬프트 혼합 방지 | ⬜ |
| Unwanted | 유효하지 않은 해상도로 API 호출 방지 | ⬜ |
| Unwanted | 프롬프트 강화로 핵심 메시지 희석 방지 | ⬜ |

### 3.2 TRUST 5 프레임워크 준수

| Pillar | 검증 항목 | 상태 |
|--------|----------|------|
| **Test-first** | 85% 이상 테스트 커버리지 | ⬜ |
| **Readable** | 명확한 함수/변수 명명 | ⬜ |
| **Unified** | 일관된 코드 스타일 (black, isort) | ⬜ |
| **Secured** | 입력 검증 (SQL injection, XSS 방지) | ⬜ |
| **Trackable** | 명확한 커밋 메시지 | ⬜ |

---

## 4. 사용자 수락 기준 (User Acceptance Criteria)

### 4.1 기능적 요구사항

사용자는 다음을 수행할 수 있어야 한다:

1. **해상도 제어**: 256x256 ~ 2048x2048 범위에서 픽셀 단위 해상도 지정
2. **프롬프트 강화**: 스타일에 맞는 키워드 자동 추가
3. **네거티브 프롬프트**: 제외할 요소 명시
4. **스타일 강도**: 3단계 강도 조절 (weak/normal/strong)
5. **프롬프트 검증**: API 제한 준수 및 자동 트리밍

### 4.2 비기능적 요구사항

시스템은 다음을 보장해야 한다:

1. **성능**: 전처리 시간 < 20ms
2. **호환성**: 기존 `generate_image()` 도구와 호환
3. **안정성**: 잘못된 입력으로 인한 크래시 없음
4. **가독성**: 명확한 오류 메시지 제공

### 4.3 사용자 경험

1. **명확한 피드백**: 조정/트리밍 발생 시 사용자에게 통지
2. **옵트아웃**: 프롬프트 강화 거부 옵션 제공
3. **합리적 기본값**: 별도 지정 시 sensible defaults 사용
4. **일관된 동작**: 동일 입력에 동일 출력

---

## 5. 성공 지표 (Success Metrics)

### 정량적 지표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 테스트 통과율 | 100% (필수), 80% (전체) | pytest 실행 |
| 코드 커버리지 | ≥ 85% | pytest-cov |
| 전처리 시간 | < 20ms | 벤치마크 테스트 |
| API 오류율 | < 1% | 통합 테스트 |

### 정성적 지표

| 지표 | 목표 | 평가 방법 |
|------|------|----------|
| 프롬프트 강화 품질 | 사용자 의도와 일치 | 수동 검토 |
| 스타일 강도 차별성 | 3단계가 명확히 구별됨 | A/B 테스트 |
| 네거티브 프롬프트 효과 | 불필요한 요소 제거됨 | 이미지 검토 |
| 오류 메시지 명확성 | 사용자가 조치 가능 | 사용자 피드백 |

---

## 6. 검증 방법 (Verification Methods)

### 6.1 자동화된 테스트

```bash
# 단위 테스트
pytest tests/test_prompt_enhancer.py -v
pytest tests/test_resolution_validator.py -v

# 통합 테스트
pytest tests/test_image_gen_advanced.py -v

# 커버리지 리포트
pytest --cov=src/models --cov=src/generators --cov-report=html
```

### 6.2 수동 테스트 시나리오

1. 다양한 해상도로 이미지 생성 시각적 검증
2. 스타일 강도별 결과 비교 (weak vs normal vs strong)
3. 네거티브 프롬프트 유무 비교
4. 프롬프트 강화 ON/OFF 비교

### 6.3 성능 벤치마크

```python
import time

def benchmark_prompt_enhancement():
    start = time.time()
    enhancer.enhance(prompt, style, intensity)
    duration = time.time() - start
    assert duration < 0.020  # 20ms 미만
```

---

## 7. 스테이킹 계획 (Staging Plan)

### Phase 1: Alpha (내부 테스트)
- 기본 기능 구현 완료
- 단위 테스트 통과
- 내부 검증

### Phase 2: Beta (제한적 공개)
- 통합 테스트 통과
- 소수 사용자 테스트
- 피드백 수집 및 개선

### Phase 3: RC (Release Candidate)
- 모든 테스트 통과
- 문서 완비
- 최종 검증

### Phase 4: GA (General Availability)
- 공식 릴리스
- README 업데이트
- 사용자 가이드 배포
