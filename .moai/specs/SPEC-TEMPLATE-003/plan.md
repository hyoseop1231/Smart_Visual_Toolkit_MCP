# SPEC-TEMPLATE-003: 구현 계획

## 메타데이터

| 항목 | 값 |
|------|-----|
| SPEC ID | SPEC-TEMPLATE-003 |
| 문서 유형 | Implementation Plan |
| 버전 | 1.0.0 |
| 작성일 | 2026-01-19 |
| 작성자 | Alfred (Orchestrator) |

---

## 1. 구현 개요

### 1.1 목표

API 템플릿 통합 확장 기능을 구현하여 재사용 가능한 스타일과 레이아웃 패턴을 제공합니다.

### 1.2 기술 접근법

- **계층형 아키텍처**: 템플릿 시스템을 기존 이미지/문서 생성 계층 위에 통합
- **매핑 패턴**: 내부 템플릿 형식 → API 특정 형식 변환 계층 도입
- **검증 계층**: 파라미터 검증을 통한 API 오류 방지

### 1.3 의존성 분석

```text
SPEC-TEMPLATE-003 (본 SPEC)
    │
    ├─→ SPEC-TEMPLATE-001 (코어 템플릿 시스템) [존재하지 않음]
    │      └─→ 선제적 구현 필요
    │
    ├─→ SPEC-NANOBANANA-001 (이미지 생성) [완료됨]
    │      └─→ 스타일 매핑 확장
    │
    └─→ SPEC-SKYWORK-001 (문서 생성) [완료됨]
           └─→ 레이아웃 파라미터 추가
```

---

## 2. 마일스톤

### Phase 1: 기반 구조 (Primary Goal)

**목표**: 템플릿 시스템 기반 구축

**작업 항목:**
- [ ] 템플릿 데이터 모델 정의
- [ ] 스타일 매핑 테이블 생성
- [ ] 파라미터 변환 규칙 정의
- [ ] 기본 템플릿 3개 예제 작성

**완료 기준:**
- 템플릿 JSON 스키마 정의 완료
- 15개 Nano Banana 스타일 매핑 완료
- 단위 테스트 통과

---

### Phase 2: 이미지 생성 통합 (Primary Goal)

**목표**: 이미지 생성 도구에 템플릿 기능 통합

**작업 항목:**
- [ ] `TemplateMapper` 클래스 구현
- [ ] `StyleMerger` 클래스 구현
- [ ] `generate_image` 도구에 템플릿 파라미터 추가
- [ ] 스타일 병합 로직 구현
- [ ] 템플릿 캐싱 최적화

**완료 기준:**
- 템플릿 지정 이미지 생성 성공
- 사용자 스타일 병합 기능 동작
- 기존 기능 하위 호환성 유지

---

### Phase 3: 문서 생성 통합 (Primary Goal)

**목표**: 문서 생성 도구에 레이아웃 템플릿 기능 통합

**작업 항목:**
- [ ] `LayoutTransformer` 클래스 구현
- [ ] `ConstraintValidator` 클래스 구현
- [ ] Word/Excel/PPT 도구에 레이아웃 파라미터 추가
- [ ] Skywork API 형식으로 파라미터 변환
- [ ] 제약조건 검증 로직 구현

**완료 기준:**
- 템플릿 지정 문서 생성 성공
- 레이아웃 파라미터 정확히 전달
- API 제한 사항 검증 동작

---

### Phase 4: 파라미터 변환 및 검증 (Secondary Goal)

**목표**: API 파라미터 변환 계층 구현

**작업 항목:**
- [ ] `ParameterConverter` 클래스 구현
- [ ] `SchemaValidator` 클래스 구현
- [ ] camelCase ↔ snake_case 변환기
- [ ] 데이터 타입 변환기
- [ ] API 스키마 검증 로직

**완료 기준:**
- 모든 파라미터 형식 올바르게 변환
- API 스키마 검증 100% 통과
- 잘못된 파라미터 사전 차단

---

### Phase 5: 하위 호환성 및 오류 처리 (Secondary Goal)

**목표**: 기존 기능과의 호환성 보장

**작업 항목:**
- [ ] 템플릿 파라미터를 선택적(optional)으로 설정
- [ ] `ErrorHandler` 클래스 구현
- [ ] 기본 동작 대체 로직
- [ ] 명확한 에러 메시지 정의
- [ ] 기존 테스트 통과 확인

**완료 기준:**
- 템플릿 없는 호출 100% 동작
- 에러 발생 시 기본 동작으로 대체
- 모든 기존 테스트 통과

---

### Phase 6: 테스트 및 문서화 (Final Goal)

**목표**: 품질 보증 및 사용자 문서 제공

**작업 항목:**
- [ ] 단위 테스트 작성 (커버리지 85%+)
- [ ] 통합 테스트 작성
- [ ] 성능 벤치마킹
- [ ] 사용자 문서 작성
- [ ] 예제 템플릿 제공

