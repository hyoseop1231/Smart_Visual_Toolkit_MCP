# SPEC-TEMPLATE-003: API 템플릿 통합 확장

## 메타데이터

| 항목 | 값 |
|------|-----|
| SPEC ID | SPEC-TEMPLATE-003 |
| 제목 | API 템플릿 통합 확장 (Template API Integration Extension) |
| 버전 | 1.0.0 |
| 상태 | Planned |
| 우선순위 | MEDIUM |
| 작성일 | 2026-01-19 |
| 작성자 | Alfred (Orchestrator) |
| 라이프사이클 | spec-anchored |

---

## 1. 개요

### 1.1 목적

API 템플릿 통합 확장은 기존 이미지 생성 및 문서 생성 기능에 템플릿 시스템을 통합하여 재사용 가능한 스타일과 레이아웃 패턴을 제공합니다.

### 1.2 범위

**포함:**
- 템플릿 스타일 키워드를 Nano Banana 스타일로 매핑
- 템플릿 레이아웃 파라미터를 Skywork API 형식으로 변환
- 사용자 정의 스타일 키워드와 템플릿 스타일 병합
- API 스키마 기반 파라미터 검증
- 기존 호출과의 하위 호환성 유지

**제외:**
- 템플릿 저장소 UI/UX 디자인
- 템플릿 버전 관리
- 템플릿 마켓플레이스

### 1.3 배경

현재 시스템은 이미지 생성 시 15개의 Nano Banana 스타일을 지원하며, 문서 생성 시 Skywork API를 사용합니다. 템플릿 시스템을 도입하여 이러한 스타일과 레이아웃을 재사용 가능한 형태로 제공함으로써 사용자 경험을 개선하고 생성 결과의 일관성을 높일 수 있습니다.

---

## 2. 환경 및 가정

### 2.1 환경

- **Python**: 3.10+
- **기존 API**: Google Imagen 4.0-fast, Skywork API
- **MCP Server**: Model Context Protocol SDK

### 2.2 가정

- **ASSUMPTION-001**: 템플릿 시스템은 SPEC-TEMPLATE-001 (코어 템플릿 시스템)이 먼저 구현되어야 함 (신뢰도: LOW, 근거: SPEC-TEMPLATE-001이 존재하지 않음)
- **ASSUMPTION-002**: Google Imagen API는 스타일 키워드 기반 생성을 지원함 (신뢰도: HIGH, 근거: SPEC-NANOBANANA-001에서 이미 구현됨)
- **ASSUMPTION-003**: Skywork API는 레이아웃 파라미터를 통한 문서 생성을 지원함 (신뢰도: MEDIUM, 근거: API 문서 검증 필요)
- **ASSUMPTION-004**: 사용자는 템플릿을 JSON 형식으로 정의할 수 있음 (신뢰도: HIGH, 근거: 일반적인 템플릿 형식)

### 2.3 의존성

| 의존 SPEC | 설명 | 상태 |
|----------|------|------|
| SPEC-TEMPLATE-001 | 코어 템플릿 시스템 | 존재하지 않음 (선제적 구현 필요) |
| SPEC-NANOBANANA-001 | Nano Banana 스타일 통합 | 완료됨 |
| SPEC-SKYWORK-001 | Skywork API 통합 | 완료됨 |
| SPEC-CACHE-001 | 이미지 캐시 시스템 | 완료됨 |

---

## 3. 요구사항 (EARS 형식)

### 3.1 템플릿 스타일 매핑

#### REQ-TMPL-001: 이미지 생성 템플릿 매핑
**[Event-driven]** 사용자가 템플릿을 지정하여 이미지 생성을 요청하면, 시스템은 템플릿 스타일 키워드를 Nano Banana 스타일로 매핑하여 Google Imagen API에 전달해야 한다.

**검증 기준:**
- 템플릿 ID로 스타일 키워드 조회
- Nano Banana 스타일 존재 여부 검증
- 매핑된 키워드를 프롬프트에 통합

