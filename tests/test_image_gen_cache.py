"""
SPEC-CACHE-001: ImageGenerator 캐시 통합 테스트

테스트 시나리오:
- TC-009: 캐시 활성화/비활성화
- TC-010: 동일 요청 캐시 HIT
- TC-011: 실패 결과 캐싱 방지
- TC-012: 캐시 통계 조회
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# google 모듈 mock 설정 (임포트 전에 수행)
mock_genai_module = MagicMock()
mock_types_module = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = mock_genai_module
sys.modules["google.genai.types"] = mock_types_module

# 이제 image_gen 임포트 가능
from generators.image_gen import ImageGenerator  # noqa: E402


class TestImageGeneratorCacheIntegration:
    """ImageGenerator 캐시 통합 테스트"""

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_cache_enabled_by_default(self):
        """캐시는 기본적으로 활성화"""
        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)

        assert generator._cache_enabled is True
        assert generator._cache is not None

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_cache_disabled_via_env(self):
        """환경 변수로 캐시 비활성화"""
        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)

        assert generator._cache_enabled is False
        assert generator._cache is None

    @patch.dict(
        os.environ,
        {
            "CACHE_ENABLED": "true",
            "CACHE_MAX_SIZE": "50",
            "CACHE_TTL_SECONDS": "1800",
            "GOOGLE_API_KEY": "test-key",
        },
    )
    def test_cache_config_from_env(self):
        """환경 변수에서 캐시 설정 로드"""
        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)

        assert generator._cache._max_size == 50
        assert generator._cache._ttl_seconds == 1800

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_cache_hit_returns_cached_result(self):
        """동일 요청 시 캐시 HIT"""
        # Mock 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = b"fake_image_data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {
            "styles": [{"name": "realistic", "keywords": "realistic style"}],
            "default_style": "realistic",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client  # 클라이언트 직접 주입

        # 첫 번째 호출 - API 호출 발생
        result1 = generator.generate("a cat", "realistic", "16:9")
        assert result1["success"] is True
        assert mock_client.models.generate_images.call_count == 1

        # 두 번째 호출 - 캐시 HIT (API 호출 없음)
        result2 = generator.generate("a cat", "realistic", "16:9")
        assert result2["success"] is True
        assert result2.get("cached") is True
        assert mock_client.models.generate_images.call_count == 1  # 증가하지 않음

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_failed_result_not_cached(self):
        """실패한 결과는 캐싱하지 않음"""
        # Mock 설정 - 실패 응답
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = Exception("API Error")

        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        # 첫 번째 호출 - 실패
        result1 = generator.generate("a cat", None, "16:9")
        assert result1["success"] is False

        # 두 번째 호출 - 다시 API 호출 (캐시되지 않음)
        result2 = generator.generate("a cat", None, "16:9")
        assert result2["success"] is False
        assert mock_client.models.generate_images.call_count == 2

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_get_cache_stats(self):
        """캐시 통계 조회"""
        # Mock 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = b"fake_image_data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {
            "styles": [{"name": "realistic", "keywords": "realistic style"}],
            "default_style": "realistic",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        # 요청 수행
        generator.generate("cat", "realistic", "16:9")  # MISS
        generator.generate("cat", "realistic", "16:9")  # HIT
        generator.generate("dog", "realistic", "16:9")  # MISS

        stats = generator.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["cache_size"] == 2

    @patch.dict(os.environ, {"CACHE_ENABLED": "false", "GOOGLE_API_KEY": "test-key"})
    def test_get_cache_stats_disabled(self):
        """캐시 비활성화 시 통계 조회"""
        styles_data = {"styles": [], "default_style": "default"}
        generator = ImageGenerator(styles_data)

        stats = generator.get_cache_stats()

        assert stats["enabled"] is False

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_clear_cache(self):
        """캐시 초기화"""
        # Mock 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = b"fake_image_data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {
            "styles": [{"name": "realistic", "keywords": "realistic style"}],
            "default_style": "realistic",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        # 캐시 채우기
        generator.generate("cat", "realistic", "16:9")
        generator.generate("dog", "realistic", "16:9")

        assert generator._cache.size == 2

        # 캐시 초기화
        result = generator.clear_cache()

        assert result["success"] is True
        assert result["cleared_count"] == 2
        assert generator._cache.size == 0

    @patch.dict(os.environ, {"CACHE_ENABLED": "true", "GOOGLE_API_KEY": "test-key"})
    def test_different_params_different_cache_entries(self):
        """다른 파라미터는 다른 캐시 항목"""
        # Mock 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.image_bytes = b"fake_image_data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response

        styles_data = {
            "styles": [
                {"name": "realistic", "keywords": "realistic style"},
                {"name": "cartoon", "keywords": "cartoon style"},
            ],
            "default_style": "realistic",
        }
        generator = ImageGenerator(styles_data)
        generator.client = mock_client

        # 서로 다른 파라미터로 요청
        generator.generate("cat", "realistic", "16:9")
        generator.generate("cat", "cartoon", "16:9")  # 다른 스타일
        generator.generate("cat", "realistic", "1:1")  # 다른 비율

        # 3개의 서로 다른 캐시 항목
        assert generator._cache.size == 3
        assert mock_client.models.generate_images.call_count == 3
