"""
이미지 형식 변환기 통합 모듈

save_image() 함수를 제공하여 다양한 이미지 형식으로 저장하는 기능을 통합합니다.
"""

from io import BytesIO

from PIL import Image

from .base import ImageFormatHandler
from .png import PNGHandler
from .jpeg import JPEGHandler
from .webp import WebPHandler


# 형식 핸들러 레지스트리
FORMAT_HANDLERS: dict[str, ImageFormatHandler] = {
    "png": PNGHandler(),
    "jpg": JPEGHandler(),
    "jpeg": JPEGHandler(),
    "webp": WebPHandler(),
}


def save_image(
    image: Image.Image,
    format: str = "png",
    quality: int = 95,
    output_path: str | None = None,
) -> BytesIO:
    """
    지정된 형식으로 이미지를 저장합니다.

    Args:
        image: PIL 이미지 객체
        format: 출력 형식 (png, jpeg, jpg, webp) - 기본값: 'png'
        quality: JPEG/WebP 품질 (1-100) - 기본값: 95
        output_path: 저장 경로 (None인 경우 BytesIO만 반환)

    Returns:
        BytesIO: 이미지 데이터가 담긴 BytesIO 객체

    Raises:
        ValueError: 지원하지 않는 형식이거나 품질 범위가 잘못된 경우

    Examples:
        >>> from PIL import Image
        >>> image = Image.new('RGB', (100, 100), color='red')
        >>> output = save_image(image, format='webp', quality=90)
        >>> with open('output.webp', 'wb') as f:
        ...     f.write(output.getvalue())
    """
    # 대소문자 구분 없이 처리
    format = format.lower()

    # 지원하지 않는 형식 검증
    if format not in FORMAT_HANDLERS:
        supported_formats = ", ".join(FORMAT_HANDLERS.keys())
        raise ValueError(
            f"Unsupported format: {format}. Supported formats: {supported_formats}"
        )

    # 핸들러 가져오기
    handler = FORMAT_HANDLERS[format]

    # BytesIO 생성
    output = BytesIO()

    # 형식별 저장 수행
    handler.save(image, output, quality=quality)

    # 파일로도 저장하는 경우
    if output_path:
        output.seek(0)
        with open(output_path, "wb") as f:
            f.write(output.getvalue())

    # 포인터를 시작으로 이동하여后续 읽기 가능하게 함
    output.seek(0)

    return output
