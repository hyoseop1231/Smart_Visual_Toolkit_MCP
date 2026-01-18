"""
JPEG 형식 핸들러

JPEG 형식으로 이미지를 저장합니다. 투명도 지원이 제한됩니다.
"""

from PIL import Image
from io import BytesIO
from typing import Any

from .base import ImageFormatHandler


class JPEGHandler(ImageFormatHandler):
    """
    JPEG 형식 핸들러

    특징:
    - 손실 압축
    - 투명도 미지원 (RGBA → RGB 변환 필요)
    - 품질 매개변수 지원 (1-100)
    """

    def save(
        self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs: Any
    ) -> None:
        """
        이미지를 JPEG 형식으로 저장합니다.

        RGBA/PA 모드의 이미지는 RGB로 변환되며, 투명 영역은 흰색으로 채워집니다.

        Args:
            image: PIL 이미지 객체
            output: 출력 BytesIO 버퍼
            quality: JPEG 품질 (1-100, 높을수록 품질 좋음)
            **kwargs: 추가 파라미터
        """
        # 품질 매개변수 검증
        self.validate_quality(quality)

        # JPEG는 투명도를 지원하지 않으므로 RGB로 변환
        if image.mode in ("RGBA", "LA", "P"):
            # 흰색 배경 생성
            background = Image.new("RGB", image.size, (255, 255, 255))

            # 투명도 채널이 있는 경우 마스크로 사용
            if image.mode == "RGBA":
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)

            image = background

        # JPEG 저장
        image.save(output, format="JPEG", quality=quality)


def create_jpeg_handler() -> JPEGHandler:
    """JPEG 핸들러 인스턴스 생성 팩토리 함수"""
    return JPEGHandler()
