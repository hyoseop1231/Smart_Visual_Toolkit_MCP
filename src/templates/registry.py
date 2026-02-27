"""
템플릿 레지스트리 (TemplateRegistry)

싱글톤 패턴과 LRU 캐시를 사용하는 템플릿 관리 시스템입니다.
src/generators/cache.py의 ImageCache 패턴을 재사용합니다.

SPEC-TEMPLATE-001: 템플릿 관리 시스템의 핵심 레지스트리 계층
"""

import logging
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional, List, Any

from .models import ContentType, TemplateMetadata
from .repository import TemplateRepository
from .validators import TemplateValidator, ValidationResult

logger = logging.getLogger(__name__)


# 전역 레지스트리 인스턴스
_registry_instance: Optional["TemplateRegistry"] = None
_registry_lock = threading.Lock()


class TemplateRegistry:
    """
    템플릿 레지스트리 (싱글톤)

    특징:
    - 싱글톤 패턴 (전역 단일 인스턴스)
    - LRU 캐시로 빠른 템플릿 조회
    - TemplateRepository와 통합
    - TemplateValidator로 자동 검증
    - 스레드 안전성 보장

    Attributes:
        repository: 템플릿 저장소
        validator: 템플릿 검증기
        cache_size: LRU 캐시 크기
    """

    def __init__(self, data_path: Path, cache_size: int = 100):
        """
        템플릿 레지스트리를 초기화합니다.

        Args:
            data_path: 템플릿 데이터 파일 경로
            cache_size: LRU 캐시 크기 (기본값: 100)
        """
        self.repository = TemplateRepository(data_path, auto_save=True)
        self.validator = TemplateValidator(strict_mode=False)
        self.cache_size = cache_size

        # LRU 캐시 (template_id -> TemplateMetadata)
        self._cache: OrderedDict[str, TemplateMetadata] = OrderedDict()
        self._cache_lock = threading.RLock()

        # 기본 템플릿 ID
        self._default_template_id: Optional[str] = None

        logger.info(f"TemplateRegistry 초기화 완료 (cache_size={cache_size})")

    @classmethod
    def get_instance(cls, data_path: Optional[Path] = None) -> "TemplateRegistry":
        """
        싱글톤 인스턴스를 반환합니다.

        Args:
            data_path: 템플릿 데이터 파일 경로 (최초 초기화 시에만 필요)

        Returns:
            TemplateRegistry 싱글톤 인스턴스

        Raises:
            RuntimeError: 최초 호출 시 data_path가 없는 경우
        """
        global _registry_instance

        with _registry_lock:
            if _registry_instance is None:
                if data_path is None:
                    raise RuntimeError(
                        "TemplateRegistry 초기화에 data_path가 필요합니다."
                    )
                _registry_instance = cls(data_path)
                logger.info("TemplateRegistry 싱글톤 인스턴스 생성 완료")

            return _registry_instance

    def _cache_get(self, template_id: str) -> Optional[TemplateMetadata]:
        """
        캐시에서 템플릿을 조회합니다.

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 메타데이터 또는 None
        """
        with self._cache_lock:
            if template_id in self._cache:
                # LRU 순서 업데이트 (가장 최근 사용으로 이동)
                self._cache.move_to_end(template_id)
                return self._cache[template_id]
            return None

    def _cache_set(self, template: TemplateMetadata) -> None:
        """
        캐시에 템플릿을 저장합니다.

        Args:
            template: 저장할 템플릿 메타데이터
        """
        with self._cache_lock:
            template_id = template.template_id

            # 기존 항목이 있으면 삭제 (업데이트를 위해)
            if template_id in self._cache:
                del self._cache[template_id]

            # 용량 초과 시 가장 오래된 항목 제거
            while len(self._cache) >= self.cache_size:
                self._cache.popitem(last=False)

            # 새 항목 추가
            self._cache[template_id] = template

    def _cache_invalidate(self, template_id: str) -> None:
        """
        특정 템플릿의 캐시를 무효화합니다.

        Args:
            template_id: 무효화할 템플릿 ID
        """
        with self._cache_lock:
            self._cache.pop(template_id, None)

    def _cache_clear(self) -> None:
        """전체 캐시를 초기화합니다."""
        with self._cache_lock:
            self._cache.clear()

    def get_template(self, template_id: str) -> Optional[TemplateMetadata]:
        """
        템플릿을 조회합니다 (캐시 우선).

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 메타데이터 또는 None (존재하지 않는 경우)
        """
        # 캐시 확인
        cached = self._cache_get(template_id)
        if cached:
            return cached

        # 저장소 조회
        template = self.repository.get_template(template_id)
        if template:
            # 캐시에 저장
            self._cache_set(template)

        return template

    def get_default_template(self) -> Optional[TemplateMetadata]:
        """
        기본 템플릿을 반환합니다.

        Returns:
            기본 템플릿 메타데이터 또는 None
        """
        if self._default_template_id:
            return self.get_template(self._default_template_id)

        # 기본 템플릿이 설정되지 않은 경우 첫 번째 템플릿 반환
        templates = self.list_templates(limit=1)
        if templates:
            return templates[0]

        return None

    def set_default_template(self, template_id: str) -> bool:
        """
        기본 템플릿을 설정합니다.

        Args:
            template_id: 기본 템플릿 ID

        Returns:
            설정 성공 여부
        """
        template = self.get_template(template_id)
        if template:
            self._default_template_id = template_id
            logger.info(f"기본 템플릿 설정: {template_id}")
            return True
        return False

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
            content_type: 필터링할 콘텐츠 타입
            limit: 반환할 최대 템플릿 수
            offset: 건너뛸 템플릿 수
            sort_by: 정렬 기준
            sort_order: 정렬 순서

        Returns:
            템플릿 메타데이터 목록
        """
        return self.repository.list_templates(
            content_type=content_type,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def search_templates(self, filters: Dict[str, Any]) -> List[TemplateMetadata]:
        """
        조건에 맞는 템플릿을 검색합니다.

        Args:
            filters: 검색 필터 딕셔너리

        Returns:
            필터링된 템플릿 메타데이터 목록
        """
        return self.repository.search_templates(filters)

    def register_template(
        self, metadata: TemplateMetadata, validate: bool = True
    ) -> ValidationResult:
        """
        새로운 템플릿을 등록합니다.

        Args:
            metadata: 등록할 템플릿 메타데이터
            validate: 검증 수행 여부 (기본값: True)

        Returns:
            ValidationResult 인스턴스
        """
        # 검증 수행
        result = ValidationResult(valid=True)
        if validate:
            result = self.validator.validate(metadata)
            if not result.valid:
                logger.error(f"템플릿 검증 실패로 등록 거부: {metadata.template_id}")
                return result

        # 저장소에 등록
        self.repository.register_template(metadata)

        # 캐시 무효화 (같은 ID가 있을 경우)
        self._cache_invalidate(metadata.template_id)

        # 캐시에 새 템플릿 추가
        self._cache_set(metadata)

        logger.info(f"템플릿 등록 완료: {metadata.template_id}")
        return result

    def update_template(
        self, template_id: str, updates: Dict[str, Any], validate: bool = True
    ) -> Optional[TemplateMetadata]:
        """
        템플릿을 업데이트합니다.

        Args:
            template_id: 템플릿 ID
            updates: 업데이트할 필드 딕셔너리
            validate: 검증 수행 여부

        Returns:
            업데이트된 템플릿 메타데이터 또는 None
        """
        # 저장소 업데이트
        updated = self.repository.update_template(template_id, updates)

        if updated:
            # 검증 수행
            if validate:
                result = self.validator.validate(updated)
                if not result.valid:
                    logger.warning(f"템플릿 업데이트 후 검증 실패: {template_id}")

            # 캐시 무효화 및 재설정
            self._cache_invalidate(template_id)
            self._cache_set(updated)

            logger.info(f"템플릿 업데이트 완료: {template_id}")

        return updated

    def delete_template(self, template_id: str) -> bool:
        """
        템플릿을 삭제합니다.

        Args:
            template_id: 템플릿 ID

        Returns:
            삭제 성공 여부
        """
        success = self.repository.delete_template(template_id)

        if success:
            # 캐시 무효화
            self._cache_invalidate(template_id)

            # 기본 템플릿이 삭제된 경우 초기화
            if self._default_template_id == template_id:
                self._default_template_id = None

            logger.info(f"템플릿 삭제 완료: {template_id}")

        return success

    def count_templates(self, content_type: Optional[ContentType] = None) -> int:
        """
        템플릿 수를 반환합니다.

        Args:
            content_type: 필터링할 콘텐츠 타입

        Returns:
            템플릿 수
        """
        return self.repository.count_templates(content_type)

    def get_all_content_types(self) -> List[ContentType]:
        """
        저장된 모든 콘텐츠 타입을 반환합니다.

        Returns:
            고유한 콘텐츠 타입 목록
        """
        return self.repository.get_all_content_types()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 통계를 반환합니다.

        Returns:
            캐시 통계 딕셔너리
        """
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "cache_max_size": self.cache_size,
                "cache_usage_percent": round(len(self._cache) / self.cache_size * 100, 2),
                "default_template_id": self._default_template_id,
            }

    def clear_cache(self) -> None:
        """캐시를 초기화합니다."""
        self._cache_clear()
        logger.info("TemplateRegistry 캐시 초기화 완료")

    def reload_from_disk(self) -> None:
        """디스크에서 템플릿 데이터를 다시 로드합니다."""
        self._cache_clear()
        self.repository._load_data()
        logger.info("TemplateRegistry 디스크에서 다시 로드 완료")


def get_registry(data_path: Optional[Path] = None) -> TemplateRegistry:
    """
    TemplateRegistry 싱글톤 인스턴스를 반환하는 편의 함수입니다.

    Args:
        data_path: 템플릿 데이터 파일 경로 (최초 초기화 시에만 필요)

    Returns:
        TemplateRegistry 싱글톤 인스턴스
    """
    return TemplateRegistry.get_instance(data_path)
