# SPEC-TEMPLATE-001: 구현 계획 (Implementation Plan)

## TAG BLOCK

```yaml
spec:
  id: SPEC-TEMPLATE-001
  title: 통합 템플릿 갤러리 시스템
  status: Planned
  priority: HIGH

implementation:
  phases: 5
  estimated_milestones: 4
  dependencies:
    - SPEC-GALLERY-001
    - SPEC-CACHE-001
    - SPEC-IMG-004
```

---

## 1. 구현 개요 (Implementation Overview)

### 1.1 접근 방식 (Approach)

통합 템플릿 갤러리 시스템은 **점진적 마이그레이션**과 **하위 호환성 유지**를 원칙으로 구현합니다.

**핵심 전략:**
1. **기존 시스템 보존**: `banana_styles.json`과 `style_name` 파라미터 유지
2. **새로운 추상화 계층 추가**: `TemplateRepository`와 `TemplateRegistry` 도입
3. **점진적 마이그레이션**: 이미지 템플릿 → 문서/PPT/Excel 순으로 확장
4. **하위 호환성**: 템플릿 ID가 없으면 기존 방식대로 동작

### 1.2 기술 아키텍처 (Technical Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Tools Layer                          │
│  (list_templates, apply_template, get_template_details)     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Template Registry                           │
│  - Template loading & caching                                │
│  - Compatibility validation                                  │
│  - Default template resolution                               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                Template Repository                           │
│  - Unified metadata storage                                  │
│  - Query by content_type, category, tags                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Template Storage (JSON Files)                   │
│  templates_image.json │ templates_doc.json │ ...           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 구현 단계 (Implementation Phases)

### Phase 1: 데이터 모델 및 리포지토리 (Primary Goal)

**목표**: 템플릿 데이터 모델과 저장소 계층 구현

**작업 항목:**
- [ ] `src/templates/models.py` 구현
  - `ContentType` Enum 정의
  - `TemplateMetadata` dataclass 구현
  - 템플릿 유효성 검증 함수 구현

- [ ] `src/templates/repository.py` 구현
  - `TemplateRepository` 클래스 구현
  - 템플릿 CRUD 메서드 (get, list, create, update, delete)
  - 콘텐츠 유형별 필터링 메서드

- [ ] `src/templates/validators.py` 구현
  - `validate_template_schema()`: JSON 구조 검증
  - `validate_compatibility()`: 콘텐츠 유형 호환성 검증
  - `validate_parameters()`: 파라미터 유효성 검증

**완료 기준:**
- `TemplateRepository`의 모든 CRUD 메서드가 단위 테스트 통과
- 템플릿 스키마 검증이 JSON Schema로 구현됨

**의존성:** 없음 (독립적 시작)

---

### Phase 2: 템플릿 레지스트리 (Primary Goal)

**목표:** 템플릿 로딩, 캐싱, 기본 템플릿 해결 기능 구현

**작업 항목:**
- [ ] `src/templates/registry.py` 구현
  - `TemplateRegistry` 클래스 구현
  - 템플릿 파일 로딩 (JSON → TemplateMetadata 변환)
  - LRU 캐싱 통합 (SPEC-CACHE-001)
  - `get_default_template(content_type)` 메서드
  - `get_template(template_id)` 메서드

- [ ] 캐싱 통합
  - `TemplateCache` 클래스 (LRU + TTL)
  - 캐시 무효화 전략 (사용자 정의 템플릿 수정 시)

- [ ] 기존 `banana_styles.json` 마이그레이션
  - `src/resources/templates_image.json` 생성
  - 마이그레이션 스크립트 작성 및 실행

**완료 기준:**
- 모든 템플릿이 시작 시 1초 이내에 로드됨
- 캐시 적중률 80% 이상 (동일 템플릿 반복 조회 시)
- 기존 스타일이 새 템플릿 형식으로 변환됨

**의존성:** Phase 1 완료

---

### Phase 3: MCP 도구 구현 (Primary Goal)

**목표:** 템플릿 관리를 위한 MCP 도구 구현

**작업 항목:**
- [ ] `src/main.py`에 템플릿 도구 추가
  - `list_templates()`: 템플릿 목록 조회
  - `get_template_details()`: 템플릿 상세 정보
  - `apply_template()`: 템플릿 적용 (콘텐츠 생성)

- [ ] 기존 도구 확장
  - `generate_image()`: `template_id` 파라미터 추가
  - `generate_image_advanced()`: `template_id` 파라미터 추가
  - 하위 호환성 유지 (`style_name` 파라미터 계속 지원)

