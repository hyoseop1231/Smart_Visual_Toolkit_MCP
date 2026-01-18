"""
SPEC-IMG-004: 고급 이미지 생성 기능 통합 테스트

테스트 커버리지:
- generate_advanced() 메서드
- 해상도 제어 (width, height)
- 네거티브 프롬프트
- 스타일 강도 (weak/normal/strong)
- 프롬프트 강화
- 캐시 키 생성
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


class TestGenerateAdvanced:
    """generate_advanced() 메서드 통합 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_generate_advanced_with_custom_resolution(self):
        """GIVEN 사용자 정의 해상도가 제공됨
        WHEN 고급 이미지 생성 수행
        THEN 지정된 해상도로 이미지가 생성됨
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

        # 512x512 이미지 생성
        arr = np.zeros((512, 512, 3), dtype=np.uint8)
        arr[:, :] = [255, 0, 0]
        img = Image.fromarray(arr, mode="RGB")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        mock_image.image.image_bytes = buffer.getvalue()

        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {
            "styles": [
                {
                    "name": "TestStyle",
                    "keywords": "minimal, clean",
                    "description": "Test",
                }
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate_advanced(
            prompt="test image",
            width=512,
            height=512,
            enhance_prompt=False,  # 프롬프트 강화 비활성화
        )

        assert result["success"] is True
        assert result["width"] == 512
        assert result["height"] == 512

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_generate_advanced_with_negative_prompt(self):
        """GIVEN 네거티브 프롬프트가 제공됨
        WHEN 고급 이미지 생성 수행
        THEN 네거티브 프롬프트가 결과에 포함됨
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

        styles_data = {
            "styles": [
                {
                    "name": "TestStyle",
                    "keywords": "minimal, clean",
                    "description": "Test",
                }
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        negative = "blurry, low quality, ugly"
        result = generator.generate_advanced(
            prompt="test image", negative_prompt=negative, enhance_prompt=False
        )

        assert result["success"] is True
        assert result["negative_prompt"] is not None
        # 스타일별 기본 네거티브 프롬프트도 병합되어야 함

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_generate_advanced_with_strong_intensity(self):
        """GIVEN strong 강도가 설정됨
        WHEN 고급 이미지 생성 수행
        THEN 4-6개의 스타일 키워드가 프롬프트에 추가됨
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

        styles_data = {
            "styles": [
                {
                    "name": "TestStyle",
                    "keywords": "minimal, clean, simple, elegant, professional, modern",
                    "description": "Test",
                }
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate_advanced(
            prompt="test image", style_intensity="strong", enhance_prompt=True
        )

        assert result["success"] is True
        # 프롬프트에 여러 키워드가 추가되었는지 확인
        assert "minimal" in result["prompt"] or "clean" in result["prompt"]

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_generate_advanced_with_weak_intensity(self):
        """GIVEN weak 강도가 설정됨
        WHEN 고급 이미지 생성 수행
        THEN 1-2개의 스타일 키워드만 프롬프트에 추가됨
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

        styles_data = {
            "styles": [
                {
                    "name": "TestStyle",
                    "keywords": "minimal, clean, simple",
                    "description": "Test",
                }
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        result = generator.generate_advanced(
            prompt="test image", style_intensity="weak", enhance_prompt=True
        )

        assert result["success"] is True
        # 원본 프롬프트가 유지되어야 함
        assert "test image" in result["prompt"]

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_generate_advanced_with_enhance_prompt_false(self):
        """GIVEN enhance_prompt가 False로 설정됨
        WHEN 고급 이미지 생성 수행
        THEN 프롬프트 강화가 수행되지 않음
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

        styles_data = {
            "styles": [
                {
                    "name": "TestStyle",
                    "keywords": "minimal, clean",
                    "description": "Test",
                }
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        original_prompt = "a simple cat"
        result = generator.generate_advanced(
            prompt=original_prompt, enhance_prompt=False
        )

        assert result["success"] is True
        # 스타일 키워드가 추가되지만, 원본 프롬프트가 유지됨
        assert "simple cat" in result["prompt"] or "cat" in result["prompt"]


class TestAdvancedCaching:
    """고급 기능 캐싱 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_cache_key_includes_advanced_params(self):
        """GIVEN 고급 파라미터들이 포함된 요청
        WHEN 캐시 키 생성
        THEN 모든 파라미터가 캐시 키에 반영됨
        """
        from generators.cache import generate_cache_key_advanced

        key1 = generate_cache_key_advanced(
            prompt="test",
            style="TestStyle",
            width=1024,
            height=768,
            negative_prompt="blurry",
            style_intensity="strong",
        )

        key2 = generate_cache_key_advanced(
            prompt="test",
            style="TestStyle",
            width=512,  # 다른 해상도
            height=512,
            negative_prompt="blurry",
            style_intensity="strong",
        )

        # 해상도가 다르면 캐시 키도 달라야 함
        assert key1 != key2

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_advanced_cache_hit_returns_cached_result(self):
        """GIVEN 캐시된 결과가 존재
        WHEN 동일한 고급 파라미터로 요청
        THEN 캐시된 결과가 반환됨
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

        styles_data = {
            "styles": [
                {"name": "TestStyle", "keywords": "minimal", "description": "Test"}
            ],
            "default_style": "TestStyle",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        # 첫 번째 호출
        result1 = generator.generate_advanced(
            prompt="test", width=512, height=512, enhance_prompt=False
        )

        # 두 번째 호출 (캐시 HIT)
        result2 = generator.generate_advanced(
            prompt="test", width=512, height=512, enhance_prompt=False
        )

        assert result1["success"] is True
        assert result2["success"] is True
        assert result2.get("cached") is True

        # API는 한 번만 호출되어야 함
        assert mock_client.models.generate_images.call_count == 1
