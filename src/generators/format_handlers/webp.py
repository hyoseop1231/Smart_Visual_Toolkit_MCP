"""
WebP 형식 핸들러

WebP 형식으로 이미지를 저장합니다. 투명도를 지원합니다.
"""

from PIL import Image
from io import BytesIO
from typing import Any

from .base import ImageFormatHandler


class WebPHandler(ImageFormatHandler):
    """
    WebP 형식 핸들러

    특징:
    - 현대적인 형식으로 PNG보다 작은 파일 크기
    - 투명도(Alpha 채널) 지원
    - 품질 매개변수 지원 (1-100)
    - 애니메이션 지원 (선택적)
    """

    def save(
        self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs: Any
    ) -> None:
        """
        이미지를 WebP 형식으로 저장합니다.

        Args:
            image: PIL 이미지 객체
            output: 출력 BytesIO 버퍼
            quality: WebP 품질 (1-100, 높을수록 품질 좋음)
            **kwargs: 추가 파라미터 (lossless, method 등)
        """
        # 품질 매개변수 검증
        self.validate_quality(quality)

        # WebP 저장 (투명도 자동 지원)
        image.save(output, format="WebP", quality=quality)


def create_webp_handler() -> WebPHandler:
    """WebP 핸들러 인스턴스 생성 팩토리 함수"""
    return WebPHandler()
