"""
템플릿 검증 프레임워크

TemplateMetadata의 유효성을 검증하는 기능을 제공합니다.
TRUST 5 품질 프레임워크의 Testability와 Security 원칙을 따릅니다.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import ContentType, TemplateMetadata

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """
    검증 오류 정보

    Attributes:
        field: 오류가 발생한 필드
        message: 오류 메시지
        severity: 오류 심각도 (error, warning)
    """

    field: str
    message: str
    severity: str = "error"  # 'error' or 'warning'


@dataclass
class ValidationResult:
    """
    검증 결과

    Attributes:
        valid: 전체 유효성 (error가 없으면 True)
        errors: 검증 오류 목록
        warnings: 검증 경고 목록
    """

    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str) -> None:
        """오류를 추가합니다."""
        self.errors.append(ValidationError(field=field, message=message, severity="error"))
        self.valid = False

    def add_warning(self, field: str, message: str) -> None:
        """경고를 추가합니다."""
        self.warnings.append(ValidationError(field=field, message=message, severity="warning"))

    def get_error_messages(self) -> List[str]:
        """모든 오류 메시지를 반환합니다."""
        return [f"{err.field}: {err.message}" for err in self.errors]

    def get_warning_messages(self) -> List[str]:
        """모든 경고 메시지를 반환합니다."""
        return [f"{warn.field}: {warn.message}" for warn in self.warnings]


class TemplateValidator:
    """
    템플릿 검증기

    TemplateMetadata의 유효성을 검증합니다.
    """

    # 유효한 화면 비율 목록
    VALID_ASPECT_RATIOS = {
        "1:1",
        "16:9",
        "9:16",
        "4:3",
        "3:4",
        "21:9",  # SPEC-IMG-003: Ultra-Wide
        "2:3",  # Portrait SNS
        "3:2",  # Photo DSLR
        "5:4",  # Large Format
    }

    # 유효한 이미지 형식
    VALID_IMAGE_FORMATS = {"png", "jpeg", "jpg", "webp"}

    # 유효한 문서 형식
    VALID_DOC_FORMATS = {"pdf", "docx"}

    # 유효한 프레젠테이션 형식
    VALID_PPT_FORMATS = {"pptx", "pdf"}

    # 유효한 스프레드시트 형식
    VALID_EXCEL_FORMATS = {"xlsx", "csv", "pdf"}

    # template_id 유효성 패턴 (영문, 숫자, 언더스코어, 하이픈)
    TEMPLATE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # 버전 번호 패턴 (semver)
    VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

    def __init__(self, strict_mode: bool = True):
        """
        검증기를 초기화합니다.

        Args:
            strict_mode: 엄격한 모드 (경고도 오류로 처리)
        """
        self.strict_mode = strict_mode

    def validate(self, metadata: TemplateMetadata) -> ValidationResult:
        """
        템플릿 메타데이터를 종합 검증합니다.

        Args:
            metadata: 검증할 템플릿 메타데이터

        Returns:
            ValidationResult 인스턴스
        """
        result = ValidationResult(valid=True)

        # 1. 기본 필드 검증
        self._validate_basic_fields(metadata, result)

        # 2. 콘텐츠 타입별 검증
        self._validate_content_type_specific(metadata, result)

        # 3. 형식 검증
        self._validate_formats(metadata, result)

        # 4. 화면 비율 검증 (이미지 템플릿만)
        if metadata.is_image_template():
            self._validate_aspect_ratios(metadata, result)

        # 5. 날짜 검증
        self._validate_dates(metadata, result)

        # 6. 버전 검증
        self._validate_version(metadata, result)

        # 7. 태그 검증
        self._validate_tags(metadata, result)

        # 엄격 모드에서는 경고를 오류로 변환
        if self.strict_mode and result.warnings:
            result.errors.extend(result.warnings)
            result.warnings.clear()
            result.valid = len(result.errors) == 0

        if not result.valid:
            logger.warning(f"템플릿 검증 실패: {metadata.template_id}")
            for msg in result.get_error_messages():
                logger.warning(f"  - {msg}")

        return result

    def _validate_basic_fields(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """기본 필드를 검증합니다."""
        # template_id 검증
        if not metadata.template_id:
            result.add_error("template_id", "template_id는 필수 항목입니다.")
        elif not self.TEMPLATE_ID_PATTERN.match(metadata.template_id):
            result.add_error(
                "template_id",
                "template_id는 영문, 숫자, 언더스코어(_), 하이픈(-)만 포함할 수 있습니다.",
            )

        # name 검증
        if not metadata.name or not metadata.name.strip():
            result.add_error("name", "name은 필수 항목입니다.")
        elif len(metadata.name) > 100:
            result.add_warning("name", "name이 100자를 초과했습니다.")

        # keywords 검증
        if not metadata.keywords or not metadata.keywords.strip():
            result.add_error("keywords", "keywords는 필수 항목입니다.")
        elif len(metadata.keywords) > 1000:
            result.add_warning("keywords", "keywords가 1000자를 초과했습니다.")

        # description 검증
        if len(metadata.description) > 500:
            result.add_warning("description", "description이 500자를 초과했습니다.")

    def _validate_content_type_specific(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """콘텐츠 타입별 검증을 수행합니다."""
        ct = metadata.content_type

        # 이미지 템플릿의 경우
        if ct == ContentType.IMAGE:
            if not metadata.aspect_ratios:
                result.add_error("aspect_ratios", "이미지 템플릿은 aspect_ratios가 필요합니다.")

        # 문서 템플릿의 경우
        elif ct in {ContentType.DOC, ContentType.PPT, ContentType.EXCEL}:
            # 문서 템플릿은 aspect_ratios가 필요 없음
            if metadata.aspect_ratios:
                result.add_warning(
                    "aspect_ratios",
                    f"{ct.value} 템플릿에는 aspect_ratios가 필요하지 않습니다.",
                )

    def _validate_formats(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """형식을 검증합니다."""
        if not metadata.formats:
            result.add_error("formats", "formats는 필수 항목입니다.")
            return

        ct = metadata.content_type
        valid_formats = set()

        if ct == ContentType.IMAGE:
            valid_formats = self.VALID_IMAGE_FORMATS
        elif ct == ContentType.DOC:
            valid_formats = self.VALID_DOC_FORMATS
        elif ct == ContentType.PPT:
            valid_formats = self.VALID_PPT_FORMATS
        elif ct == ContentType.EXCEL:
            valid_formats = self.VALID_EXCEL_FORMATS

        invalid_formats = [f for f in metadata.formats if f.lower() not in valid_formats]

        if invalid_formats:
            result.add_error(
                "formats",
                f"유효하지 않은 형식: {invalid_formats}. "
                f"{ct.value} 템플릿은 {sorted(valid_formats)} 형식만 지원합니다.",
            )

    def _validate_aspect_ratios(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """화면 비율을 검증합니다."""
        if not metadata.aspect_ratios:
            return

        invalid_ratios = [
            ar for ar in metadata.aspect_ratios if ar not in self.VALID_ASPECT_RATIOS
        ]

        if invalid_ratios:
            result.add_error(
                "aspect_ratios",
                f"유효하지 않은 화면 비율: {invalid_ratios}. "
                f"지원되는 비율: {sorted(self.VALID_ASPECT_RATIOS)}",
            )

    def _validate_dates(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """날짜를 검증합니다."""
        try:
            created_dt = metadata.get_created_datetime()
            updated_dt = metadata.get_updated_datetime()

            # updated_at이 created_at보다 빠르면 경고
            if updated_dt < created_dt:
                result.add_warning(
                    "updated_at", "updated_at이 created_at보다 빠릅니다."
                )

            # 미래 날짜 검증
            now = datetime.now()
            if updated_dt > now:
                result.add_warning("updated_at", "updated_at이 미래 시간입니다.")

        except ValueError as e:
            result.add_error("created_at/updated_at", f"잘못된 날짜 형식: {e}")

    def _validate_version(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """버전을 검증합니다."""
        if not metadata.version:
            result.add_warning("version", "version이 비어있습니다.")
            return

        if not self.VERSION_PATTERN.match(metadata.version):
            result.add_warning(
                "version",
                "version은 semver 형식이어야 합니다 (예: 1.0.0).",
            )

    def _validate_tags(
        self, metadata: TemplateMetadata, result: ValidationResult
    ) -> None:
        """태그를 검증합니다."""
        if not metadata.tags:
            return

        # 태그 수 검증
        if len(metadata.tags) > 20:
            result.add_warning("tags", "태그가 20개를 초과했습니다.")

        # 태그 형식 검증
        invalid_tags = [
            tag for tag in metadata.tags if not tag or not tag.strip() or len(tag) > 50
        ]

        if invalid_tags:
            result.add_warning(
                "tags",
                f"유효하지 않은 태그: {invalid_tags}. "
                "태그는 1-50자 사이여야 합니다.",
            )
