# SPEC-TEMPLATE-001: 통합 템플릿 갤러리 시스템

## TAG BLOCK

```yaml
spec:
  id: SPEC-TEMPLATE-001
  title: 통합 템플릿 갤러리 시스템 (Template Gallery System Core)
  status: Planned
  priority: HIGH
  created: 2025-01-19
  assigned: workflow-spec
  lifecycle: spec-anchored
  version: 1.0.0

dependencies:
  - SPEC-GALLERY-001  # 갤러리 인프라 재사용
  - SPEC-CACHE-001   # 템플릿 미리보기 캐싱
  - SPEC-IMG-004     # 고급 이미지 생성 확장
  - SPEC-SKYWORK-001 # Skywork 통합 템플릿 파라미터

domains:
  - backend
  - data-model
  - api

labels:
  - template-system
  - gallery
  - content-generation
  - unified-repository
```

---

## 1. 개요 (Overview)

### 1.1 목적 (Purpose)

Smart Visual Toolkit MCP 서버의 모든 콘텐츠 생성 기능(이미지, 문서, PPT, Excel)에 대해 통합된 템플릿 관리 시스템을 제공합니다. 현재 이미지 생성에서는 `banana_styles.json`으로 스타일 템플릿을 관리하고 있으나, 문서/PPT/Excel 생성에는 템플릿 시스템이 없습니다. 이를 통합하여 일관된 템플릿 관리와 재사용성을 제공합니다.

### 1.2 배경 (Background)

**현재 상황:**
- 이미지 생성: 15종의 Nano Banana 스타일 템플릿 (`banana_styles.json`)
- 문서/PPT/Excel 생성: 템플릿 시스템 없음 (Skywork API 직접 호출)
- 각 콘텐츠 유형별로 템플릿 구조가 다름

**문제점:**
- 템플릿 관리의 중복과 비효율성
- 사용자 경험의 불일치
- 템플릿 재사용 및 공유 어려움
- 새로운 템플릿 추가의 번거로움

### 1.3 목표 (Goals)

1. **통합된 템플릿 저장소**: 모든 콘텐츠 유형(Image, Doc, PPT, Excel)에 대한 단일 템플릿 관리 시스템
2. **일관된 메타데이터 구조**: 모든 템플릿 유형에 대해 동일한 메타데이터 스키마 적용
3. **호환성 검증**: 템플릿과 콘텐츠 유형 간의 호환성 자동 검증
4. **미리보기 지원**: 템플릿 미리보기 이미지/샘플 제공
5. **사용자 정의 템플릿**: 사용자가 직접 템플릿 생성 및 공유 가능 (선택사항)

---

## 2. 환경 및 가정 (Environment & Assumptions)

### 2.1 기술 환경 (Technical Environment)

- **언어**: Python 3.10+
- **프레임워크**: FastMCP (Model Context Protocol SDK)
- **데이터 포맷**: JSON (템플릿 저장), YAML (사용자 정의 템플릿)
- **캐싱**: 기존 LRU+TTL 캐싱 시스템 재사용 (SPEC-CACHE-001)

### 2.2 통합 지점 (Integration Points)

- **이미지 생성**: `generate_image()`, `generate_image_advanced()` 함수
- **문서 생성**: `gen_doc()` 프록시 함수
- **PPT 생성**: `gen_ppt()`, `gen_ppt_fast()` 프록시 함수
- **Excel 생성**: `gen_excel()` 프록시 함수
- **갤러리 시스템**: `ImageGallery` 클래스 확장 (SPEC-GALLERY-001)

### 2.3 가정사항 (Assumptions)

| 가정 | 신뢰도 | 근거 | 위험 |
|------|--------|------|------|
| Skywork API가 템플릿 파라미터를 지원함 | Medium | Skywork 문서 확인 필요 | API가 템플릿을 지원하지 않을 경우 대안 필요 |
| 사용자는 JSON 형식으로 템플릿 정의 가능 | High | 기존 `banana_styles.json` 사용 중 | 복잡한 템플릿의 경우 UI 도구 필요 |
| 템플릿 미리보기는 선택사항 | High | 모든 템플릿에 미리보기 필요 없음 | 미리보기 없는 템플릿의 UX 저하 |
| 기존 갤러리 인프라 확장 가능 | High | SPEC-GALLERY-001 구조 확인됨 | 복잡한 리팩토링 필요할 수 있음 |

---

## 3. 요구사항 (Requirements)

### 3.1 Ubiquitous Requirements (항상 활성 요구사항)

시스템은 **항상** 다음 동작을 수행해야 합니다:

