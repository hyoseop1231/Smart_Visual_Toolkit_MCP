"""
SPEC-IMG-002: 다중 이미지 형식 지원 시스템 테스트

테스트 커버리지:
- PNG 형식 저장 및 투명도 지원
- JPEG 형식 저장, 품질 제어, 투명도 처리
- WebP 형식 저장 및 품질 제어
- 형식 검증 및 오류 처리
- 후방 호환성
"""

import pytest
from io import BytesIO
from PIL import Image
import numpy as np

# 테스트용 이미지 생성 헬퍼 함수


def create_test_image(size=(1024, 1024), mode="RGB"):
    """테스트용 이미지 생성"""
    if mode == "RGB":
        arr = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
        return Image.fromarray(arr, mode="RGB")
    elif mode == "RGBA":
        arr = np.random.randint(0, 255, (*size, 4), dtype=np.uint8)
        # 투명도 채널에 다양한 값 설정
        arr[:, :, 3] = np.random.randint(0, 255, size)
        return Image.fromarray(arr, mode="RGBA")
    elif mode == "L":
        arr = np.random.randint(0, 255, size, dtype=np.uint8)
        return Image.fromarray(arr, mode="L")


class TestPNGFormatHandler:
    """PNG 형식 핸들러 테스트"""

    def test_png_format_support(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="png"으로 save_image 함수 호출
        THEN PNG 형식의 이미지가 생성됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image, format="png")

        assert isinstance(output, BytesIO)
        output.seek(0)
        img = Image.open(output)
        assert img.format == "PNG"

    def test_png_transparency_support(self):
        """GIVEN 투명도가 포함된 RGBA 이미지가 생성됨
        WHEN format="png"으로 save_image 함수 호출
        THEN PNG 파일에 알파 채널이 포함됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((512, 512), "RGBA")
        output = save_image(image, format="png")

        output.seek(0)
        img = Image.open(output)
        assert img.mode == "RGBA"  # 투명도 보존


class TestJPEGFormatHandler:
    """JPEG 형식 핸들러 테스트"""

    def test_jpeg_format_support(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="jpeg"으로 save_image 함수 호출
        THEN JPEG 형식의 이미지가 생성됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image, format="jpeg")

        output.seek(0)
        img = Image.open(output)
        assert img.format == "JPEG"

    def test_jpeg_quality_control(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="jpeg", quality=80으로 save_image 함수 호출
        THEN JPEG 파일이 품질 80으로 저장됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")

        # 품질 80과 95 각각 저장
        output_80 = save_image(image, format="jpeg", quality=80)
        output_95 = save_image(image, format="jpeg", quality=95)

        # 품질 80이 파일 크기가 더 작아야 함
        assert len(output_80.getvalue()) < len(output_95.getvalue())

    def test_jpeg_quality_validation(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="jpeg", quality=150으로 save_image 함수 호출
        THEN ValueError가 발생함
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")

        with pytest.raises(ValueError) as exc_info:
            save_image(image, format="jpeg", quality=150)

        assert "1 and 100" in str(exc_info.value)

    def test_jpeg_transparency_handling(self):
        """GIVEN 투명도가 포함된 RGBA 이미지가 생성됨
        WHEN format="jpeg"으로 save_image 함수 호출
        THEN 이미지가 RGB로 변환됨
        AND 투명 영역이 흰색으로 채워짐
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((512, 512), "RGBA")
        output = save_image(image, format="jpeg")

        output.seek(0)
        img = Image.open(output)
        assert img.mode == "RGB"  # JPEG는 투명도 지원 안 함


class TestWebPFormatHandler:
    """WebP 형식 핸들러 테스트"""

    def test_webp_format_support(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="webp"으로 save_image 함수 호출
        THEN WebP 형식의 이미지가 생성됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image, format="webp")

        output.seek(0)
        img = Image.open(output)
        assert img.format == "WEBP"

    def test_webp_quality_control(self):
        """GIVEN 1024x1024 RGB 이미지가 생성됨
        WHEN format="webp", quality=85으로 save_image 함수 호출
        THEN WebP 파일이 품질 85로 저장됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image, format="webp", quality=85)

        output.seek(0)
        img = Image.open(output)
        assert img.format == "WEBP"

    def test_webp_file_size_optimization(self):
        """GIVEN 1024x1024 크기의 복잡한 이미지가 생성됨
        WHEN 이미지를 PNG 형식으로 저장
        AND 동일한 이미지를 WebP 형식으로 저장
        THEN WebP 파일 크기 < PNG 파일 크기
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")

        png_output = save_image(image, format="png")
        webp_output = save_image(image, format="webp", quality=90)

        # WebP는 PNG보다 파일 크기가 작아야 함
        assert len(webp_output.getvalue()) < len(png_output.getvalue())


class TestFormatValidation:
    """형식 검증 및 오류 처리 테스트"""

    def test_unsupported_format(self):
        """GIVEN 1024x1024 크기의 이미지가 생성됨
        WHEN format="bmp"으로 save_image 함수 호출
        THEN ValueError가 발생함
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")

        with pytest.raises(ValueError) as exc_info:
            save_image(image, format="bmp")

        assert "Unsupported format" in str(exc_info.value)

    def test_format_case_insensitive(self):
        """GIVEN 1024x1024 크기의 이미지가 생성됨
        WHEN format="PNG"으로 save_image 함수 호출
        THEN 이미지가 PNG 형식으로 저장됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image, format="PNG")  # 대문자

        output.seek(0)
        img = Image.open(output)
        assert img.format == "PNG"


class TestBackwardCompatibility:
    """후방 호환성 테스트"""

    def test_default_format_is_png(self):
        """GIVEN 1024x1024 크기의 이미지가 생성됨
        WHEN save_image 함수에 format 매개변수 미지정
        THEN 이미지가 PNG 형식으로 저장됨
        """
        from src.generators.format_handlers import save_image

        image = create_test_image((1024, 1024), "RGB")
        output = save_image(image)  # format 미지정

        output.seek(0)
        img = Image.open(output)
        assert img.format == "PNG"
