# SPEC-TEMPLATE-002: 템플릿 갤러리 UI 기능

## TAG BLOCK

```yaml
SPEC_ID: SPEC-TEMPLATE-002
Title: 템플릿 갤러리 UI 기능 (Template Gallery UI Features)
Created: 2026-01-19
Status: Planned
Priority: MEDIUM
Assigned: TBD
Related_SPECs:
  - SPEC-TEMPLATE-001 (핵심 템플릿 시스템)
Lifecycle: spec-first
```

## 환경 (Environment)

### 시스템 컨텍스트

- **프로젝트**: Smart Visual Toolkit MCP Server
- **대상 플랫폼**: MCP 클라이언트 (Claude Desktop, VS Code, Cline)
- **사용자**: MCP 서버를 통해 시각적 도구를 사용하는 개발자 및 디자이너
- **데이터 저장소**: 로컬 파일 시스템 (JSON)
- **언어**: Python 3.13+, TypeScript 5.9+

### 기술 제약사항

- **프레임워크**: FastAPI 0.115+ (백엔드), React 19+ (프론트엔드)
- **데이터 검증**: Pydantic v2.9+
- **테스팅**: pytest, async 테스트 지원
- **아키텍처**: 이벤트 기반 MCP 통신

## 가정사항 (Assumptions)

### 기술적 가정

1. **신뢰도**: 높음 - 사용자는 MCP 서버와 안정적으로 연결됨
2. **데이터 지속성**: 높음 - 사용자 선호도는 세션 간 유지됨
3. **메트릭 수집**: 중간 - 템플릿 사용 횟수는 정확하게 추적됨

### 비즈니스 가정

1. **사용자 행동**: 인기 템플릿은 더 자주 사용됨
2. **콘텐츠 갱신**: 새 템플릿은 주기적으로 추가됨
3. **사용자 참여**: 즐겨찾기 기능은 재사용성을 높임

### 검증 방법

- 사용자 선호도 저장 실패 시 로컬 폴백 메커니즘 적용
- 메트릭 수집 오류 시 기본 정렬 방식으로 대체

## 요구사항 (Requirements)

### 이벤트 기반 요구사항 (Event-Driven)

#### REQ-TEMPLATE-001: 인기도 배지 표시
**When** 템플릿 목록을 표시할 때, **the system shall** 사용 메트릭을 기반으로 배지(Popular, New, Recommended)를 표시해야 한다.

- **트리거**: 템플릿 갤러리 로드 또는 갱신
- **응답**: 각 템플릿 카드에 관련 배지 표시
- **우선순위**: HIGH
- **추적가능성**: UI 컴포넌트, 메트릭 계산 로직

#### REQ-TEMPLATE-002: 즐겨찾기 토글
**When** 사용자가 즐겨찾기 버튼을 클릭할 때, **the system shall** 템플릿 즐겨찾기 상태를 토글해야 한다.

- **트리거**: 즐겨찾기 버튼 클릭 이벤트
- **응답**: 상태 토글 및 지속성 저장소 업데이트
- **우선순위**: HIGH
- **추적가능성**: 사용자 선호도 매니저, UI 상태

#### REQ-TEMPLATE-003: 템플릿 공유
**When** 사용자가 템플릿을 공유할 때, **the system shall** 공유 가능한 URL 또는 템플릿 설정을 내보내야 한다.

- **트리거**: 공유 버튼 클릭
- **응답**: 공유 링크 생성 또는 설정 내보내기
- **우선순위**: MEDIUM
- **추적가능성**: 공유 유틸리티, 내보내기 핸들러

### 상태 기반 요구사항 (State-Driven)

#### REQ-TEMPLATE-004: 인기 템플릿 식별
**If** 템플릿이 상위 10% 사용량에 속하면, **then the system shall** "Popular" 배지를 표시해야 한다.

- **조건**: `usage_count >= 전체 사용량의 90번째 백분위수`
- **동작**: Popular 배지 렌더링
- **우선순위**: HIGH
- **추적가능성**: 메트릭 분석기, 배지 렌더러

#### REQ-TEMPLATE-005: 신규 템플릿 식별
**If** 템플릿이 7일 이내에 생성되었으면, **then the system shall** "New" 배지를 표시해야 한다.

- **조건**: `created_at >= 현재 날짜 - 7일`
- **동작**: New 배지 렌더링
- **우선순위**: MEDIUM
- **추적가능성**: 날짜 비교 로직, 배지 렌더러

#### REQ-TEMPLATE-006: 즐겨찾기 상태 표시
**If** 사용자가 템플릿을 즐겨찾기로 표시했으면, **then the system shall** 채워진 즐겨찾기 아이콘을 표시해야 한다.

