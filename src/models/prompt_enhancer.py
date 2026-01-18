"""
프롬프트 강화 및 최적화 모듈

SPEC-IMG-004: 고급 이미지 제어 기능을 위한
프롬프트 강화, 길이 검증, 네거티브 프롬프트 구성 기능을 제공합니다.
"""

from typing import Optional


class PromptEnhancer:
    """
    프롬프트 강화 및 검증 클래스

    스타일 키워드 추가, 프롬프트 길이 검증,
    네거티브 프롬프트 구성 기능을 제공합니다.
    """

    STYLE_INTENSITY_WEIGHTS = {
        "weak": 0.5,
        "normal": 1.0,
        "strong": 1.5,
    }

    # 스타일별 기본 네거티브 프롬프트
    STYLE_NEGATIVE_PROMPTS = {
        "Corporate Memphis": "low quality, blurry, distorted, ugly, amateur",
        "Flat Corporate": "low quality, blurry, distorted, ugly, amateur",
        "Corporate": "low quality, blurry, distorted, ugly, amateur",
        "default": "low quality, blurry, distorted",
    }

    def enhance(
        self, prompt: str, style: Optional[str] = None, intensity: str = "normal"
    ) -> str:
        """
        스타일 키워드를 프롬프트에 추가합니다.

        Args:
            prompt: 원본 프롬프트
            style: 스타일 키워드 (쉼표표로 구분)
            intensity: 강도 ("weak", "normal", "strong")

        Returns:
            강화된 프롬프트

        강도에 따른 키워드 수:
        - weak: 1-2개 키워드
        - normal: 2-4개 키워드
        - strong: 4-6개 키워드
        """
        if not style:
            return prompt

        # 스타일 키워드 파싱
        keywords = [kw.strip() for kw in style.split(",") if kw.strip()]

        if not keywords:
            return prompt

        # 강도에 따른 키워드 수 결정
        intensity_map = {
            "weak": (1, 2),
            "normal": (2, 4),
            "strong": (4, 6),
        }

        min_count, max_count = intensity_map.get(intensity, (2, 4))
        max_keywords = min(len(keywords), max_count)

        # 키워드 선택 (앞에서부터)
        selected_keywords = keywords[:max_keywords]

        # 프롬프트에 키워드 추가 (접미사 방식)
        if selected_keywords:
            enhanced = f"{prompt}, {', '.join(selected_keywords)}"
            return enhanced

        return prompt

    def validate_length(self, prompt: str, max_length: int = 1000) -> tuple[str, bool]:
        """
        프롬프트 길이를 검증하고 필요시 트리밍합니다.

        Args:
            prompt: 검증할 프롬프트
            max_length: 최대 길이 (기본값: 1000)

        Returns:
            (검증된/트리밍된 프롬프트, 길이 적합 여부)
        """
        if len(prompt) <= max_length:
            return prompt, True

        # 트리밍 (말줄임표 추가)
        trimmed = prompt[: max_length - 3] + "..."
        return trimmed, False

    def build_negative_prompt(
        self, custom_negative: Optional[str] = None, style: Optional[str] = None
    ) -> Optional[str]:
        """
        스타일별 기본 네거티브 프롬프트와 사용자 입력을 병합합니다.

        Args:
            custom_negative: 사용자 정의 네거티브 프롬프트
            style: 스타일 이름

        Returns:
            병합된 네거티브 프롬프트 (둘 다 None이면 None)
        """
        parts = []

        # 사용자 정의 네거티브 프롬프트
        if custom_negative:
            parts.append(custom_negative)

        # 스타일별 기본 네거티브 프롬프트
        if style:
            default_negative = self.STYLE_NEGATIVE_PROMPTS.get(
                style, self.STYLE_NEGATIVE_PROMPTS["default"]
            )
            parts.append(default_negative)

        if not parts:
            return None

        return ", ".join(parts)


def validate_resolution(
    width: int, height: int, min_size: int = 256, max_size: int = 2048
) -> tuple[int, int, bool]:
    """
    해상도를 검증하고 API 제약 내로 조정합니다.

    Args:
        width: 요청된 너비
        height: 요청된 높이
        min_size: 최소 해상도 (기본값: 256)
        max_size: 최대 해상도 (기본값: 2048)

    Returns:
        (조정된 너비, 조정된 높이, 조정 여부)

    제약사항:
    - 최소: 256x256
    - 최대: 2048x2048
    """
    adjusted = False
    new_width = width
    new_height = height

    # 비율 계산 (원본 비율 유지용)
    original_ratio = width / height if height > 0 else 1.0

    # 최소 해상도 검증
    if width < min_size or height < min_size:
        # 더 작은 쪽을 min_size로 맞추고 비율 유지
        if width < height:
            new_width = min_size
            new_height = int(min_size / original_ratio)
        else:
            new_height = min_size
            new_width = int(min_size * original_ratio)
        adjusted = True

    # 최대 해상도 검증 (비율 유지하며 조정)
    if new_width > max_size or new_height > max_size:
        # 더 큰 쪽이 max_size를 초과하면 비율 유지하며 조정
        if new_width > new_height:
            new_width = max_size
            new_height = int(max_size / original_ratio)
        else:
            new_height = max_size
            new_width = int(max_size * original_ratio)
        adjusted = True

    # 최소/최대 재검증 (비율 유지 후)
    if new_width < min_size:
        new_width = min_size
        adjusted = True
    if new_height < min_size:
        new_height = min_size
        adjusted = True
    if new_width > max_size:
        new_width = max_size
        adjusted = True
    if new_height > max_size:
        new_height = max_size
        adjusted = True

    return new_width, new_height, adjusted