- **REQ-T-001**: 시스템은 이미지, 문서, PPT, Excel 생성을 위한 통합 템플릿 저장소를 유지해야 한다.
- **REQ-T-002**: 시스템은 모든 콘텐츠 유형에 대해 일관된 템플릿 메타데이터 구조를 제공해야 한다.
- **REQ-T-003**: 시스템은 템플릿 적용 전 대상 콘텐츠 유형과의 호환성을 검증해야 한다.
- **REQ-T-004**: 시스템은 템플릿 사용 로그를 기록하여 분석에 활용 가능해야 한다.

### 3.2 Event-Driven Requirements (이벤트-응답 요구사항)

**WHEN** 이벤트가 발생하면 **THEN** 시스템은 다음 동작을 수행해야 합니다:

- **REQ-T-101**: **WHEN** 사용자가 콘텐츠 생성을 요청하면, **THEN** 시스템은 해당 콘텐츠 유형에 적용 가능한 템플릿 목록과 미리보기 썸네일을 표시해야 한다.
- **REQ-T-102**: **WHEN** 사용자가 템플릿을 선택하면, **THEN** 시스템은 템플릿 파라미터를 생성 API에 적용해야 한다.
- **REQ-T-103**: **WHEN** 템플릿이 적용되면, **THEN** 시스템은 템플릿 사용 횟수를 업데이트하고 로그를 기록해야 한다.
- **REQ-T-104**: **WHEN** 템플릿 목록 조회 요청이 있으면, **THEN** 시스템은 콘텐츠 유형별 필터링된 목록을 반환해야 한다.

### 3.3 State-Driven Requirements (조건부 동작 요구사항)

**IF** 조건이 참이면 **THEN** 시스템은 다음 동작을 수행해야 합니다:

- **REQ-T-201**: **IF** 템플릿이 선택되지 않으면, **THEN** 시스템은 해당 콘텐츠 유형의 기본 템플릿을 적용해야 한다.
- **REQ-T-202**: **IF** 템플릿 미리보기를 사용할 수 없으면, **THEN** 시스템은 템플릿 메타데이터와 함께 플레이스홀더를 표시해야 한다.
- **REQ-T-203**: **IF** 템플릿이 콘텐츠 유형과 호환되지 않으면, **THEN** 시스템은 선택을 비활성화하고 사유를 표시해야 한다.
- **REQ-T-204**: **IF** 템플릿 로딩에 실패하면, **THEN** 시스템은 오류 메시지를 표시하고 기본 템플릿으로 대체해야 한다.

### 3.4 Unwanted Behavior Requirements (금지 동작 요구사항)

시스템은 **다음 동작을 수행해서는 안 됩니다**:

- **REQ-T-301**: 시스템은 호환되지 않는 콘텐츠 유형에 템플릿을 강제 적용해서는 안 된다.
- **REQ-T-302**: 시스템은 유효하지 않은 템플릿 구조를 허용해서는 안 된다.
- **REQ-T-303**: 시스템은 사용자 동의 없이 기본 템플릿을 자동 변경해서는 안 된다.
- **REQ-T-304**: 시스템은 템플릿 적용 실패 시 전체 생성 작업을 중단해서는 안 된다 (대신 기본 템플릿로 대체).

### 3.5 Optional Requirements (선택적 기능 요구사항)

**가능하면** 시스템은 다음 기능을 제공해야 합니다:

- **REQ-T-401**: **WHERE 가능하면**, 시스템은 템플릿 즐겨찾기 기능을 제공해야 한다.
- **REQ-T-402**: **WHERE 가능하면**, 시스템은 사용자 정의 템플릿 생성 기능을 지원해야 한다.
- **REQ-T-403**: **WHERE 가능하면**, 시스템은 템플릿 내보내기/가져오기를 통한 공유를 지원해야 한다.
- **REQ-T-404**: **WHERE 가능하면**, 시스템은 템플릿 카테고리/태그 관리를 제공해야 한다.

---

## 4. 상세 사양 (Specifications)

### 4.1 데이터 모델 (Data Models)

#### 4.1.1 통합 템플릿 스키마

```python
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

class ContentType(Enum):
    """지원되는 콘텐츠 유형"""
    IMAGE = "image"
    DOCUMENT = "document"  # Word
    PRESENTATION = "presentation"  # PPT
    SPREADSHEET = "spreadsheet"  # Excel

@dataclass
class TemplateMetadata:
    """템플릿 메타데이터 (모든 콘텐츠 유형 공통)"""
    template_id: str                    # 고유 ID
    name: str                           # 템플릿 이름
    content_type: ContentType           # 적용 가능한 콘텐츠 유형
    description: str                    # 템플릿 설명
    keywords: List[str]                 # 검색/필터링용 키워드
    parameters: Dict[str, Any]          # 생성 API에 전달할 파라미터
    preview_url: Optional[str] = None   # 미리보기 이미지/샘플 URL
    thumbnail_path: Optional[str] = None  # 로컬 썸네일 경로
    category: Optional[str] = None      # 카테고리
    tags: List[str] = None              # 추가 태그
    usage_count: int = 0                # 사용 횟수
    created_at: datetime = None         # 생성일
    updated_at: datetime = None         # 수정일
    is_custom: bool = False             # 사용자 정의 템플릿 여부
    is_active: bool = True              # 활성화 상태
```

