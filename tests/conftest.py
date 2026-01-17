# pytest 설정 및 공통 fixture
import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def mock_styles_data():
    """테스트용 스타일 데이터"""
    return {
        "default_style": "Flat Corporate",
        "styles": [
            {
                "name": "Flat Corporate",
                "keywords": "flat design, corporate, minimal",
                "description": "Clean corporate style",
            },
            {
                "name": "Pixel Art",
                "keywords": "pixel art, retro, 8-bit",
                "description": "Retro pixel art style",
            },
        ],
    }


@pytest.fixture
def mock_genai_client():
    """Mock Google GenAI 클라이언트"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_image = MagicMock()
    mock_image.image.image_bytes = b"fake_image_data"
    mock_response.generated_images = [mock_image]
    mock_client.models.generate_images.return_value = mock_response
    return mock_client


@pytest.fixture
def temp_output_dir(tmp_path):
    """임시 출력 디렉토리"""
    output_dir = tmp_path / "output" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def event_loop():
    """pytest-asyncio 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
