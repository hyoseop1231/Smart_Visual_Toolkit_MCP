# SPEC-IMG-003: 확장된 Aspect Ratio 지원 - 구현 계획

## 개요 (Overview)

이 문서는 SPEC-IMG-003의 구현 계획, 기술적 접근 방식, 그리고 마일스톤을 설명합니다.

## 구현 마일스톤 (Implementation Milestones)

### 1차 목표: 핵심 기능 구현 (Priority High)

**목적**: 새로운 aspect ratio를 시스템에 통합하고 기본 기능을 구현합니다.

- **백엔드 통합**: Skywork API에 새 비율(21:9, 2:3, 3:2, 5:4) 추가
- **데이터 모델 업데이트**: AspectRatioConfig 클래스 확장
- **API 유효성 검사**: 새 비율 파라미터 검증 로직 추가
- **테스트 커버리지**: 최소 85% 커버리지 달성

### 2차 목표: UI/UX 개선 (Priority Medium)

**목적**: 사용자가 새로운 비율을 쉽게 선택하고 이해할 수 있도록 UI를 개선합니다.

- **UI 컴포넌트 업데이트**: Aspect ratio 선택기에 새 옵션 추가
- **시각적 미리보기**: 각 비율에 대한 미리보기 표시
- **카테고리별 그룹화**: Standard, Ultra-Wide, Photography, Print 카테고리 구현
- **사용 사례 표시**: 각 비율의 사용 사례를 Tooltip이나 라벨로 표시

### 3차 목표: 최종 목표: 고급 기능 (Priority Low)

**목적**: 사용자 경험을 향상시키는 추가 기능을 구현합니다.

- **즐겨찾기 기능**: 자주 사용하는 비율 저장
- **미리보기 최적화**: 선택 전 이미지 비율 시각화 개선
- **성능 최적화**: 이미지 생성 시간 최적화

### 4차 목표: 문서화 및 동기화 (Optional)

**목적**: 변경 사항을 문서화하고 사용자에게 안내합니다.

- API 문서 업데이트
- 사용자 가이드 업데이트
- CHANGELOG 엔트리 작성

## 기술적 접근 방식 (Technical Approach)

### 1단계: Skywork API 지원 확인

**활동**:
1. Skywork API 문서 확인으로 새 비율 지원 여부 검증
2. 지원하지 않는 경우, 대안 방안 탐색 (이미지 크롭, 리사이징)
3. API 제한 사항 문서화

**검증 방법**:
- Skywork API 문서 리뷰
- 테스트 이미지 생성으로 비율 지원 확인

### 2단계: 백엔드 구현

**파일 구조**:
```
src/
├── server/
│   ├── handlers/
│   │   └── image_generation.py      # 이미지 생성 핸들러
│   ├── models/
│   │   └── aspect_ratio.py          # Aspect Ratio 데이터 모델
│   └── utils/
│       └── skywork_api.py           # Skywork API 래퍼
```

**구현 세부사항**:

**2.1 데이터 모델 정의**:
```python
# src/server/models/aspect_ratio.py
from dataclasses import dataclass
from typing import List

@dataclass
class AspectRatioConfig:
    ratio_id: str
    width: int
    height: int
    name: str
    category: str
    use_cases: List[str]
    is_new: bool = False

# Aspect Ratio 레지스트리
ASPECT_RATIOS = {
    "1:1": AspectRatioConfig("1:1", 1024, 1024, "Square", "Standard", ["Instagram", "General"]),
    "16:9": AspectRatioConfig("16:9", 1920, 1080, "Landscape", "Standard", ["YouTube", "General"]),
    # ... 기존 비율
    "21:9": AspectRatioConfig("21:9", 2560, 1080, "Ultra-Wide", "Ultra-Wide", ["Ultra-wide monitors"], is_new=True),
    "2:3": AspectRatioConfig("2:3", 1080, 1620, "Portrait SNS", "Photography", ["Instagram", "Pinterest"], is_new=True),
    "3:2": AspectRatioConfig("3:2", 1620, 1080, "Photo DSLR", "Photography", ["DSLR Standard"], is_new=True),
    "5:4": AspectRatioConfig("5:4", 1350, 1080, "Large Format", "Print", ["Large format prints"], is_new=True),
}
```

**2.2 Skywork API 매핑 업데이트**:
```python
# src/server/utils/skywork_api.py
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

def get_resolution_for_ratio(aspect_ratio: str) -> tuple[str, str]:
    """aspect ratio에 해당하는 해상도를 반환합니다."""
    if aspect_ratio not in ASPECT_RATIO_MAP:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    return ASPECT_RATIO_MAP[aspect_ratio]
```