#### 4.1.2 템플릿 저장소 구조

```json
{
  "version": "1.0",
  "templates": [
    {
      "template_id": "tpl-corp-memphis",
      "name": "Corporate Memphis",
      "content_type": "image",
      "description": "Modern tech company style, clean and friendly",
      "keywords": ["Corporate Memphis", "3D Render", "Confetti"],
      "parameters": {
        "style_keywords": "Corporate Memphis, 3D Render, Confetti"
      },
      "preview_url": null,
      "category": "Business",
      "tags": ["modern", "3d", "friendly"],
      "is_custom": false
    },
    {
      "template_id": "tpl-doc-report",
      "name": "Professional Report",
      "content_type": "document",
      "description": "Standard business report format",
      "keywords": ["report", "business", "professional"],
      "parameters": {
        "format": "standard_report",
        "include_toc": true,
        "include_headers": true
      },
      "preview_url": null,
      "category": "Business",
      "tags": ["report", "standard"],
      "is_custom": false
    }
  ],
  "defaults": {
    "image": "tpl-corp-memphis",
    "document": "tpl-doc-report",
    "presentation": "tpl-ppt-business",
    "spreadsheet": "tpl-excel-basic"
  }
}
```

### 4.2 API 설계 (API Design)

#### 4.2.1 MCP 도구 (MCP Tools)

```python
@mcp.tool()
def list_templates(
    content_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    템플릿 목록을 조회합니다.

    Args:
        content_type: 필터링할 콘텐츠 유형 (image/document/presentation/spreadsheet)
        category: 필터링할 카테고리
        limit: 최대 반환 개수
    """

@mcp.tool()
def get_template_details(template_id: str) -> str:
    """
    특정 템플릿의 상세 정보를 조회합니다.
    """

@mcp.tool()
def apply_template(
    template_id: str,
    content_type: str,
    prompt: str,
    **kwargs
) -> str:
    """
    템플릿을 적용하여 콘텐츠를 생성합니다.
    """

@mcp.tool()
def create_custom_template(
    name: str,
    content_type: str,
    parameters: Dict[str, Any],
    description: str = "",
    category: str = "Custom"
) -> str:
    """
    사용자 정의 템플릿을 생성합니다 (선택사항).
    """
```

#### 4.2.2 기존 API 확장

```python
# 기존 함수에 template_id 파라미터 추가
@mcp.tool()
def generate_image(
    prompt: str,
    style_name: Optional[str] = None,
    template_id: Optional[str] = None  # 새로운 파라미터
) -> str:
    """
    템플릿 ID가 제공되면 템플릿 파라미터를 우선 적용합니다.
    style_name은 하위 호환성을 위해 유지합니다.
    """

# Skywork 프록시 함수도 template_id 지원
@mcp.tool()
async def gen_doc(
    query: str,
    use_network: str = "true",
    template_id: Optional[str] = None  # 새로운 파라미터
) -> str:
    """
    템플릿이 제공되면 문서 형식을 템플릿에 맞춥니다.
    """
```

### 4.3 파일 구조 (File Structure)

```
src/
├── templates/
│   ├── __init__.py
│   ├── models.py              # TemplateMetadata, ContentType 등
│   ├── repository.py          # TemplateRepository 클래스
│   ├── registry.py            # TemplateRegistry (템플릿 로드 및 관리)
│   └── validators.py          # 템플릿 유효성 검증
├── resources/
│   ├── templates_image.json   # 이미지 템플릿 (기존 banana_styles.json 마이그레이션)
│   ├── templates_doc.json     # 문서 템플릿
│   ├── templates_ppt.json     # PPT 템플릿
│   ├── templates_excel.json   # Excel 템플릿
│   └── templates_custom.json  # 사용자 정의 템플릿 (선택사항)
└── main.py                    # 템플릿 MCP 도구 등록
```

### 4.4 캐싱 전략 (Caching Strategy)

- **템플릿 메타데이터 캐싱**: LRU 캐시 (최대 100개 템플릿)
- **미리보기 썸네일 캐싱**: 기존 갤러리 시스템 재사용 (SPEC-GALLERY-001)
- **TTL**: 1시간 (사용자 정의 템플릿의 경우 즉시 반영)

