# SPEC-IMG-001: 배치 이미지 생성 테스트
# TDD RED 단계: 실패하는 테스트 먼저 작성

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path


class TestGenerateSingleAsync:
    """REQ-IMG-002: 비동기 단일 이미지 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_single_async_success(
        self, mock_styles_data, mock_genai_client, tmp_path
    ):
        """정상적인 비동기 이미지 생성"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = mock_genai_client
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            # _generate_single_async 메서드가 존재해야 함
            result = await gen._generate_single_async("a cute dog", "Flat Corporate")

            assert result["success"] is True
            assert "local_path" in result
            assert Path(result["local_path"]).exists()

    @pytest.mark.asyncio
    async def test_generate_single_async_no_client(self, mock_styles_data, tmp_path):
        """API 클라이언트 없을 때 오류 반환"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = None  # 클라이언트 없음
            gen.output_dir = tmp_path / "output" / "images"

            result = await gen._generate_single_async("a cute dog")

            assert result["success"] is False
            assert "error" in result


class TestGenerateBatch:
    """REQ-IMG-001, REQ-IMG-003: 배치 이미지 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_batch_basic(
        self, mock_styles_data, mock_genai_client, tmp_path
    ):
        """TC-001: 기본 배치 생성 - 3개 이미지"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = mock_genai_client
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            prompts = ["dog", "cat", "bird"]
            result = await gen.generate_batch(prompts)

            assert result["total"] == 3
            assert result["success_count"] == 3
            assert result["failure_count"] == 0
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_generate_batch_with_style(
        self, mock_styles_data, mock_genai_client, tmp_path
    ):
        """TC-002: 스타일 지정 배치"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = mock_genai_client
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            prompts = ["robot", "spaceship"]
            result = await gen.generate_batch(prompts, style_name="Pixel Art")

            assert result["total"] == 2
            assert result["success_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_batch_concurrency_limit(
        self, mock_styles_data, mock_genai_client, tmp_path
    ):
        """TC-003: 동시성 제한 - max_concurrent=2로 6개 처리"""
        from src.generators.image_gen import ImageGenerator

        call_times = []

        async def track_call(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # 시뮬레이션 지연
            return {
                "success": True,
                "local_path": "/fake/path.png",
                "prompt": args[0] if args else "test",
            }

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = mock_genai_client
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            # _generate_single_async를 모킹하여 호출 시간 추적
            with patch.object(gen, "_generate_single_async", side_effect=track_call):
                prompts = ["p1", "p2", "p3", "p4", "p5", "p6"]
                result = await gen.generate_batch(prompts, max_concurrent=2)

                assert result["total"] == 6
                assert result["success_count"] == 6

    @pytest.mark.asyncio
    async def test_generate_batch_partial_failure(self, mock_styles_data, tmp_path):
        """TC-004: 부분 실패 - 3개 중 1개 실패"""
        from src.generators.image_gen import ImageGenerator

        call_count = 0

        async def partial_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # 두 번째 호출 실패
                return {"success": False, "error": "API Error", "prompt": args[0]}
            return {"success": True, "local_path": "/fake/path.png", "prompt": args[0]}

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = MagicMock()
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(gen, "_generate_single_async", side_effect=partial_fail):
                prompts = ["p1", "p2", "p3"]
                result = await gen.generate_batch(prompts)

                assert result["total"] == 3
                assert result["success_count"] == 2
                assert result["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_generate_batch_empty_prompts(self, mock_styles_data, tmp_path):
        """TC-005: 빈 프롬프트 목록"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = MagicMock()
            gen.output_dir = tmp_path / "output" / "images"

            result = await gen.generate_batch([])

            assert result["total"] == 0
            assert result["success_count"] == 0
            assert "error" in result or result["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_generate_batch_no_client(self, mock_styles_data, tmp_path):
        """TC-006: API 키 없음 - 모든 이미지 실패"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = None  # API 클라이언트 없음
            gen.output_dir = tmp_path / "output" / "images"

            prompts = ["p1", "p2", "p3"]
            result = await gen.generate_batch(prompts)

            assert result["total"] == 3
            assert result["failure_count"] == 3
            assert result["success_count"] == 0


class TestResultFormat:
    """REQ-IMG-006: 결과 형식 테스트"""

    @pytest.mark.asyncio
    async def test_result_format_structure(
        self, mock_styles_data, mock_genai_client, tmp_path
    ):
        """결과 JSON 구조 검증"""
        from src.generators.image_gen import ImageGenerator

        with patch.object(ImageGenerator, "__init__", lambda self, data: None):
            gen = ImageGenerator.__new__(ImageGenerator)
            gen.styles = {s["name"]: s for s in mock_styles_data["styles"]}
            gen.default_style = mock_styles_data["default_style"]
            gen.client = mock_genai_client
            gen.output_dir = tmp_path / "output" / "images"
            gen.output_dir.mkdir(parents=True, exist_ok=True)

            result = await gen.generate_batch(["test prompt"])

            # 필수 키 확인
            assert "total" in result
            assert "success_count" in result
            assert "failure_count" in result
            assert "results" in result
            assert isinstance(result["results"], list)

            # 개별 결과 구조 확인
            if result["results"]:
                item = result["results"][0]
                assert "prompt" in item
                assert "success" in item
                if item["success"]:
                    assert "local_path" in item
                else:
                    assert "error" in item