#### REQ-TMPL-002: 스타일 키워드 병합
**[State-driven]** 템플릿에 사용자 정의 스타일 키워드가 정의된 경우, 시스템은 사용자가 제공한 스타일 키워드와 병합하여 우선순위를 적용해야 한다.

**검증 기준:**
- 사용자 키워드 우선순위 높음
- 템플릿 키워드를 기본값으로 사용
- 중복 키워드 제거

#### REQ-TMPL-003: 스타일 매핑 테이블
**[Ubiquitous]** 시스템은 모든 템플릿 스타일 키워드와 Nano Banana 스타일 간의 매핑 테이블을 유지해야 한다.

**검증 기준:**
- 15개 Nano Banana 스타일 모두 매핑
- JSON 형식으로 저장
- 런타임에 로드 가능

### 3.2 레이아웃 파라미터 변환

#### REQ-TMPL-004: 문서 생성 레이아웃 파라미터
**[Event-driven]** 사용자가 템플릿을 지정하여 Word/Excel/PowerPoint 생성을 요청하면, 시스템은 템플릿 레이아웃 파라미터를 Skywork API 형식으로 변환하여 전달해야 한다.

**검증 기준:**
- Word: 섹션, 스타일, 형식 파라미터
- Excel: 열, 행, 셀 스타일 파라미터
- PowerPoint: 슬라이드 레이아웃, 테마 파라미터

#### REQ-TMPL-005: 레이아웃 제약조건 검증
**[State-driven]** 템플릿이 레이아웃 제약조건을 정의하는 경우, 시스템은 생성 요청 전에 API 제한과의 호환성을 검증해야 한다.

**검증 기준:**
- 최대 페이지/슬라이드 수 확인
- 지원되는 스타일 검증
- 제약조건 위반 시 명확한 에러 메시지

#### REQ-TMPL-006: 파라미터 변환 규칙
**[Ubiquitous]** 시스템은 내부 템플릿 형식에서 API 특정 형식으로의 파라미터 변환 규칙을 일관되게 적용해야 한다.

**검증 기준:**
- camelCase ↔ snake_case 변환
- 데이터 타입 변환 (문자열 ↔ 숫자)
- 중첩 구조 평탄화

### 3.3 하위 호환성

#### REQ-TMPL-007: 템플릿 없는 호출 지원
**[Ubiquitous]** 시스템은 템플릿 파라미터 없는 기존 호출을 완벽하게 지원해야 한다.

**검증 기준:**
- 템플릿 파라미터 선택적 (optional)
- 기존 테스트 통과
- 동일한 출력 결과

#### REQ-TMPL-008: API 스키마 검증
**[Ubiquitous]** 시스템은 API 제출 전에 모든 템플릿 파라미터를 API 스키마에 대해 검증해야 한다.

**검증 기준:**
- 파라미터 이름 존재 확인
- 데이터 타입 일치 확인
- 필수 파라미터 누락 확인

### 3.4 비기능 요구사항

#### REQ-TMPL-009: 성능
**[Ubiquitous]** 템플릿 적용에 따른 오버헤드는 100ms 이내여야 한다.

**검증 기준:**
- 템플릿 로드: < 10ms
- 파라미터 변환: < 50ms
- 검증: < 40ms

#### REQ-TMPL-010: 오류 처리
**[Event-driven]** 템플릿 로드 또는 파라미터 변환 실패 시, 시스템은 명확한 에러 메시지와 함께 기본 동작으로 대체해야 한다.

**검증 기준:**
- 에러 메시지에 실패 원인 포함
- 기본 스타일/레이아웃으로 대체
- 로그에 상세 정보 기록

---

## 4. 기술 사양

### 4.1 템플릿 데이터 구조

```python
Template = {
    "id": str,                    # 템플릿 고유 ID
    "name": str,                  # 템플릿 이름
    "description": str,           # 템플릿 설명
    "type": "image" | "doc" | "excel" | "ppt",
    "style_keywords": List[str],  # 이미지 생성용 스타일 키워드
    "layout_params": {            # 문서 생성용 레이아웃 파라미터
        "page_count": int,
        "columns": int,
        "theme": str,
        # 문서 타입별 추가 파라미터
    },
    "constraints": {              # 제약조건
        "max_pages": Optional[int],
        "supported_formats": List[str],
    }
}
```