- **조건**: `template_id in user_favorites`
- **동작**: 채워진 하트 아이콘 렌더링
- **우선순위**: HIGH
- **추적가능성**: 사용자 선호도 저장소, UI 상태 매니저

### 보편적 요구사항 (Ubiquitous)

#### REQ-TEMPLATE-007: 사용량 추적
The system **shall** 순위 계산을 위해 템플릿 사용 빈도를 추적해야 한다.

- **동작**: 각 템플릿 사용 시 `usage_count` 증가
- **데이터 저장**: 템플릿 메타데이터에 지속적 저장
- **우선순위**: HIGH
- **추적가능성**: 메트릭 수집기, 템플릿 저장소

#### REQ-TEMPLATE-008: 선호도 지속성
The system **shall** 세션 간 사용자 즐겨찾기 선호도를 유지해야 한다.

- **동작**: 사용자 선호도를 `output/user_preferences.json`에 저장
- **로드**: 애플리케이션 시작 시 선호도 로드
- **우선순위**: HIGH
- **추적가능성**: 사용자 선호도 매니저, 파일 시스템 핸들러

## 기술 사양 (Technical Specifications)

### 데이터 모델

#### 템플릿 메타데이터 확장

```python
class TemplateMetadata(BaseModel):
    """기존 템플릿 메타데이터 확장"""
    id: str
    name: str
    description: str
    category: str

    # 추가 필드
    usage_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 사용자 선호도 저장소

```python
class UserPreferences(BaseModel):
    """사용자 선호도 모델"""
    favorite_templates: list[str] = Field(default_factory=list)
    recently_used: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

### 배지 계산 로직

```python
def calculate_template_badges(
    template: TemplateMetadata,
    all_templates: list[TemplateMetadata]
) -> list[str]:
    """
    템플릿 배지를 동적으로 계산

    Args:
        template: 배지를 계산할 템플릿
        all_templates: 모든 템플릿 목록 (백분위수 계산용)

    Returns:
        배지 태그 리스트 ("Popular", "New", "Recommended")
    """
    badges = []

    # Popular 배지: 상위 10% 사용량
    usage_percentile = calculate_percentile(
        template.usage_count,
        [t.usage_count for t in all_templates]
    )
    if usage_percentile >= 90:
        badges.append("Popular")

    # New 배지: 7일 이내 생성
    if (datetime.utcnow() - template.created_at).days <= 7:
        badges.append("New")

    # Recommended 배지: 높은 사용량 + 최근 업데이트
    if usage_percentile >= 70 and (datetime.utcnow() - template.updated_at).days <= 30:
        badges.append("Recommended")

    return badges
```

### UI 컴포넌트 사양

#### 템플릿 카드 구조

```typescript
interface TemplateCardProps {
  template: TemplateMetadata;
  badges: string[];
  isFavorite: boolean;
  onFavoriteToggle: (id: string) => void;
  onShare: (id: string) => void;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  badges,
  isFavorite,
  onFavoriteToggle,
  onShare
}) => {
  return (
    <div className="template-card">
      {/* 배지 영역 */}
      <div className="badges">
        {badges.map(badge => (
          <Badge key={badge} variant={badge}>
            {badge}
          </Badge>
        ))}
      </div>

      {/* 템플릿 정보 */}
      <h3>{template.name}</h3>
      <p>{template.description}</p>

      {/* 액션 버튼 */}
      <div className="actions">
        <button
          onClick={() => onFavoriteToggle(template.id)}
          aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
        >
          {isFavorite ? "❤️" : "🤍"}
        </button>
        <button
          onClick={() => onShare(template.id)}
          aria-label="Share template"
        >
          🔗
        </button>
      </div>
    </div>
  );
};
```

### API 엔드포인트

#### 템플릿 목록 조회 (배지 포함)

```python
@router.get("/templates", response_model=list[TemplateWithBadges])
async def list_templates(
    sort_by: str = "name",
    favorites_only: bool = False
) -> list[TemplateWithBadges]:
    """
    배지 정보가 포함된 템플릿 목록 반환

    Query Parameters:
        sort_by: 정렬 기준 (name, usage, created)
        favorites_only: 즐겨찾기만 표시
    """
    templates = await template_service.get_all()
    user_prefs = await user_preferences_service.load()

    result = []
    for template in templates:
        badges = calculate_template_badges(template, templates)
        is_favorite = template.id in user_prefs.favorite_templates

        if favorites_only and not is_favorite:
            continue

        result.append(TemplateWithBadges(
            **template.model_dump(),
            badges=badges,
            is_favorite=is_favorite
        ))

    return sort_templates(result, sort_by)
```

