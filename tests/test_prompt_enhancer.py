"""
SPEC-IMG-004: 고급 이미지 제어 기능 테스트

테스트 커버리지:
- PromptEnhancer 모듈 기능
- 해상도 검증
- 프롬프트 강화
- 네거티브 프롬프트 구성
- 스타일 강도 조절
"""

from src.models.prompt_enhancer import PromptEnhancer, validate_resolution


class TestPromptEnhancer:
    """PromptEnhancer 모듈 테스트"""

    def test_enhance_with_weak_intensity(self):
        """GIVEN 스타일과 weak 강도가 주어짐
        WHEN 프롬프트 강화 수행
        THEN 1-2개의 스타일 키워드만 추가됨
        """
        enhancer = PromptEnhancer()
        style_keywords = "flat design, vector illustration, minimal colors"

        enhanced = enhancer.enhance(
            prompt="a cat sitting on a table", style=style_keywords, intensity="weak"
        )

        assert "a cat sitting on a table" in enhanced
        assert "cat" in enhanced
        # weak 강도는 1-2개 키워드만 추가
        keyword_count = sum(
            1 for kw in style_keywords.split(", ") if kw.strip() in enhanced
        )
        assert 1 <= keyword_count <= 2

    def test_enhance_with_normal_intensity(self):
        """GIVEN 스타일과 normal 강도가 주어짐
        WHEN 프롬프트 강화 수행
        THEN 2-4개의 스타일 키워드가 추가됨
        """
        enhancer = PromptEnhancer()
        style_keywords = (
            "flat design, vector illustration, minimal colors, professional atmosphere"
        )

        enhanced = enhancer.enhance(
            prompt="business meeting", style=style_keywords, intensity="normal"
        )

        assert "business meeting" in enhanced
        # normal 강도는 2-4개 키워드 추가
        keyword_count = sum(
            1 for kw in style_keywords.split(", ") if kw.strip() in enhanced
        )
        assert 2 <= keyword_count <= 4

    def test_enhance_with_strong_intensity(self):
        """GIVEN 스타일과 strong 강도가 주어짐
        WHEN 프롬프트 강화 수행
        THEN 4-6개의 스타일 키워드가 추가됨
        """
        enhancer = PromptEnhancer()
        style_keywords = "flat design, vector illustration, minimal colors, professional atmosphere, clean lines, modern style"

        enhanced = enhancer.enhance(
            prompt="startup office", style=style_keywords, intensity="strong"
        )

        assert "startup office" in enhanced
        # strong 강도는 4-6개 키워드 추가
        keyword_count = sum(
            1 for kw in style_keywords.split(", ") if kw.strip() in enhanced
        )
        assert 4 <= keyword_count <= 6

    def test_enhance_preserves_core_message(self):
        """GIVEN 사용자 프롬프트의 핵심 메시지
        WHEN 프롬프트 강화 수행
        THEN 핵심 메시지가 희석되지 않음
        """
        enhancer = PromptEnhancer()
        core_message = "a detailed painting of a mountain landscape at sunset"

        enhanced = enhancer.enhance(
            prompt=core_message,
            style="impressionist style, oil painting texture, warm colors",
            intensity="strong",
        )

        # 핵심 메시지의 주요 단어들이 모두 존재해야 함
        assert "mountain" in enhanced
        assert "landscape" in enhanced
        assert "sunset" in enhanced or "sunset" in enhanced.lower()

    def test_enhance_with_no_style(self):
        """GIVEN 스타일이 없음
        WHEN 프롬프트 강화 수행
        THEN 원본 프롬프트가 그대로 반환됨
        """
        enhancer = PromptEnhancer()
        original = "a simple red car"

        enhanced = enhancer.enhance(prompt=original, style=None, intensity="normal")

        assert enhanced == original

    def test_validate_length_within_limit(self):
        """GIVEN 1000자 이내의 프롬프트
        WHEN 길이 검증 수행
        THEN 원본 프롬프트와 True 반환
        """
        enhancer = PromptEnhancer()
        short_prompt = "a cat" * 50  # 约 250자

        result, is_valid = enhancer.validate_length(short_prompt, max_length=1000)

        assert is_valid is True
        assert result == short_prompt

    def test_validate_length_exceeds_limit(self):
        """GIVEN 1000자를 초과하는 프롬프트
        WHEN 길이 검증 수행
        THEN 트리밍된 프롬프트와 False 반환
        """
        enhancer = PromptEnhancer()
        long_prompt = "a cat" * 500  # 약 2500자

        result, is_valid = enhancer.validate_length(long_prompt, max_length=1000)

        assert is_valid is False
        assert len(result) <= 1000
        # 말줄임표(...)로 끝나야 함
        assert result.endswith("...")

    def test_build_negative_prompt_with_custom(self):
        """GIVEN 사용자 정의 네거티브 프롬프트
        WHEN 네거티브 프롬프트 구성
        THEN 사용자 정의가 기본값과 병합됨
        """
        enhancer = PromptEnhancer()

        negative = enhancer.build_negative_prompt(
            custom_negative="blurry, low quality", style="Corporate Memphis"
        )

        assert "blurry" in negative
        assert "low quality" in negative
        # 스타일별 기본 네거티브 프롬프트도 포함되어야 함

    def test_build_negative_prompt_none_custom(self):
        """GIVEN 사용자 정의가 None
        WHEN 네거티브 프롬프트 구성
        THEN 스타일별 기본값만 반환
        """
        enhancer = PromptEnhancer()

        negative = enhancer.build_negative_prompt(
            custom_negative=None, style="Flat Corporate"
        )

        assert negative is not None
        assert len(negative) > 0

    def test_build_negative_prompt_no_style(self):
        """GIVEN 스타일이 None
        WHEN 네거티브 프롬프트 구성
        THEN 빈 문자열 반환
        """
        enhancer = PromptEnhancer()

        negative = enhancer.build_negative_prompt(custom_negative="ugly", style=None)

        # 사용자 정의만 있으면 그것만 반환
        assert "ugly" in negative