**완료 기준:**
- 테스트 커버리지 85% 이상
- 모든 인수 테스트 통과
- 사용자 가이드 완성

---

## 3. 기술 아키텍처

### 3.1 컴포넌트 구조

```text
src/
├── templates/                    # 템플릿 시스템
│   ├── __init__.py
│   ├── models.py                 # 템플릿 데이터 모델
│   ├── mapper.py                 # TemplateMapper
│   ├── transformer.py            # LayoutTransformer, ParameterConverter
│   ├── validator.py              # ConstraintValidator, SchemaValidator
│   ├── merger.py                 # StyleMerger
│   ├── resources/
│   │   ├── style_mapping.json    # 스타일 매핑 테이블
│   │   └── templates/            # 템플릿 저장소
│   │       ├── image/
│   │       │   ├── corporate.json
│   │       │   ├── minimal.json
│   │       │   └── ...
│   │       ├── doc/
│   │       │   ├── report.json
│   │       │   └── ...
│   │       ├── excel/
│   │       │   └── ...
│   │       └── ppt/
│   │           └── ...
│   └── cache.py                  # 템플릿 캐시
│
├── generators/
│   ├── image_gen.py              # 템플릿 통합 수정
│   └── ...
│
├── skywork/
│   └── client.py                 # 레이아웃 파라미터 추가
│
└── main.py                       # MCP 도구에 템플릿 파라미터 추가
```

### 3.2 데이터 흐름

```text
[사용자 요청]
      │
      ▼
[MCP 도구 호출: template 파라미터 포함]
      │
      ├─→ [TemplateMapper] ──→ 템플릿 로드
      │         │
      │         ▼
      │   [StyleMappingTable]
      │
      ├─→ [StyleMerger] ──→ 스타일 병합
      │         │
      │         ▼
      │   병합된 스타일 키워드
      │
      ├─→ [LayoutTransformer] ──→ 레이아웃 변환
      │         │
      │         ▼
      │   변환된 레이아웃 파라미터
      │
      ├─→ [ParameterConverter] ──→ 포맷 변환
      │         │
      │         ▼
      │   API 특정 포맷
      │
      ├─→ [ConstraintValidator] ──→ 제약 검증
      │         │
      │         ▼
      │   검증 결과
      │
      └─→ [SchemaValidator] ──→ 스키마 검증
                │
                ▼
          [API 호출]
```

### 3.3 클래스 설계

#### TemplateMapper

```python
class TemplateMapper:
    """템플릿 ID로 템플릿을 로드하고 매핑합니다."""

    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self._cache = {}

    def load_template(self, template_id: str) -> Template:
        """템플릿 ID로 템플릿을 로드합니다."""

    def get_style_keywords(self, template_id: str) -> List[str]:
        """템플릿의 스타일 키워드를 반환합니다."""

    def get_layout_params(self, template_id: str) -> Dict:
        """템플릿의 레이아웃 파라미터를 반환합니다."""
```

#### StyleMerger

```python
class StyleMerger:
    """사용자 스타일과 템플릿 스타일을 병합합니다."""

    def merge_styles(
        self,
        template_keywords: List[str],
        user_keywords: List[str]
    ) -> List[str]:
        """사용자 키워드(우선)과 템플릿 키워드를 병합합니다."""

    def deduplicate(self, keywords: List[str]) -> List[str]:
        """중복 키워드를 제거합니다."""
```

#### LayoutTransformer

```python
class LayoutTransformer:
    """내부 레이아웃 파라미터를 Skywork API 형식으로 변환합니다."""

    def transform_for_word(self, layout: Dict) -> Dict:
        """Word용 레이아웃 파라미터 변환"""

    def transform_for_excel(self, layout: Dict) -> Dict:
        """Excel용 레이아웃 파라미터 변환"""

    def transform_for_ppt(self, layout: Dict) -> Dict:
        """PPT용 레이아웃 파라미터 변환"""
```

#### ConstraintValidator

```python
class ConstraintValidator:
    """템플릿 제약조건을 검증합니다."""

    def validate_page_count(self, count: int, max_pages: int) -> bool:
        """페이지 수가 제한을 초과하는지 검증"""

    def validate_format(self, format: str, supported: List[str]) -> bool:
        """지원되는 형식인지 검증"""

    def validate_constraints(self, template: Template, params: Dict) -> ValidationResult:
        """모든 제약조건 검증"""
```

#### ParameterConverter

```python
class ParameterConverter:
    """파라미터 형식을 변환합니다."""

    def camel_to_snake(self, s: str) -> str:
        """camelCase를 snake_case로 변환"""

    def snake_to_camel(self, s: str) -> str:
        """snake_case를 camelCase로 변환"""

    def convert_type(self, value: Any, target_type: str) -> Any:
        """데이터 타입 변환"""

    def convert_params(self, params: Dict, format: "internal" | "api") -> Dict:
        """파라미터 형식 변환"""
```

