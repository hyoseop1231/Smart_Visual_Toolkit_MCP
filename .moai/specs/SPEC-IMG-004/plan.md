# SPEC-IMG-004: 고급 이미지 제어 및 프롬프트 최적화
## Implementation Plan

---

## 1. 마일스톤 (Milestones)

### Milestone 1: 프리미엄 (필수 기능)
**목표**: 핵심 고급 제어 기능 구현

- [ ] 해상도 제어 기능 구현
- [ ] 프롬프트 강화 시스템 구현
- [ ] 네거티브 프롬프트 지원
- [ ] 기본 단위 테스트 작성

### Milestone 2: 표준 (스타일 최적화)
**목표**: 스타일 강도 제어 및 검증

- [ ] 스타일 강도 제어 (weak/normal/strong)
- [ ] 프롬프트 길이 검증 및 트리밍
- [ ] 해상도 검증 및 자동 조정
- [ ] 통합 테스트 작성

### Milestone 3: 최종 (사용자 경험)
**목표**: 사용자 친화적 기능 완성

- [ ] 해상도 프리셋 (FHD, 4K 등)
- [ ] 상세 오류 메시지 개선
- [ ] API 문서 업데이트
- [ ] 성능 최적화

---

## 2. 기술 접근 방식 (Technical Approach)

### 2.1 모듈 아키텍처

```
src/
├── generators/
│   ├── image_gen.py              # [수정] ImageGenerator 확장
│   └── image_gen_advanced.py     # [신규] 고급 제어 로직
├── models/
│   ├── prompt_enhancer.py        # [신규] 프롬프트 강화
│   ├── resolution_validator.py   # [신규] 해상도 검증
│   └── style_config.py           # [신규] 스타일 강도 설정
├── resources/
│   ├── banana_styles.json        # [수정] 강도별 키워드 추가
│   └── resolution_presets.json   # [신규] 해상도 프리셋
└── tests/
    ├── test_prompt_enhancer.py   # [신규]
    ├── test_resolution_validator.py  # [신규]
    └── test_image_gen_advanced.py    # [신규]
```

### 2.2 주요 컴포넌트 설계

#### 2.2.1 PromptEnhancer 클래스

```python
class PromptEnhancer:
    """프롬프트 강화 및 검증"""

    def __init__(self, style_config_path: str):
        self.styles = self._load_styles(style_config_path)

    def enhance(
        self,
        prompt: str,
        style: Optional[str],
        intensity: str = "normal"
    ) -> EnhancedPrompt:
        """
        프롬프트를 강화하고 결과를 반환합니다.

        Returns:
            EnhancedPrompt(
                original="user prompt",
                enhanced="user prompt + style keywords",
                applied_keywords=["keyword1", "keyword2"],
                was_enhanced=True
            )
        """

    def validate_length(
        self,
        prompt: str,
        max_length: int = 1000
    ) -> ValidationResult:
        """프롬프트 길이를 검증합니다."""
```

#### 2.2.2 ResolutionValidator 클래스

```python
class ResolutionValidator:
    """해상도 검증 및 조정"""

    MIN_RESOLUTION = 256
    MAX_RESOLUTION = 2048

    SUPPORTED_RATIOS = [
        (1, 1),    # 정방형
        (4, 3),    # 표준
        (16, 9),   # 와이드
        (3, 4),    # 세로 표준
        (9, 16)    # 세로 와이드
    ]

    def validate(
        self,
        width: int,
        height: int
    ) -> ResolutionResult:
        """
        해상도를 검증하고 조정합니다.

        Returns:
            ResolutionResult(
                width=1920,
                height=1080,
                was_adjusted=False,
                adjustment_reason=None
            )
        """
```

#### 2.2.3 ImageGenerator 확장

```python
class ImageGenerator:
    # 기존 메서드 유지...

    async def generate_advanced(
        self,
        prompt: str,
        style: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: Optional[str] = None,
        style_intensity: str = "normal",
        enhance_prompt: bool = True
    ) -> GenerationResult:
        """
        고급 매개변수로 이미지를 생성합니다.
        """
```

### 2.3 데이터 구조

#### EnhancedPrompt 데이터클래스

```python
@dataclass
class EnhancedPrompt:
    original: str
    enhanced: str
    applied_keywords: List[str]
    was_enhanced: bool
    was_trimmed: bool = False
    original_length: int = 0
    final_length: int = 0
```

#### ResolutionResult 데이터클래스

```python
@dataclass
class ResolutionResult:
    width: int
    height: int
    was_adjusted: bool
    adjustment_reason: Optional[str]
    aspect_ratio: Tuple[int, int]
```

### 2.4 스타일 강도 구현

#### banana_styles.json 확장

