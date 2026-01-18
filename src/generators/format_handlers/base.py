"""
이미지 형식 핸들러 기본 클래스 (ABC)

Strategy Pattern의 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO
from typing import Any


class ImageFormatHandler(ABC):
    """
    이미지 형식 핸들러 추상 기본 클래스

    모든 형식 핸들러는 이 클래스를 상속하여 save() 메서드를 구현해야 합니다.
    """

    @abstractmethod
    def save(
        self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs: Any
    ) -> None:
        """
        이미지를 지정된 형식으로 저장합니다.

        Args:
            image: PIL 이미지 객체
            output: 출력 BytesIO 버퍼
            quality: 이미지 품질 (1-100)
            **kwargs: 형식별 추가 파라미터

        Raises:
            ValueError: 품질 매개변수가 유효하지 않은 경우
        """
        pass

    def validate_quality(self, quality: int) -> None:
        """
        품질 매개변수를 검증합니다.

        Args:
            quality: 검증할 품질 값

        Raises:
            ValueError: 품질이 1-100 범위를 벗어난 경우
        """
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            raise ValueError(
                f"Quality must be an integer between 1 and 100, got {quality}"
            )