---

## 5. 의존성 및 통합 (Dependencies & Integration)

### 5.1 의존 SPEC (Dependent SPECs)

| SPEC ID | 관계 | 설명 |
|---------|------|------|
| SPEC-GALLERY-001 | Reuse | 갤러리 인프라를 템플릿 관리에 재사용 |
| SPEC-CACHE-001 | Extend | 캐싱 시스템을 템플릿 미리보기에 확장 |
| SPEC-IMG-004 | Extend | 고급 이미지 생성에 템플릿 파라미터 추가 |
| SPEC-SKYWORK-001 | Integrate | Skywork API 호출에 템플릿 파라미터 전달 |

### 5.2 외부 의존성 (External Dependencies)

- **Skywork API**: 템플릿 파라미터 지원 여부 확인 필요
- **Google Imagen API**: 이미지 생성에 템플릿 스타일 적용

---

## 6. 품질 요구사항 (Quality Requirements)

### 6.1 성능 (Performance)

- 템플릿 목록 조회: < 100ms
- 템플릿 적용: < 50ms (파라미터 변환만, 생성 시간 제외)
- 템플릿 로딩: 시작 시 < 1초

### 6.2 보안 (Security)

- 사용자 정의 템플릿의 파라미터 검증 (인젝션 방지)
- 템플릿 파일 접근 권한 제어
- 민감 정보가 템플릿에 포함되지 않도록 검증

### 6.3 호환성 (Compatibility)

- 기존 `style_name` 파라미터와의 하위 호환성 유지
- 템플릿 ID가 없는 경우 기존 동작 유지

---

## 7. 추적 가능성 (Traceability)

### 7.1 요구사항-설계 매핑

| 요구사항 | 설계 요소 | 테스트 시나리오 |
|----------|-----------|----------------|
| REQ-T-001 | TemplateRepository, TemplateRegistry | TC-T-001: 모든 콘텐츠 유형 템플릿 로드 |
| REQ-T-002 | TemplateMetadata 공통 스키마 | TC-T-002: 메타데이터 구조 일관성 |
| REQ-T-003 | validate_compatibility() | TC-T-003: 호환되지 않는 템플릿 거부 |
| REQ-T-101 | list_templates() | TC-T-101: 필터링된 템플릿 목록 반환 |
| REQ-T-102 | apply_template() | TC-T-102: 템플릿 파라미터 적용 |
| REQ-T-201 | get_default_template() | TC-T-201: 기본 템플릿 적용 |
| REQ-T-401 | [선택사항] favorites 기능 | TC-T-401: 즐겨찾기 추가/제거 |

### 7.2 구현 작업 추적

- **Phase 1**: 데이터 모델 및 리포지토리 구현
- **Phase 2**: 기존 이미지 템플릿 마이그레이션
- **Phase 3**: MCP 도구 구현
- **Phase 4**: Skywork API 통합 (문서/PPT/Excel)
- **Phase 5**: [선택사항] 사용자 정의 템플릿 기능

---

## 8. 부록 (Appendix)

### 8.1 기존 banana_styles.json 마이그레이션 계획

```python
# 마이그레이션 스크립트 예시
def migrate_banana_styles():
    """기존 스타일을 새 템플릿 형식으로 변환"""
    with open("src/resources/banana_styles.json") as f:
        data = json.load(f)

    templates = []
    for style in data["styles"]:
        template = {
            "template_id": f"tpl-{style['name'].lower().replace(' ', '-')}",
            "name": style["name"],
            "content_type": "image",
            "description": style["description"],
            "keywords": style["keywords"].split(", "),
            "parameters": {
                "style_keywords": style["keywords"]
            },
            "category": "Style",
            "is_custom": False
        }
        templates.append(template)

    return {"version": "1.0", "templates": templates}
```

### 8.2 용어 정의

| 용어 | 정의 |
|------|------|
| 템플릿 (Template) | 콘텐츠 생성에 적용되는 미리 정의된 파라미터 집합 |
| 콘텐츠 유형 (Content Type) | 생성할 콘텐츠의 종류 (Image, Document, Presentation, Spreadsheet) |
| 호환성 (Compatibility) | 템플릿이 특정 콘텐츠 유형에 적용 가능한지 여부 |
| 기본 템플릿 (Default Template) | 템플릿이 선택되지 않았을 때 자동으로 적용되는 템플릿 |
| 사용자 정의 템플릿 (Custom Template) | 사용자가 직접 생성한 템플릿 |

---

**버전**: 1.0.0
**최종 수정**: 2025-01-19
**다음 검토**: 구현 완료 후