```json
{
  "Corporate Memphis": {
    "weak_keywords": [
      "simple",
      "minimal"
    ],
    "normal_keywords": [
      "flat design",
      "clean vector",
      "minimal colors"
    ],
    "strong_keywords": [
      "flat design illustration",
      "clean vector art",
      "minimal color palette",
      "geometric shapes",
      "professional aesthetic"
    ],
    "negative_keywords": [
      "realistic",
      "3D render",
      "photograph"
    ]
  }
}
```

#### 강도별 키워드 선택 로직

```python
def get_keywords_by_intensity(
    style_config: dict,
    intensity: str
) -> List[str]:
    """
    강도에 따라 키워드 수를 결정합니다:
    - weak: 상위 1-2개 키워드
    - normal: 상위 2-4개 키워드
    - strong: 전체 키워드
    """
```

---

## 3. 구현 순서 (Implementation Order)

### 단계 1: PromptEnhancer 구현
1. `PromptEnhancer` 클래스 스켈레톤 작성
2. `enhance()` 메서드 구현 (스타일 키워드 추가)
3. `validate_length()` 메서드 구현 (길이 검증 및 트리밍)
4. 단위 테스트 작성

### 단계 2: ResolutionValidator 구현
1. `ResolutionValidator` 클래스 스켈레톤 작성
2. `validate()` 메서드 구현 (해상도 검증)
3. `calculate_aspect_ratio()` 헬퍼 메서드 구현
4. 단위 테스트 작성

### 단계 3: ImageGenerator 확장
1. `generate_advanced()` 메서드 구현
2. PromptEnhancer, ResolutionValidator 통합
3. 네거티브 프롬프트 처리 로직 추가
4. API 매개변수 구성 로직 구현

### 단계 4: MCP 도구 등록
1. `generate_image_advanced()` 도구 등록
2. 입력 파라미터 검증 추가
3. 결과 포맷팅 구현
4. 통합 테스트 작성

### 단계 5: 스타일 강도 구현
1. banana_styles.json 확장 (강도별 키워드)
2. 스타일 강도 가중치 로직 구현
3. 네거티브 프롬프트 자동 생성
4. 사용자 정의 네거티브 프롬프트 병합

### 단계 6: 사용자 경험 개선
1. 해상도 프리셋 구현 (FHD, 4K 등)
2. 상세 오류 메시지 구현
3. API 문서 업데이트
4. 예제 코드 작성

---

## 4. 위험 및 대응 계획 (Risks and Mitigation)

| 위험 | 확률 | 영향 | 대응 계획 |
|------|------|------|----------|
| Imagen API가 해상도 매개변수를 지원하지 않음 | MEDIUM | HIGH | aspect_ratio 기반 해상도 매핑으로 대체 |
| 프롬프트 강화가 사용자 의도와 맞지 않음 | LOW | MEDIUM | enhance_prompt 옵트아웃 제공 |
| 스타일 강도가 의도한 대로 작동하지 않음 | MEDIUM | MEDIUM | A/B 테스트 후 키워드 가중치 조정 |
| API Rate Limit 초과 | LOW | MEDIUM | 기존 캐싱 레이어(SPEC-CACHE-001) 활용 |

---

## 5. 성능 고려사항 (Performance Considerations)

### 5.1 최적화 전략

- **프롬프트 강화 캐싱**: 동일 프롬프트+스타일 조합 캐싱
- **스타일 설정 로딩**: 앱 시작 시 한 번만 로드
- **해상도 검증**: O(1) 복잡도의 단순 비교

### 5.2 예상 성능

| 작업 | 예상 시간 | 비고 |
|------|----------|------|
| 프롬프트 강화 | < 10ms | 메모리 연산 |
| 해상도 검증 | < 5ms | 단순 비교 |
| 전체 전처리 | < 20ms | API 호출 전 |
| API 호출 | 2-5초 | 외부 의존 |

---

## 6. 테스트 전략 (Testing Strategy)

### 6.1 단위 테스트

- `PromptEnhancer`: 모든 강도 레벨, 스타일 조합
- `ResolutionValidator`: 경계값, 비율 검증
- 데이터클래스: 직렬화/역직렬화

### 6.2 통합 테스트

- 전체 파이프라인: 입력 → 강화 → 검증 → API 호출
- 오류 경로: 잘못된 해상도, 너무 긴 프롬프트

### 6.3 E2E 테스트

- 실제 API 호출로 최종 이미지 생성 검증
- 다양한 해상도/스타일/강도 조합 테스트

---

## 7. 롤백 계획 (Rollback Plan)

**문제 발생 시**:
1. 기존 `generate_image()` 도구는 그대로 유지
2. `generate_image_advanced()` 실패해도 기존 기능 영향 없음
3. 새로운 모듈은 선택적이므로 독립적으로 비활성화 가능

**롤백 절차**:
1. `generate_image_advanced()` 도구 등록 해제
2. main.py에서 import 제거
3. 기존 `generate_image()` 도구로 계속 운영
