"""
이미지 갤러리 모델

ImageMetadata 데이터클래스와 관련 헬퍼 함수를 제공합니다.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class ImageMetadata:
    """
    이미지 메타데이터 데이터 클래스

    이미지 생성 정보와 관련 메타데이터를 저장합니다.

    Attributes:
        id: 고유 이미지 ID
        filename: 파일 이름
        filepath: 절대 파일 경로
        thumbnail_path: 썸네일 경로 (없으면 None)
        created_at: 생성 일시 (ISO 8601 형식)
        prompt: 이미지 생성 프롬프트
        style: 사용된 스타일
        aspect_ratio: 이미지 비율
        resolution: 이미지 해상도 (예: "1024x576")
        format: 이미지 형식 (png, jpeg, webp)
        size_bytes: 파일 크기 (바이트)
        generation_params: 생성 파라미터 딕셔너리
    """

    id: str
    filename: str
    filepath: str
    thumbnail_path: Optional[str]
    created_at: str
    prompt: str
    style: str
    aspect_ratio: str
    resolution: str
    format: str
    size_bytes: int
    generation_params: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """
        메타데이터를 딕셔너리로 변환합니다.

        Returns:
            메타데이터의 딕셔너리 표현
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageMetadata":
        """
        딕셔너리에서 메타데이터 인스턴스를 생성합니다.

        Args:
            data: 메타데이터 딕셔너리

        Returns:
            ImageMetadata 인스턴스
        """
        return cls(**data)

    def get_file_size_mb(self) -> float:
        """
        파일 크기를 메가바이트 단위로 반환합니다.

        Returns:
            파일 크기 (MB)
        """
        return self.size_bytes / (1024 * 1024)

    def get_created_datetime(self) -> datetime:
        """
        생성 일시를 datetime 객체로 반환합니다.

        Returns:
            생성 일시 datetime 객체
        """
        return datetime.fromisoformat(self.created_at)

    def is_expired(self, days: int) -> bool:
        """
        이미지가 지정된 일수보다 오래되었는지 확인합니다.

        Args:
            days: 기준 일수

        Returns:
            True면 이미지가 기준일수보다 오래됨
        """
        created = self.get_created_datetime()
        delta = datetime.now() - created
        return delta.days >= days
