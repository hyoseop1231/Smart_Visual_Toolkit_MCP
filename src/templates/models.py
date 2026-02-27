"""
템플릿 데이터 모델

ContentType enum과 TemplateMetadata 데이터클래스를 제공합니다.
이 모듈은 src/gallery/models.py의 패턴을 따라 설계되었습니다.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """
    콘텐츠 타입 열거형

    지원하는 콘텐츠 생성 타입을 정의합니다.
    """

    IMAGE = "image"
    DOC = "doc"
    PPT = "ppt"
    EXCEL = "excel"

    @classmethod
    def from_string(cls, value: str) -> "ContentType":
        """
        문자열에서 ContentType을 변환합니다.

        Args:
            value: 콘텐츠 타입 문자열

        Returns:
            ContentType 인스턴스

        Raises:
            ValueError: 지원하지 않는 타입인 경우
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = [t.value for t in cls]
            raise ValueError(
                f"Invalid content type: '{value}'. Must be one of {valid}"
            )


@dataclass
class TemplateMetadata:
    """
    템플릿 메타데이터 데이터 클래스

    템플릿 정보와 관련 메타데이터를 저장합니다.
    ImageMetadata와 유사한 구조로 설계되었습니다.

    Attributes:
        template_id: 고유 템플릿 ID
        name: 템플릿 이름
        content_type: 콘텐츠 타입 (ContentType)
        keywords: 스타일 키워드 (프롬프트 강화용)
        description: 템플릿 설명
        style_name: 레거시 스타일 이름 (하위 호환성용)
        tags: 검색용 태그 목록
        aspect_ratios: 지원하는 화면 비율 목록 (image 전용)
        formats: 지원하는 출력 형식 목록
        created_at: 생성 일시 (ISO 8601)
        updated_at: 수정 일시 (ISO 8601)
        version: 템플릿 버전
        metadata: 추가 메타데이터 딕셔너리
    """

    template_id: str
    name: str
    content_type: ContentType
    keywords: str
    description: str = ""
    style_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    aspect_ratios: List[str] = field(default_factory=lambda: ["16:9"])
    formats: List[str] = field(default_factory=lambda: ["png"])
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """초기화 후 처리"""
        # created_at이 비어있으면 현재 시간으로 설정
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

        # updated_at이 비어있으면 created_at과 동일하게 설정
        if not self.updated_at:
            self.updated_at = self.created_at

        # content_type이 문자열이면 enum으로 변환
        if isinstance(self.content_type, str):
            self.content_type = ContentType.from_string(self.content_type)

    def to_dict(self) -> Dict[str, Any]:
        """
        메타데이터를 딕셔너리로 변환합니다.

        Returns:
            메타데이터의 딕셔너리 표현
        """
        data = asdict(self)
        # ContentType enum을 문자열로 변환
        if isinstance(self.content_type, ContentType):
            data["content_type"] = self.content_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """
        딕셔너리에서 메타데이터 인스턴스를 생성합니다.

        Args:
            data: 메타데이터 딕셔너리

        Returns:
            TemplateMetadata 인스턴스
        """
        # 깊은 복사로 원본 데이터 보호
        data_copy = data.copy()

        # tags와 aspect_ratios, formats가 없으면 빈 리스트로
        data_copy.setdefault("tags", [])
        data_copy.setdefault("aspect_ratios", ["16:9"])
        data_copy.setdefault("formats", ["png"])
        data_copy.setdefault("metadata", {})

        return cls(**data_copy)

    def supports_aspect_ratio(self, ratio: str) -> bool:
        """
        특정 화면 비율을 지원하는지 확인합니다.

        Args:
            ratio: 화면 비율 (예: "16:9")

        Returns:
            지원 여부
        """
        return ratio in self.aspect_ratios

    def supports_format(self, format: str) -> bool:
        """
        특정 형식을 지원하는지 확인합니다.

        Args:
            format: 출력 형식 (예: "png")

        Returns:
            지원 여부
        """
        return format.lower() in [f.lower() for f in self.formats]

    def has_tag(self, tag: str) -> bool:
        """
        특정 태그를 가지고 있는지 확인합니다.

        Args:
            tag: 태그

        Returns:
            태그 존재 여부
        """
        return tag.lower() in [t.lower() for t in self.tags]

    def get_created_datetime(self) -> datetime:
        """
        생성 일시를 datetime 객체로 반환합니다.

        Returns:
            생성 일시 datetime 객체
        """
        return datetime.fromisoformat(self.created_at)

    def get_updated_datetime(self) -> datetime:
        """
        수정 일시를 datetime 객체로 반환합니다.

        Returns:
            수정 일시 datetime 객체
        """
        return datetime.fromisoformat(self.updated_at)

    def is_image_template(self) -> bool:
        """이미지 템플릿인지 확인합니다."""
        return self.content_type == ContentType.IMAGE

    def is_document_template(self) -> bool:
        """문서 템플릿인지 확인합니다 (DOC, PPT, EXCEL)."""
        return self.content_type in {
            ContentType.DOC,
            ContentType.PPT,
            ContentType.EXCEL,
        }

    def get_legacy_style_name(self) -> str:
        """
        레거시 스타일 이름을 반환합니다.

        하위 호환성을 위해 style_name이 있으면 반환하고,
        없으면 template_id를 사용합니다.

        Returns:
            레거시 스타일 이름
        """
        return self.style_name if self.style_name else self.template_id

    def update_timestamp(self) -> None:
        """updated_at을 현재 시간으로 업데이트합니다."""
        self.updated_at = datetime.now().isoformat()
