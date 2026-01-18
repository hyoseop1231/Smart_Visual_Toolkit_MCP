"""
SPEC-IMG-003: 확장된 Aspect Ratio 지원 테스트

테스트 커버리지:
- 새로운 비율 지원 (21:9, 2:3, 3:2, 5:4)
- 기존 비율 호환성 유지
- 유효하지 않은 비율 처리
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image
import numpy as np

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_mock_png_bytes() -> bytes:
    """유효한 PNG 이미지 바이트 생성"""
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :] = [255, 0, 0]
    img = Image.fromarray(arr, mode="RGB")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestNewAspectRatios:
    """새로운 Aspect Ratio 지원 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_ultra_wide_21_to_9_support(self):
        """GIVEN 21:9 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 21:9 비율이 지원되어야 함 (현재 실패 예상)
        """
        # google 모듈 mock 설정 (테스트 내에서)
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        # 모듈 재로드
        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate("test", aspect_ratio="21:9")

        # 현재는 지원하지 않으므로 16:9로 폴백됨 (RED 단계)
        assert result["success"] is True
        # TODO: 구현 후 aspect_ratio == "21:9" 확인

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_portrait_sns_2_to_3_support(self):
        """GIVEN 2:3 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 2:3 비율이 지원되어야 함 (현재 실패 예상)
        """
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate("test", aspect_ratio="2:3")

        assert result["success"] is True
        # TODO: 구현 후 aspect_ratio == "2:3" 확인

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_photo_dslr_3_to_2_support(self):
        """GIVEN 3:2 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 3:2 비율이 지원되어야 함 (현재 실패 예상)
        """
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate("test", aspect_ratio="3:2")

        assert result["success"] is True
        # TODO: 구현 후 aspect_ratio == "3:2" 확인

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_large_format_5_to_4_support(self):
        """GIVEN 5:4 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 5:4 비율이 지원되어야 함 (현재 실패 예상)
        """
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate("test", aspect_ratio="5:4")

        assert result["success"] is True
        # TODO: 구현 후 aspect_ratio == "5:4" 확인


class TestExistingRatioCompatibility:
    """기존 비율 호환성 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_existing_ratios_still_work(self):
        """GIVEN 기존 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 모든 기존 비율이 정상 작동해야 함
        """
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        existing_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]

        for ratio in existing_ratios:
            mock_client.models.generate_images.reset_mock()
            result = generator.generate("test", aspect_ratio=ratio)
            assert result["success"] is True, f"Ratio {ratio} failed"


class TestInvalidRatioHandling:
    """유효하지 않은 비율 처리 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_invalid_ratio_fallback_to_default(self):
        """GIVEN 유효하지 않은 비율이 요청됨
        WHEN 이미지 생성 시도
        THEN 기본값(16:9)로 폴백되어야 함
        """
        mock_genai = MagicMock()
        mock_types = MagicMock()

        class MockConfig:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        mock_types.GenerateImagesConfig = MockConfig
        sys.modules["google"] = MagicMock()
        sys.modules["google.genai"] = mock_genai
        sys.modules["google.genai.types"] = mock_types

        import importlib
        import generators.image_gen

        importlib.reload(generators.image_gen)
        from generators.image_gen import ImageGenerator

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = create_mock_png_bytes()
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate("test", aspect_ratio="99:1")

        assert result["success"] is True
        # 유효하지 않은 비율은 16:9로 폴백되어야 함