#### 즐겨찾기 토글

```python
@router.post("/templates/{template_id}/favorite")
async def toggle_favorite(
    template_id: str,
    user_prefs: UserPreferences = Depends(get_user_preferences)
) -> UserPreferences:
    """
    템플릿 즐겨찾기 상태 토글
    """
    if template_id in user_prefs.favorite_templates:
        user_prefs.favorite_templates.remove(template_id)
    else:
        user_prefs.favorite_templates.append(template_id)

    user_prefs.last_updated = datetime.utcnow()
    await user_preferences_service.save(user_prefs)

    return user_prefs
```

#### 템플릿 공유

```python
@router.post("/templates/{template_id}/share")
async def share_template(
    template_id: str,
    format: str = "url"
) -> ShareResponse:
    """
    템플릿 공유 링크 또는 설정 내보내기

    Query Parameters:
        format: 공유 형식 (url, json, yaml)
    """
    template = await template_service.get_by_id(template_id)

    if format == "url":
        share_url = generate_share_url(template)
        return ShareResponse(type="url", content=share_url)
    elif format == "json":
        return ShareResponse(type="json", content=template.model_dump_json())
    elif format == "yaml":
        return ShareResponse(type="yaml", content=to_yaml(template))
```

### 스토리지 구조

#### 템플릿 메타데이터 (`templates/metadata.json`)

```json
{
  "templates": [
    {
      "id": "chart-line-001",
      "name": "Line Chart Template",
      "description": "Basic line chart visualization",
      "category": "chart",
      "usage_count": 127,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-18T14:30:00Z"
    }
  ]
}
```

#### 사용자 선호도 (`output/user_preferences.json`)

```json
{
  "favorite_templates": [
    "chart-line-001",
    "table-basic-003"
  ],
  "recently_used": [
    "chart-bar-002",
    "chart-pie-005"
  ],
  "last_updated": "2026-01-19T09:15:00Z"
}
```

## 제약사항 (Constraints)

### 성능 요구사항

- 배지 계산은 100ms 이내에 완료되어야 함
- 템플릿 목록 로드는 500ms 이내에 완료되어야 함
- 즐겨찾기 토글은 50ms 이내에 응답해야 함

### 보안 요구사항

- 사용자 선호도 파일은 사용자 홈 디렉토리에만 저장되어야 함
- 공유 URL은 만료 기간을 가져야 함 (옵션)

### 호환성 요구사항

- Python 3.13+ 호환
- React 19+ 호환
- MCP 프로토콜 준수

## 추적성 (Traceability)

### 요구사항-구성요소 매핑

| 요구사항 | 컴포넌트 | 파일 경로 |
|---------|---------|----------|
| REQ-TEMPLATE-001 | TemplateCard, BadgeCalculator | frontend/components/TemplateCard.tsx |
| REQ-TEMPLATE-002 | FavoriteManager | backend/services/favorites.py |
| REQ-TEMPLATE-003 | ShareUtility | backend/services/share.py |
| REQ-TEMPLATE-004 | BadgeCalculator | backend/services/badges.py |
| REQ-TEMPLATE-005 | BadgeCalculator | backend/services/badges.py |
| REQ-TEMPLATE-006 | UserPreferencesStore | backend/services/preferences.py |
| REQ-TEMPLATE-007 | MetricsCollector | backend/services/metrics.py |
| REQ-TEMPLATE-008 | UserPreferencesStore | backend/services/preferences.py |

### 테스트 커버리지 매핑

- `test_badge_calculation.py`: REQ-TEMPLATE-001, REQ-TEMPLATE-004, REQ-TEMPLATE-005
- `test_favorite_toggle.py`: REQ-TEMPLATE-002, REQ-TEMPLATE-006
- `test_share_functionality.py`: REQ-TEMPLATE-003
- `test_metrics_tracking.py`: REQ-TEMPLATE-007
- `test_preferences_persistence.py`: REQ-TEMPLATE-008

## 의존성 (Dependencies)

### 선행 SPEC

- **SPEC-TEMPLATE-001**: 핵심 템플릿 시스템 (필수)
  - 템플릿 메타데이터 구조 제공
  - 기본 템플릿 저장소 구현

### 관련 SPEC

- 없음 (최초 UI 기능)

## 참조 (References)

- EARS Methodology: Alistair Mavin (2009)
- MCP Protocol Specification
- React 19 Documentation
- FastAPI 0.115 Documentation
