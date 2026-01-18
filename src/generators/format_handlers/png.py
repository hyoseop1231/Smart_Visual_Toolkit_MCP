"""
PNG 형식 핸들러

무손실 PNG 형식으로 이미지를 저장합니다. 투명도를 지원합니다.
"""

from PIL import Image
from io import BytesIO
from typing import Any

from .base import ImageFormatHandler


class PNGHandler(ImageFormatHandler):
    """
    PNG 형식 핸들러

    특징:
    - 무손실 압축
    - 투명도(Alpha 채널) 지원
    - 최적화 옵션 지원
    """

    def save(
        self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs: Any
    ) -> None:
        """
        이미지를 PNG 형식으로 저장합니다.

        PNG는 무손실 형식이므로 quality 매개변수는 무시되지만,
        API 호환성을 위해 받아둡니다.

        Args:
            image: PIL 이미지 객체
            output: 출력 BytesIO 버퍼
            quality: PNG에서는 무시됨 (호환성 유지용)
            **kwargs: 추가 파라미터 (optimize=True 등)
        """
        # PNG 최적화 옵션 적용
        image.save(output, format="PNG", optimize=True)


def create_png_handler() -> PNGHandler:
    """PNG 핸들러 인스턴스 생성 팩토리 함수"""
    return PNGHandler()