- [ ] 테스트
  - MCP 도구 호출 테스트 (Mock FastMCP)
  - 파라미터 검증 테스트

**완료 기준:**
- 모든 MCP 도구가 정상적으로 등록되고 호출됨
- `template_id`와 `style_name`이 모두 동작 (하위 호환성)
- 템플릿이 적용된 이미지 생성 성공

**의존성:** Phase 2 완료

---

### Phase 4: Skywork API 통합 (Secondary Goal)

**목표:** 문서/PPT/Excel 생성에 템플릿 적용

**작업 항목:**
- [ ] Skywork 템플릿 스키마 정의
  - `templates_doc.json`: 문서 템플릿
  - `templates_ppt.json`: PPT 템플릿
  - `templates_excel.json`: Excel 템플릿

- [ ] Skywork API 템플릿 파라미터 조사
  - Skywork API 문서 확인
  - 템플릿 파라미터 매핑 (예: `format`, `layout`)

- [ ] 프록시 함수 확장
  - `gen_doc()`: `template_id` 파라미터 추가
  - `gen_ppt()`, `gen_ppt_fast()`: `template_id` 파라미터 추가
  - `gen_excel()`: `template_id` 파라미터 추가

- [ ] 템플릿 파라미터 변환 로직
  - `TemplateMetadata.parameters` → Skywork API 요청 포맷

**완료 기준:**
- 문서/PPT/Excel 생성에 템플릿이 적용됨
- Skywork API가 템플릿을 지원하지 않을 경우 대안 마련됨

**의존성:** Phase 3 완료, Skywork API 확인

---

### Phase 5: 선택적 기능 (Optional Goal)

**목표:** 사용자 정의 템플릿 및 고급 기능

**작업 항목:**
- [ ] 사용자 정의 템플릿 생성
  - `create_custom_template()` MCP 도구
  - `templates_custom.json` 저장소
  - 사용자 템플릿 유효성 검증

- [ ] 템플릿 즐겨찾기
  - `add_template_favorite()`, `remove_template_favorite()` 도구
  - 즐겨찾기 저장소 (사용자별)

- [ ] 템플릿 내보내기/가져오기
  - `export_template()`, `import_template()` 도구
  - JSON/YAML 포맷 지원

- [ ] 템플릿 미리보기 개선
  - 썸네일 생성 (이미지 템플릿)
  - 샘플 파일 생성 (문서/PPT/Excel 템플릿)

**완료 기준:**
- 사용자가 자신만의 템플릿을 생성하고 적용할 수 있음
- 즐겨찾기 필터링이 동작함
- 템플릿을 내보내고 가져올 수 있음

**의존성:** Phase 4 완료

---

## 3. 기술 접근 (Technical Approach)

### 3.1 데이터 모델 설계

**공통 메타데이터 스키마:**
```python
@dataclass
class TemplateMetadata:
    template_id: str              # 고유 ID (예: "tpl-corp-memphis")
    name: str                     # 표시 이름
    content_type: ContentType     # IMAGE, DOCUMENT, PRESENTATION, SPREADSHEET
    description: str              # 설명
    keywords: List[str]           # 검색용 키워드
    parameters: Dict[str, Any]    # API에 전달할 파라미터
    category: Optional[str]       # 카테고리 (예: "Business", "Creative")
    tags: List[str]               # 추가 태그
    is_custom: bool               # 사용자 정의 여부
    is_active: bool               # 활성화 상태
```

**파라미터 매핑:**
- **이미지**: `style_keywords` (기존 `banana_styles.json` 호환)
- **문서**: `format`, `include_toc`, `include_headers`
- **PPT**: `layout`, `theme`, `slide_count`
- **Excel**: `sheet_format`, `include_charts`

### 3.2 리포지토리 패턴

**TemplateRepository 책임:**
- 템플릿 파일 로딩 및 파싱
- 템플릿 CRUD 작업
- 필터링 및 검색

**TemplateRegistry 책임:**
- 전역 템플릿 인스턴스 관리 (싱글톤)
- 캐싱 계층 추상화
- 기본 템플릿 해결

### 3.3 캐싱 전략

**LRU 캐시 설정:**
- 최대 크기: 100개 템플릿
- TTL: 1시간 (사용자 정의 템플릿의 경우 5분)
- 캐시 키: `template:{content_type}:{template_id}`

