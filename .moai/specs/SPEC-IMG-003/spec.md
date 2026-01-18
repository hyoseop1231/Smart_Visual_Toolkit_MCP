---
SPEC_ID: SPEC-IMG-003
TITLE: 확장된 Aspect Ratio 지원
STATUS: Planned
PRIORITY: MEDIUM
AUTHOR: Hyoseop
CREATED: 2025-01-18
ASSIGNED: TBD
RELATED_SPECS: []
EPIC: 이미지 생성 기능 향상
LIFECYCLE_LEVEL: spec-first
TAGS: [aspect-ratio, image-generation, ui-enhancement]
---

# SPEC-IMG-003: 확장된 Aspect Ratio 지원

## HISTORY

| 버전 | 날짜 | 변경 사항 | 작성자 |
|-------|------|-----------|--------|
| 1.0.0 | 2025-01-18 | 초기 SPEC 작성 | Hyoseop |

## 요약 (Summary)

이미지 생성 시 초와이드(21:9), 포트레이트/SNS(2:3), 사진/DSLR 표준(3:2), 대형 포맷(5:4) 등 새로운 aspect ratio를 지원하는 기능을 추가합니다. 기존 비율(1:1, 16:9, 9:16, 4:3, 3:4)은 유지됩니다.

## 환경 (Environment)

### 시스템 환경
- **프로젝트**: Smart Visual Toolkit MCP
- **플랫폼**: MCP Server (Python)
- **타겟 사용자**: 이미지 생성 도구를 사용하는 클라이언트 애플리케이션

### 기술 환경
- **언어**: Python 3.13+
- **프레임워크**: FastAPI 기반 MCP 서버
- **이미지 생성**: Skywork API 통합
- **UI 상태 관리**: React 기반 클라이언트 (필요시)

## 가정 (Assumptions)

### 기술적 가정
1. Skywork API가 추가 aspect ratio를 지원한다고 가정
2. 현재 이미지 생성 파이프라인이 aspect ratio 파라미터를 처리할 수 있다고 가정
3. 클라이언트 UI가 선택적 aspect ratio 옵션을 표시할 수 있다고 가정

### 비즈니스 가정
1. 사용자가 다양한 디스플레이 및 플랫폼에 최적화된 이미지를 원한다고 가정
2. 초와이드 모니터 사용자가 21:9 비율을 필요로 한다고 가정
3. SNS 및 모바일 사용자가 2:3 및 3:2 비율을 필요로 한다고 가정

### 검증 방법
- Skywork API 문서 확인으로 새 비율 지원 검증
- 기존 코드베이스 분석으로 aspect ratio 처리 방식 확인
- 사용자 피드백으로 필요한 비율 우선순위 확인

## 요구사항 (Requirements)

### EARS 형식 요구사항

#### 1. Ubiquitous Requirements (항상 활성화)

**REQ-IMG-003-001**: 시스템은 모든 이미지 생성 요청에서 aspect ratio 파라미터의 유효성을 검사해야 한다.

**REQ-IMG-003-002**: 시스템은 지원되는 모든 aspect ratio에 대해 일관된 이미지 품질을 보장해야 한다.

**REQ-IMG-003-003**: 시스템은 aspect ratio 변경 시 기존 기능에 영향을 주지 않아야 한다.

#### 2. Event-Driven Requirements (이벤트 기반)

**REQ-IMG-003-004**: WHEN 사용자가 이미지 생성 요청 시 21:9 비율을 선택하면, 시스템은 초와이드 디스플레이에 최적화된 이미지를 생성해야 한다.

**REQ-IMG-003-005**: WHEN 사용자가 이미지 생성 요청 시 2:3 비율을 선택하면, 시스템은 포트레이트/SNS 플랫폼에 최적화된 이미지를 생성해야 한다.

**REQ-IMG-003-006**: WHEN 사용자가 이미지 생성 요청 시 3:2 비율을 선택하면, 시스템은 DSLR 표준 포맷에 최적화된 이미지를 생성해야 한다.

**REQ-IMG-003-007**: WHEN 사용자가 이미지 생성 요청 시 5:4 비율을 선택하면, 시스템은 대형 포맷 인쇄에 최적화된 이미지를 생성해야 한다.

**REQ-IMG-003-008**: WHEN 사용자가 지원되지 않는 aspect ratio를 요청하면, 시스템은 명확한 에러 메시지를 표시하고 사용 가능한 비율 목록을 제공해야 한다.

#### 3. State-Driven Requirements (상태 기반)

**REQ-IMG-003-009**: IF 기존 aspect ratio가 선택된 상태에서 새로운 비율이 추가되면, 시스템은 기존 선택을 유지하고 새 옵션을 추가해야 한다.

**REQ-IMG-003-010**: IF 이미지 생성이 진행 중인 상태에서 aspect ratio가 변경되면, 시스템은 진행 중인 생성을 취소하고 새 비율로 재시작해야 한다.