---

## 4. 리스크 및 대응 계획

### 4.1 리스크 매트릭스

| 리스크 | 확률 | 영향 | 점수 | 완화 전략 |
|--------|------|------|------|-----------|
| SPEC-TEMPLATE-001 미존재로 인한 의존성 누락 | HIGH | HIGH | 9 | 코어 템플릿 기능을 본 SPEC에 통합하여 구현 |
| Skywork API 레이아웃 파라미터 미지원 | MEDIUM | HIGH | 6 | API 문서 확인 후 지원 범위 조정 |
| 스타일 매핑 복잡도 증가 | LOW | MEDIUM | 3 | 매핑 테이블 JSON으로 관리하여 단순화 |
| 하위 호환성 파기 | LOW | HIGH | 4 | 포괄적인 회귀 테스트로 방지 |
| 성능 저하 | MEDIUM | MEDIUM | 4 | 템플릿 캐싱으로 완화 |

### 4.2 대응 계획

**리스크 1: SPEC-TEMPLATE-001 미존재**
- **대응**: Phase 1에서 코어 템플릿 기능을 직접 구현
- **계획**: 템플릿 로딩, 캐싱, 기본 검증 기능 포함

**리스크 2: Skywork API 레이아웃 파라미터**
- **대응**: Phase 3 시작 전 API 문서 검증
- **계획**: 지원하지 않는 경우 문서 템플릿 기능만 구현

**리스크 3: 하위 호환성**
- **대응**: Phase 5에서 포괄적인 회귀 테스트
- **계획**: 모든 기존 테스트가 통과할 때까지 Phase 진행 중지

---

## 5. 테스트 전략

### 5.1 단위 테스트

| 컴포넌트 | 테스트 파일 | 커버리지 목표 |
|---------|------------|--------------|
| TemplateMapper | tests/templates/test_mapper.py | 90% |
| StyleMerger | tests/templates/test_merger.py | 90% |
| LayoutTransformer | tests/templates/test_transformer.py | 90% |
| ConstraintValidator | tests/templates/test_validator.py | 90% |
| ParameterConverter | tests/templates/test_converter.py | 90% |

### 5.2 통합 테스트

| 시나리오 | 테스트 파일 | 검증 항목 |
|---------|------------|----------|
| 템플릿 이미지 생성 | tests/integration/test_template_image.py | 스타일 매핑, 병합 |
| 템플릿 Word 생성 | tests/integration/test_template_word.py | 레이아웃 파라미터 |
| 템플릿 Excel 생성 | tests/integration/test_template_excel.py | 레이아웃 파라미터 |
| 템플릿 PPT 생성 | tests/integration/test_template_ppt.py | 레이아웃 파라미터 |
| 하위 호환성 | tests/integration/test_backward_compat.py | 기존 기능 동작 |

### 5.3 성능 테스트

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| 템플릿 로드 | < 10ms | Benchmark |
| 파라미터 변환 | < 50ms | Benchmark |
| 전체 처리 | < 100ms | End-to-end |

---

## 6. 성공 기준

### 6.1 기능적 기준

- [ ] 템플릿 지정 이미지 생성 100% 성공
- [ ] 템플릿 지정 문서 생성 100% 성공
- [ ] 스타일 병합 기능 정확히 동작
- [ ] 레이아웃 파라미터 정확히 전달
- [ ] 제약조건 검증 동작
- [ ] 하위 호환성 100% 유지

### 6.2 품질 기준

- [ ] 단위 테스트 커버리지 85% 이상
- [ ] 모든 인수 테스트 통과
- [ ] 린터 오류 0개
- [ ] 성능 목표 달성 (< 100ms)
- [ ] 보안 취약점 0개

### 6.3 문서 기준

- [ ] API 문서 완성
- [ ] 사용자 가이드 완성
- [ ] 예제 템플릿 3개 이상 제공
- [ ] README.md 업데이트

---

## 7. 다음 단계

### 7.1 구현 시작

```bash
# 구현 시작
/moai:2-run SPEC-TEMPLATE-003
```

### 7.2 전문가 상담 권장

**Backend 구현 필요 시:**
- [HARD] code-backend 전문가 상담 권장
- WHY: API 파라미터 변환, 데이터 모델링 복잡
- IMPACT: 아키텍처 결정에 전문 지식 필요

**문의 항목:**
- 템플릿 데이터 모델 최적 설계
- 파라미터 변환 패턴 모범 사례
- 캐싱 전략 최적화
- API 검증 계층 설계

---

## 8. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-19 | 초안 작성 | Alfred |

---

## 추적성 태그

```
TAG: SPEC-TEMPLATE-003
TAG: IMPLEMENTATION-PLAN
TAG: MILESTONES
TAG: ARCHITECTURE
TAG: RISK-MANAGEMENT
TAG: TESTING-STRATEGY
```