**캐시 무효화:**
- 사용자 정의 템플릿 생성/수정/삭제 시
- 템플릿 파일 변경 감지 (mtime 모니터링)

### 3.4 하위 호환성 유지

**이중 파라미터 지원:**
```python
def generate_image(
    prompt: str,
    style_name: Optional[str] = None,  # 기존 파라미터
    template_id: Optional[str] = None  # 새 파라미터
) -> str:
    # template_id 우선, 없으면 style_name 사용
    if template_id:
        template = registry.get_template(template_id)
        return apply_template(template, prompt)
    elif style_name:
        # 기존 로직 (STYLES 딕셔너리)
        return legacy_apply_style(style_name, prompt)
    else:
        # 기본 템플릿
        return apply_default_template(ContentType.IMAGE, prompt)
```

---

## 4. 위험 관리 (Risk Management)

### 4.1 기술적 위험

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|-----------|
| Skywork API가 템플릿을 지원하지 않음 | Medium | High | 템플릿 파라미터를 프롬프트에 주입하는 대안 구현 |
| 기존 스타일과의 호환성 문제 | Low | Medium | 포괄적인 회귀 테스트 및 이중 파라미터 지원 |
| 템플릿 파일 크기 증가에 따른 로딩 지연 | Low | Low | 지연 로딩 및 인덱싱 최적화 |

### 4.2 사용자 경험 위험

| 위험 | 완화 전략 |
|------|-----------|
| 사용자가 새로운 템플릿 시스템을 혼동함 | 기존 `style_name` 파라미터 계속 지원 및 문서화 |
| 템플릿 선택이 복잡함 | `list_templates`에 필터링 및 정렬 기능 제공 |
| 미리보기 없는 템플릿의 UX 저하 | 플레이스홀더와 상세한 메타데이터 제공 |

---

## 5. 마일스톤 (Milestones)

### Milestone 1: 핵심 데이터 모델 완료
- **완료 기준:** Phase 1, Phase 2 완료
- **산출물:**
  - `TemplateRepository`, `TemplateRegistry` 구현
  - 기존 스타일 마이그레이션 완료
  - 단위 테스트 통과

### Milestone 2: MCP 도구 통합
- **완료 기준:** Phase 3 완료
- **산출물:**
  - `list_templates`, `get_template_details`, `apply_template` 도구
  - `generate_image` 템플릿 지원
  - 통합 테스트 통과

### Milestone 3: 다중 콘텐츠 유형 지원
- **완료 기준:** Phase 4 완료
- **산출물:**
  - 문서/PPT/Excel 템플릿 정의
  - Skywork 프록시 함수 확장
  - 모든 콘텐츠 유형에 템플릿 적용 가능

### Milestone 4: 선택적 기능 (Optional)
- **완료 기준:** Phase 5 완료
- **산출물:**
  - 사용자 정의 템플릿 기능
  - 즐겨찾기, 내보내기/가져오기

---

## 6. 테스트 전략 (Testing Strategy)

### 6.1 단위 테스트 (Unit Tests)

- **TemplateRepository**: CRUD 메서드, 필터링, 검색
- **TemplateRegistry**: 로딩, 캐싱, 기본 템플릿 해결
- **Validators**: 스키마 검증, 호환성 검증

### 6.2 통합 테스트 (Integration Tests)

- **MCP 도구**: `list_templates`, `apply_template` 호출 테스트
- **이미지 생성**: 템플릿 적용된 이미지 생성 확인
- **Skywork API**: 템플릿 파라미터가 정상적으로 전달되는지 확인

### 6.3 회귀 테스트 (Regression Tests)

- **하위 호환성**: `style_name` 파라미터가 여전히 동작하는지 확인
- **기존 스타일**: 모든 15종 Nano Banana 스타일이 변환되어 동작하는지 확인

---

## 7. 롤아웃 계획 (Rollout Plan)

### 7.1 개발 단계
- Phase 1-3: 이미지 템플릿만 지원 (기존 기능 마이그레이션)
- Phase 4: 문서/PPT/Excel 템플릿 추가
- Phase 5: 선택적 기능 구현

### 7.2 배포 단계
- **Beta**: 템플릿 시스템 도입, 하위 호환성 유지
- **Stable**: Skywork 통합 완료 후 안정화
- **Enhanced**: 사용자 정의 템플릿 기능 추가

---

**버전**: 1.0.0
**최종 수정**: 2025-01-19
**다음 검토**: Milestone 1 완료 후