#### 4. Unwanted Requirements (금지 동작)

**REQ-IMG-003-011**: 시스템은 aspect ratio 파라미터 누락 시 기본값(16:9)을 자동으로 적용해서는 안 된다. 명시적인 사용자 선택을 요구해야 한다.

**REQ-IMG-003-012**: 시스템은 새로운 aspect ratio 추가로 인해 기존 비율(1:1, 16:9, 9:16, 4:3, 3:4)의 기능을 저하해서는 안 된다.

#### 5. Optional Requirements (선택적 기능)

**REQ-IMG-003-013**: WHERE 가능하면, 시스템은 사용자가 자주 사용하는 aspect ratio를 즐겨찾기로 저장할 수 있는 기능을 제공해야 한다.

**REQ-IMG-003-014**: WHERE 가능하면, 시스템은 aspect ratio 미리보기 기능을 제공하여 선택 전 이미지 비율을 시각화해야 한다.

## 상세 설명 (Specifications)

### SPEC-IMG-003-S001: Aspect Ratio 정의

| Ratio | 이름 | 사용 사례 | 해상도 예시 |
|-------|------|-----------|------------|
| 1:1 | Square | Instagram, 일반 | 1024x1024 |
| 16:9 | Landscape | YouTube, 일반 | 1920x1080 |
| 9:16 | Portrait | Mobile, TikTok | 1080x1920 |
| 4:3 | Standard | 전통적 디스플레이 | 1440x1080 |
| 3:4 | Portrait Standard | 전통적 포트레이트 | 1080x1440 |
| **21:9** | **Ultra-Wide** | **초와이드 모니터** | **2560x1080** |
| **2:3** | **Portrait SNS** | **Instagram, Pinterest** | **1080x1620** |
| **3:2** | **Photo DSLR** | **DSLR 표준** | **1620x1080** |
| **5:4** | **Large Format** | **대형 포맷 인쇄** | **1350x1080** |

### SPEC-IMG-003-S002: API 인터페이스

**MCP Tool 업데이트**:
```typescript
interface GenerateImageParams {
  prompt: string;
  aspect_ratio: "1:1" | "16:9" | "9:16" | "4:3" | "3:4" | "21:9" | "2:3" | "3:2" | "5:4";
  // ... other parameters
}
```

**Skywork API 매핑**:
```python
ASPECT_RATIO_MAP = {
    "1:1": ("1024", "1024"),
    "16:9": ("1920", "1080"),
    "9:16": ("1080", "1920"),
    "4:3": ("1440", "1080"),
    "3:4": ("1080", "1440"),
    "21:9": ("2560", "1080"),  # New
    "2:3": ("1080", "1620"),   # New
    "3:2": ("1620", "1080"),   # New
    "5:4": ("1350", "1080"),   # New
}
```

### SPEC-IMG-003-S003: UI/UX 변경사항

**Aspect Ratio 선택기**:
- 새로운 비율 옵션 4개 추가 (21:9, 2:3, 3:2, 5:4)
- 각 비율에 대한 시각적 미리보기 제공
- 비율별 사용 사례 표시 (Tooltip 혹은 라벨)

**카테고리별 그룹화**:
- Standard: 1:1, 16:9, 9:16, 4:3, 3:4
- Ultra-Wide: 21:9
- Photography: 3:2, 2:3
- Print: 5:4

### SPEC-IMG-003-S004: 데이터 모델

**Aspect Ratio Config**:
```python
@dataclass
class AspectRatioConfig:
    ratio_id: str
    width: int
    height: int
    name: str
    category: str
    use_cases: List[str]
    is_new: bool = False
```

## 제약사항 (Constraints)

### 기술적 제약사항
1. Skywork API가 지원하는 최대/최소 해상도 준수
2. 이미지 생성 시간이 새로운 비율로 인해 과도하게 증가하지 않아야 함
3. 기존 API 호환성 유지

### 비즈니스 제약사항
1. 새로운 비율 추가로 인한 비용 증가 최소화
2. 사용자 경험 저하 방지

### 호환성 제약사항
1. 기존 클라이언트와의 호환성 유지
2. 백엔드 API 변경 시 하위 호환성 보장

## 추적 가능성 (Traceability)

### TAG 맵핑
- **태그**: `aspect-ratio`, `image-generation`, `ui-enhancement`
- **관련 코드**: 이미지 생성 MCP tool, Skywork API wrapper, UI aspect ratio selector

### 구현 가이드
- `/moai:2-run SPEC-IMG-003`로 구현 시작
- `code-expert` 에이전트에게 Skywork API 비율 지원 확인 위임
- `expert-frontend` 에이전트에게 UI component 업데이트 위임

## 참고 자료 (References)

- Skywork API Documentation (aspect ratio 지원 범위)
- 기존 이미지 생성 코드베이스
- SPEC-SKYWORK-001: Skywork API 품질 개선
