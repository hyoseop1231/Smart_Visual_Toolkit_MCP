"""
템플릿 저장소 (TemplateRepository)

CRUD 연산을 제공하는 템플릿 저장소 계층입니다.
src/gallery/image_gallery.py의 패턴을 따라 설계되었습니다.

SPEC-TEMPLATE-001: 템플릿 관리 시스템의 핵심 데이터 액세스 계층
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import ContentType, TemplateMetadata

logger = logging.getLogger(__name__)


class TemplateRepository:
    """
    템플릿 저장소

    템플릿 메타데이터를 관리하고 검색, 필터링 기능을 제공합니다.

    Attributes:
        data_path: 템플릿 데이터 파일 경로
        auto_save: 자동 저장 활성화 여부
    """

    # 파일 잠금 (동시성 제어)
    _lock = threading.Lock()

    def __init__(self, data_path: Path, auto_save: bool = True):
        """
        템플릿 저장소를 초기화합니다.

        Args:
            data_path: 템플릿 데이터 파일 경로
            auto_save: 변경 시 자동 저장 여부 (기본값: True)
        """
        self.data_path = Path(data_path)
        self.auto_save = auto_save

        # 메타데이터 로드
        self._templates: Dict[str, TemplateMetadata] = {}
        self._load_data()

    def _load_data(self) -> None:
        """템플릿 데이터 파일을 로드합니다."""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._templates = {
                    tmpl["template_id"]: TemplateMetadata.from_dict(tmpl)
                    for tmpl in data.get("templates", [])
                }

                logger.info(f"템플릿 데이터 로드 완료: {len(self._templates)}개 템플릿")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"템플릿 데이터 로드 실패: {e}")
                self._templates = {}
        else:
            self._templates = {}
            self._save_data()  # 빈 데이터 파일 생성

    def _save_data(self) -> None:
        """템플릿 데이터를 저장합니다."""
        with self._lock:
            data = {
                "templates": [tmpl.to_dict() for tmpl in self._templates.values()],
                "last_updated": TemplateMetadata.__name__,
                "total_count": len(self._templates),
            }

            # 디렉토리가 없으면 생성
            self.data_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def register_template(self, metadata: TemplateMetadata) -> None:
        """
        새로운 템플릿을 등록합니다.

        Args:
            metadata: 등록할 템플릿 메타데이터
        """
        with self._lock:
            # 메타데이터 등록
            self._templates[metadata.template_id] = metadata

            if self.auto_save:
                self._save_data()

            logger.info(f"템플릿 등록 완료: {metadata.template_id}")

    def get_template(self, template_id: str) -> Optional[TemplateMetadata]:
        """
        특정 템플릿을 조회합니다.

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 메타데이터 또는 None (존재하지 않는 경우)
        """
        return self._templates.get(template_id)

    def list_templates(
        self,
        content_type: Optional[ContentType] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> List[TemplateMetadata]:
        """
        템플릿 목록을 반환합니다.

        Args:
            content_type: 필터링할 콘텐츠 타입 (None인 경우 모든 타입)
            limit: 반환할 최대 템플릿 수
            offset: 건너뛸 템플릿 수 (페이지네이션용)
            sort_by: 정렬 기준 (name, created_at, content_type)
            sort_order: 정렬 순서 (asc, desc)

        Returns:
            템플릿 메타데이터 목록
        """
        # 유효하지 않은 정렬 필드 처리
        valid_sort_fields = {"name", "created_at", "content_type"}
        if sort_by not in valid_sort_fields:
            logger.warning(f"잘못된 정렬 필드: {sort_by}, 기본값 사용")
            sort_by = "name"

        # 메타데이터 정렬 키 매핑
        sort_key_map = {
            "name": lambda tmpl: tmpl.name.lower(),
            "created_at": lambda tmpl: tmpl.get_created_datetime(),
            "content_type": lambda tmpl: tmpl.content_type.value,
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map["name"])

        # 목록 필터링
        results = list(self._templates.values())

        if content_type:
            results = [tmpl for tmpl in results if tmpl.content_type == content_type]

        # 목록 정렬
        sorted_templates = sorted(
            results,
            key=sort_key,
            reverse=(sort_order == "desc"),
        )

        # 페이지네이션 적용
        paginated_templates = sorted_templates[offset : offset + limit]

        return paginated_templates

    def search_templates(self, filters: Dict[str, Any]) -> List[TemplateMetadata]:
        """
        조건에 맞는 템플릿을 검색합니다.

        Args:
            filters: 검색 필터 딕셔너리
                - content_type: 콘텐츠 타입 필터
                - keyword: 키워드 검색 (이름, 설명, 태그)
                - tag: 태그 필터
                - style_name: 레거시 스타일 이름 필터
                - supports_format: 지원하는 형식 필터

        Returns:
            필터링된 템플릿 메타데이터 목록
        """
        results = list(self._templates.values())

        # 콘텐츠 타입 필터
        if "content_type" in filters and filters["content_type"]:
            ct = filters["content_type"]
            if isinstance(ct, str):
                ct = ContentType.from_string(ct)
            results = [tmpl for tmpl in results if tmpl.content_type == ct]

        # 키워드 검색 (이름, 설명, 태그)
        if "keyword" in filters and filters["keyword"]:
            keyword = filters["keyword"].lower()
            results = [
                tmpl
                for tmpl in results
                if (
                    keyword in tmpl.name.lower()
                    or keyword in tmpl.description.lower()
                    or keyword in tmpl.keywords.lower()
                    or any(keyword in tag.lower() for tag in tmpl.tags)
                )
            ]

        # 태그 필터
        if "tag" in filters and filters["tag"]:
            tag = filters["tag"]
            results = [tmpl for tmpl in results if tmpl.has_tag(tag)]

        # 레거시 스타일 이름 필터
        if "style_name" in filters and filters["style_name"]:
            style_name = filters["style_name"]
            results = [
                tmpl
                for tmpl in results
                if tmpl.style_name and tmpl.style_name.lower() == style_name.lower()
            ]

        # 형식 지원 필터
        if "supports_format" in filters and filters["supports_format"]:
            format = filters["supports_format"]
            results = [tmpl for tmpl in results if tmpl.supports_format(format)]

        return results

    def update_template(
        self, template_id: str, updates: Dict[str, Any]
    ) -> Optional[TemplateMetadata]:
        """
        템플릿을 업데이트합니다.

        Args:
            template_id: 템플릿 ID
            updates: 업데이트할 필드 딕셔너리

        Returns:
            업데이트된 템플릿 메타데이터 또는 None (존재하지 않는 경우)
        """
        with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return None

            # 업데이트 가능한 필드만 적용
            updatable_fields = {
                "name",
                "keywords",
                "description",
                "tags",
                "aspect_ratios",
                "formats",
                "version",
                "metadata",
            }

            for key, value in updates.items():
                if key in updatable_fields and hasattr(template, key):
                    setattr(template, key, value)

            # 타임스탬프 업데이트
            template.update_timestamp()

            if self.auto_save:
                self._save_data()

            logger.info(f"템플릿 업데이트 완료: {template_id}")
            return template

    def delete_template(self, template_id: str) -> bool:
        """
        템플릿을 삭제합니다.

        Args:
            template_id: 템플릿 ID

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if template_id in self._templates:
                del self._templates[template_id]

                if self.auto_save:
                    self._save_data()

                logger.info(f"템플릿 삭제 완료: {template_id}")
                return True

            return False

    def count_templates(self, content_type: Optional[ContentType] = None) -> int:
        """
        템플릿 수를 반환합니다.

        Args:
            content_type: 필터링할 콘텐츠 타입 (None인 경우 전체)

        Returns:
            템플릿 수
        """
        if content_type:
            return sum(
                1 for tmpl in self._templates.values() if tmpl.content_type == content_type
            )
        return len(self._templates)

    def get_all_content_types(self) -> List[ContentType]:
        """
        저장된 모든 콘텐츠 타입을 반환합니다.

        Returns:
            고유한 콘텐츠 타입 목록
        """
        types = set(tmpl.content_type for tmpl in self._templates.values())
        return sorted(types, key=lambda ct: ct.value)