**2.3 MCP Tool 업데이트**:
```python
# src/server/handlers/image_generation.py
from .models.aspect_ratio import ASPECT_RATIOS

SUPPORTED_ASPECT_RATIOS = list(ASPECT_RATIOS.keys())

@mcp_tool()
def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    # ... other parameters
) -> dict:
    """
    이미지를 생성합니다.

    Args:
        prompt: 이미지 생성 프롬프트
        aspect_ratio: 이미지 비율 (지원되는 값: 1:1, 16:9, 9:16, 4:3, 3:4, 21:9, 2:3, 3:2, 5:4)
    """
    # 유효성 검사
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}. Supported: {SUPPORTED_ASPECT_RATIOS}")

    # 이미지 생성 로직
    width, height = get_resolution_for_ratio(aspect_ratio)
    # ... Skywork API 호출
```

### 3단계: 프론트엔드 구현 (필요시)

**파일 구조**:
```
src/
├── client/
│   ├── components/
│   │   └── AspectRatioSelector.tsx   # Aspect Ratio 선택 컴포넌트
│   ├── hooks/
│   │   └── useAspectRatios.ts        # Aspect Ratio 데이터 훅
│   └── types/
│       └── image.ts                  # 이미지 타입 정의
```

**구현 세부사항**:

**3.1 타입 정의**:
```typescript
// src/client/types/image.ts
export type AspectRatio =
  | "1:1" | "16:9" | "9:16" | "4:3" | "3:4"
  | "21:9" | "2:3" | "3:2" | "5:4";

export interface AspectRatioOption {
  id: AspectRatio;
  width: number;
  height: number;
  name: string;
  category: "Standard" | "Ultra-Wide" | "Photography" | "Print";
  useCases: string[];
  isNew?: boolean;
}
```

**3.2 Aspect Ratio Selector 컴포넌트**:
```typescript
// src/client/components/AspectRatioSelector.tsx
import { useState } from "react";
import { useAspectRatios } from "../hooks/useAspectRatios";

export function AspectRatioSelector() {
  const { ratios, categories } = useAspectRatios();
  const [selectedRatio, setSelectedRatio] = useState<AspectRatio>("16:9");

  return (
    <div className="aspect-ratio-selector">
      {categories.map(category => (
        <div key={category.name} className="category">
          <h3>{category.name}</h3>
          {category.ratios.map(ratio => (
            <button
              key={ratio.id}
              onClick={() => setSelectedRatio(ratio.id)}
              className={selectedRatio === ratio.id ? "selected" : ""}
              title={ratio.useCases.join(", ")}
            >
              {ratio.id}
              {ratio.isNew && <span className="new-badge">New</span>}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}
```

### 4단계: 테스트 전략

**테스트 커버리지 목표**: 85% 이상

**4.1 단위 테스트**:
```python
# tests/test_aspect_ratio.py
import pytest
from server.models.aspect_ratio import ASPECT_RATIOS, AspectRatioConfig

def test_all_aspect_ratios_have_valid_config():
    """모든 aspect ratio가 유효한 설정을 가지는지 확인"""
    for ratio_id, config in ASPECT_RATIOS.items():
        assert isinstance(config, AspectRatioConfig)
        assert config.width > 0
        assert config.height > 0
        assert len(config.use_cases) > 0

def test_new_aspect_ratios_exist():
    """새로운 aspect ratio가 추가되었는지 확인"""
    new_ratios = ["21:9", "2:3", "3:2", "5:4"]
    for ratio in new_ratios:
        assert ratio in ASPECT_RATIOS
        assert ASPECT_RATIOS[ratio].is_new is True

def test_get_resolution_for_ratio():
    """aspect ratio로 해상도를 정확히 가져오는지 확인"""
    from server.utils.skywork_api import get_resolution_for_ratio

    assert get_resolution_for_ratio("21:9") == ("2560", "1080")
    assert get_resolution_for_ratio("2:3") == ("1080", "1620")
    assert get_resolution_for_ratio("3:2") == ("1620", "1080")
    assert get_resolution_for_ratio("5:4") == ("1350", "1080")

def test_unsupported_aspect_ratio_raises_error():
    """지원하지 않는 aspect ratio가 에러를 발생시키는지 확인"""
    from server.utils.skywork_api import get_resolution_for_ratio

    with pytest.raises(ValueError, match="Unsupported aspect ratio"):
        get_resolution_for_ratio("99:1")
```