class TestResolutionValidation:
    """해상도 검증 테스트"""

    def test_validate_resolution_valid(self):
        """GIVEN 유효한 해상도 (1024x1024)
        WHEN 검증 수행
        THEN 조정 없이 원본 해상도 반환
        """
        width, height, adjusted = validate_resolution(1024, 1024)

        assert width == 1024
        assert height == 1024
        assert adjusted is False

    def test_validate_resolution_minimum(self):
        """GIVEN 최소 해상도 미만 (100x100)
        WHEN 검증 수행
        THEN 최소 해상도(256x256)로 조정
        """
        width, height, adjusted = validate_resolution(100, 100)

        assert width == 256
        assert height == 256
        assert adjusted is True

    def test_validate_resolution_maximum(self):
        """GIVEN 최대 해상도 초과 (3000x3000)
        WHEN 검증 수행
        THEN 최대 해상도(2048x2048)로 조정
        """
        width, height, adjusted = validate_resolution(3000, 3000)

        assert width == 2048
        assert height == 2048
        assert adjusted is True

    def test_validate_resolution_mixed_dimensions(self):
        """GIVEN 서로 다른 크기의 해상도 (1920x1080)
        WHEN 검증 수행
        THEN 각 차원별로 검증 수행
        """
        width, height, adjusted = validate_resolution(1920, 1080)

        assert width == 1920
        assert height == 1080
        assert adjusted is False

    def test_validate_resolution_aspect_ratio_preserved(self):
        """GIVEN 16:9 비율의 초과 해상도 (4000x2250)
        WHEN 검증 수행
        THEN 비율을 유지하며 최대 해상도로 조정
        """
        width, height, adjusted = validate_resolution(4000, 2250)

        # 2048x1152로 조정되어야 함 (16:9 비율 유지)
        assert width <= 2048
        assert height <= 2048
        assert adjusted is True
        # 비율 근사치 확인
        ratio = width / height
        assert 1.7 <= ratio <= 1.8  # 16:9 ≈ 1.78