### 4.2 Nano Banana 스타일 매핑 테이블

```python
STYLE_MAPPING = {
    "corporate": ["Corporate Memphis", "3D Render", "Confetti"],
    "flat": ["Flat illustration", "Corporate", "Memphis"],
    "isometric": ["Infographic", "Isometric", "Colorful"],
    "minimal": ["Minimal", "Monochrome", "Line Art"],
    "doodle": ["Doodle", "Notebook", "Blue Ink"],
    "clay": ["Clay", "Stopmotion", "Cute"],
    "watercolor": ["Watercolor", "Map", "Fantasy"],
    "pixel": ["Pixel Art", "Retro Game", "8-bit"],
    "glass": ["Glassmorphism", "Dark", "Blur"],
    "cyberpunk": ["Cyberpunk", "Blue", "Circuit"],
    "synthwave": ["Synthwave", "Sunset", "Retro Grid"],
    "paper": ["Paper Cutout", "Layered", "Shadow"],
    "ukiyo": ["Ukiyo-e", "City Pop", "Halftone"],
    "lowpoly": ["Low Poly", "3D", "Geometric"],
    "fluid": ["Abstract", "Fluid", "Gradient"],
}
```

### 4.3 Skywork 레이아웃 파라미터 구조

```python
SKYWORK_LAYOUT_PARAMS = {
    "word": {
        "sections": int,
        "page_layout": str,  # "standard", "wide", "portrait"
        "style": str,
    },
    "excel": {
        "rows": int,
        "columns": int,
        "header_style": str,
        "cell_format": str,
    },
    "ppt": {
        "slide_count": int,
        "layout": str,  # "title", "content", "two_column"
        "theme": str,
    }
}
```

### 4.4 파라미터 변환 규칙

| 내부 형식 | Skywork API 형식 | 변환 규칙 |
|----------|-----------------|-----------|
| `pageCount` | `page_count` | camelCase → snake_case |
| `columns` | `columns` | 그대로 사용 |
| `theme` | `theme_name` | 접두사 추가 |
| `layout` | `slide_layout` | 이름 변환 |

---

## 5. 추적성 (Traceability)

### 5.1 요구사항-기능 매핑

| 요구사항 | 구현 컴포넌트 | 테스트 시나리오 |
|---------|--------------|---------------|
| REQ-TMPL-001 | TemplateMapper | TC-TMPL-001 |
| REQ-TMPL-002 | StyleMerger | TC-TMPL-002 |
| REQ-TMPL-003 | StyleMappingTable | TC-TMPL-003 |
| REQ-TMPL-004 | LayoutTransformer | TC-TMPL-004 |
| REQ-TMPL-005 | ConstraintValidator | TC-TMPL-005 |
| REQ-TMPL-006 | ParameterConverter | TC-TMPL-006 |
| REQ-TMPL-007 | BackwardCompatLayer | TC-TMPL-007 |
| REQ-TMPL-008 | SchemaValidator | TC-TMPL-008 |
| REQ-TMPL-009 | PerformanceMonitor | TC-TMPL-009 |
| REQ-TMPL-010 | ErrorHandler | TC-TMPL-010 |

### 5.2 태그 블록

```
TAG: SPEC-TEMPLATE-003
TAG: TEMPLATE-INTEGRATION
TAG: STYLE-MAPPING
TAG: LAYOUT-PARAMETERS
TAG: API-TRANSFORMATION
TAG: BACKWARD-COMPATIBILITY
```

---

## 6. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-19 | 초안 작성 | Alfred |

---

## 7. 승인

| 역할 | 이름 | 날짜 | 상태 |
|------|------|------|------|
| 작성자 | Alfred | 2026-01-19 | ✅ |
| 검토자 | Hyoseop | - | ⏳ |
| 승인자 | - | - | ⏳ |