**4.2 통합 테스트**:
```python
# tests/test_image_generation_integration.py
import pytest
from server.handlers.image_generation import generate_image

@pytest.mark.asyncio
async def test_generate_image_with_new_aspect_ratios():
    """새로운 aspect ratio로 이미지를 생성하는지 확인"""
    new_ratios = ["21:9", "2:3", "3:2", "5:4"]

    for ratio in new_ratios:
        result = await generate_image(
            prompt="test image",
            aspect_ratio=ratio
        )
        assert result["status"] == "success"
        assert "image_url" in result
```

**4.3 E2E 테스트 (필요시)**:
```typescript
// tests/e2e/aspect-ratio-selector.spec.ts
import { test, expect } from "@playwright/test";

test("should display new aspect ratios in selector", async ({ page }) => {
  await page.goto("/image-generator");

  // 새로운 비율 옵션이 표시되는지 확인
  await expect(page.locator("button[value='21:9']")).toBeVisible();
  await expect(page.locator("button[value='2:3']")).toBeVisible();
  await expect(page.locator("button[value='3:2']")).toBeVisible();
  await expect(page.locator("button[value='5:4']")).toBeVisible();

  // New badge가 표시되는지 확인
  await expect(page.locator(".new-badge")).toHaveCount(4);
});
```

## 위험 및 대응 계획 (Risks and Mitigation)

### 위험 1: Skywork API가 새 비율을 지원하지 않음

**확률**: Medium
**영향**: High

**대응 계획**:
1. API가 지원하지 않는 경우, 이미지 생성 후 crop/resize로 대응
2. Pillow 또는 이미지 처리 라이브러리를 사용하여 클라이언트 사이드에서 조정
3. 사용자에게 "지원하지 않는 비율" 메시지를 표시하고 대안 제시

### 위험 2: 새 비율로 인한 이미지 생성 시간 증가

**확률**: Low
**영향**: Medium

**대응 계획**:
1. 이미지 생성 시간을 모니터링하고 임계값 설정
2. 시간 초과 시 적절한 에러 메시지 표시
3. 캐싱 전략으로 반복 생성 시간 최적화

### 위험 3: 기존 기능과의 호환성 문제

**확률**: Low
**영향**: High

**대응 계획**:
1. 하위 호환성 테스트를 통합 테스트에 포함
2. 기존 비율(1:1, 16:9 등)에 대한 회귀 테스트 실행
3. API 버전 관리로 호환성 보장

## 의존성 (Dependencies)

### 내부 의존성
- SPEC-SKYWORK-001: Skywork API 품질 개선
- 기존 이미지 생성 파이프라인

### 외부 의존성
- Skywork API 안정성
- 클라이언트 UI 지원 (React/Next.js)

## 순서 의존성 (Order Dependencies)

1. **Skywork API 확인** → **백엔드 구현**
   - API 지원 여부를 먼저 확인한 후 백엔드 구현

2. **백엔드 구현** → **프론트엔드 구현**
   - 백엔드 API가 먼저 준비되어야 프론트엔드 연동 가능

3. **프론트엔드 구현** → **테스트**
   - 구현 완료 후 테스트 실행

## 성공 기준 (Success Criteria)

### 기능적 기준
- [ ] 4개 새 aspect ratio(21:9, 2:3, 3:2, 5:4)가 정상 작동
- [ ] 기존 5개 비율(1:1, 16:9, 9:16, 4:3, 3:4)에 영향 없음
- [ ] 유효하지 않은 비율 요청 시 적절한 에러 처리
- [ ] UI에서 모든 비율 선택 가능

### 품질 기준
- [ ] 테스트 커버리지 85% 이상
- [ ] Zero linter warnings
- [ ] Zero security vulnerabilities
- [ ] API response time P95 < 5초

### 사용자 경험 기준
- [ ] 새 비율이 UI에서 명확히 식별 가능 (New badge)
- [ ] 각 비율의 사용 사례가 명확히 표시
- [ ] 비율 선택이 직관적임

## 다음 단계 (Next Steps)

1. `/moai:2-run SPEC-IMG-003` 실행으로 TDD 구현 시작
2. `expert-backend` 에이전트에게 Skywork API 확인 위임
3. `expert-frontend` 에이전트에게 UI 컴포넌트 구현 위임
4. `/moai:3-sync SPEC-IMG-003` 실행으로 문서 동기화
