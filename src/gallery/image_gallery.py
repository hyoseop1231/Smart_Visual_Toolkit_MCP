"""
이미지 갤러리 관리 시스템

이미지 메타데이터 관리, 검색, 삭제, 정리 기능을 제공합니다.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading

from .models import ImageMetadata

logger = logging.getLogger(__name__)


class ImageGallery:
    """
    이미지 갤러리 관리 시스템

    이미지 메타데이터를 관리하고 검색, 필터링, 삭제, 정리 기능을 제공합니다.

    Attributes:
        images_dir: 이미지 파일 저장 디렉토리
        metadata_path: 메타데이터 파일 경로
        thumbnail_dir: 썸네일 저장 디렉토리
        enable_thumbnails: 썸네일 생성 활성화 여부
        thumbnail_size: 썸네일 크기 (픽셀)
    """

    # 메타데이터 파일 잠금 (동시성 제어)
    _lock = threading.Lock()

    def __init__(
        self,
        images_dir: Path,
        metadata_path: Path,
        enable_thumbnails: bool = False,
        thumbnail_dir: Optional[Path] = None,
        thumbnail_size: int = 256,
    ):
        """
        이미지 갤러리를 초기화합니다.

        Args:
            images_dir: 이미지 파일 저장 디렉토리
            metadata_path: 메타데이터 파일 경로
            enable_thumbnails: 썸네일 생성 활성화 여부
            thumbnail_dir: 썸네일 저장 디렉토리 (기본값: images_dir.parent / "thumbnails")
            thumbnail_size: 썸네일 크기 (기본값: 256px)
        """
        self.images_dir = Path(images_dir)
        self.metadata_path = Path(metadata_path)
        self.enable_thumbnails = enable_thumbnails
        self.thumbnail_size = thumbnail_size

        # 썸네일 디렉토리 설정
        if thumbnail_dir is None:
            self.thumbnail_dir = self.images_dir.parent / "thumbnails"
        else:
            self.thumbnail_dir = Path(thumbnail_dir)

        # 디렉토리 생성
        self._ensure_directories()

        # 메타데이터 로드
        self._images: Dict[str, ImageMetadata] = {}
        self._load_metadata()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리를 생성합니다."""
        self.images_dir.mkdir(parents=True, exist_ok=True)

        if self.enable_thumbnails:
            self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> None:
        """메타데이터 파일을 로드합니다."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._images = {
                    img["id"]: ImageMetadata.from_dict(img)
                    for img in data.get("images", [])
                }

                logger.info(f"메타데이터 로드 완료: {len(self._images)}개 이미지")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"메타데이터 로드 실패: {e}")
                self._images = {}
        else:
            self._images = {}
            self._save_metadata()  # 빈 메타데이터 파일 생성

    def _save_metadata(self) -> None:
        """메타데이터를 저장합니다."""
        with self._lock:
            data = {
                "images": [img.to_dict() for img in self._images.values()],
                "last_updated": datetime.now().isoformat(),
                "total_count": len(self._images),
            }

            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def register_image(self, metadata: ImageMetadata) -> None:
        """
        새로운 이미지를 등록합니다.

        Args:
            metadata: 등록할 이미지 메타데이터
        """
        with self._lock:
            # 썸네일 생성 (활성화된 경우)
            if self.enable_thumbnails and metadata.thumbnail_path is None:
                metadata.thumbnail_path = self._generate_thumbnail(metadata.filepath)

            # 메타데이터 등록
            self._images[metadata.id] = metadata
            self._save_metadata()

            logger.info(f"이미지 등록 완료: {metadata.id}")

    def _generate_thumbnail(self, image_path: str) -> Optional[str]:
        """
        이미지 썸네일을 생성합니다.

        Args:
            image_path: 원본 이미지 경로

        Returns:
            썸네일 경로 (실패 시 None)
        """
        try:
            from PIL import Image

            # 썸네일 파일명 생성
            image_filename = Path(image_path).stem
            thumbnail_filename = f"thumb_{image_filename}.png"
            thumbnail_path = self.thumbnail_dir / thumbnail_filename

            # 이미지 열기 및 썸네일 생성
            with Image.open(image_path) as img:
                img.thumbnail((self.thumbnail_size, self.thumbnail_size))
                img.save(thumbnail_path, format="PNG", optimize=True)

            logger.debug(f"썸네일 생성 완료: {thumbnail_path}")
            return str(thumbnail_path)
        except ImportError:
            logger.warning("Pillow 라이브러리가 없어 썸네일을 생성할 수 없습니다")
            return None
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            return None

    def list_images(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[ImageMetadata]:
        """
        이미지 목록을 반환합니다.

        Args:
            limit: 반환할 최대 이미지 수
            offset: 건너뛸 이미지 수 (페이지네이션용)
            sort_by: 정렬 기준 (created_at, size, style)
            sort_order: 정렬 순서 (asc, desc)

        Returns:
            이미지 메타데이터 목록
        """
        # 유효하지 않은 정렬 필드 처리
        valid_sort_fields = {"created_at", "size", "style", "filename"}
        if sort_by not in valid_sort_fields:
            logger.warning(f"잘못된 정렬 필드: {sort_by}, 기본값 사용")
            sort_by = "created_at"

        # 메타데이터 정렬 키 매핑
        sort_key_map = {
            "created_at": lambda img: img.created_at,
            "size": lambda img: img.size_bytes,
            "style": lambda img: img.style.lower(),
            "filename": lambda img: img.filename.lower(),
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map["created_at"])

        # 목록 정렬
        sorted_images = sorted(
            self._images.values(),
            key=sort_key,
            reverse=(sort_order == "desc"),
        )

        # 페이지네이션 적용
        paginated_images = sorted_images[offset : offset + limit]

        return paginated_images

    def search_images(self, filters: Dict[str, Any]) -> List[ImageMetadata]:
        """
        조건에 맞는 이미지를 검색합니다.

        Args:
            filters: 검색 필터 딕셔너리
                - style: 스타일 필터
                - date_from: 시작 날짜 (ISO 8601)
                - date_to: 종료 날짜 (ISO 8601)
                - keyword: 프롬프트 키워드
                - format: 이미지 형식
                - min_resolution: 최소 해상도

        Returns:
            필터링된 이미지 메타데이터 목록
        """
        results = list(self._images.values())

        # 스타일 필터
        if "style" in filters and filters["style"]:
            style_filter = filters["style"].lower()
            results = [img for img in results if img.style.lower() == style_filter]

        # 날짜 범위 필터
        if "date_from" in filters and filters["date_from"]:
            date_from = datetime.fromisoformat(filters["date_from"])
            results = [
                img for img in results if img.get_created_datetime() >= date_from
            ]

        if "date_to" in filters and filters["date_to"]:
            date_to = datetime.fromisoformat(filters["date_to"])
            results = [
                img for img in results if img.get_created_datetime() <= date_to
            ]

        # 키워드 필터
        if "keyword" in filters and filters["keyword"]:
            keyword = filters["keyword"].lower()
            results = [img for img in results if keyword in img.prompt.lower()]

        # 형식 필터
        if "format" in filters and filters["format"]:
            format_filter = filters["format"].lower()
            results = [img for img in results if img.format.lower() == format_filter]

        return results

    def get_image_details(self, image_id: str) -> Optional[ImageMetadata]:
        """
        특정 이미지의 상세 정보를 반환합니다.

        Args:
            image_id: 이미지 ID

        Returns:
            이미지 메타데이터 또는 None (존재하지 않는 경우)
        """
        return self._images.get(image_id)

    def delete_image(self, image_id: str, confirm: bool = False) -> Dict[str, Any]:
        """
        특정 이미지를 삭제합니다.

        Args:
            image_id: 이미지 ID
            confirm: 삭제 확인 (안전장치)

        Returns:
            삭제 결과 딕셔너리
        """
        if not confirm:
            return {
                "success": False,
                "deleted": False,
                "message": "confirm=True가 필요합니다",
            }

        metadata = self._images.get(image_id)
        if not metadata:
            return {
                "success": False,
                "deleted": False,
                "message": "이미지를 찾을 수 없습니다",
            }

        with self._lock:
            # 파일 삭제
            image_file = Path(metadata.filepath)
            if image_file.exists():
                image_file.unlink()

            # 썸네일 삭제
            if metadata.thumbnail_path:
                thumbnail_file = Path(metadata.thumbnail_path)
                if thumbnail_file.exists():
                    thumbnail_file.unlink()

            # 메타데이터에서 제거
            del self._images[image_id]
            self._save_metadata()

        return {
            "success": True,
            "deleted": True,
            "message": f"이미지가 삭제되었습니다: {image_id}",
        }

    def cleanup_old_images(
        self, days: int = 30, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        지정된 일수보다 오래된 이미지를 정리합니다.

        Args:
            days: 보관 기간 (일)
            dry_run: true인 경우 실제 삭제 없이 목록만 반환

        Returns:
            정리 결과 딕셔너리
        """
        to_delete = []

        # 삭제 대상 식별
        for image_id, metadata in self._images.items():
            if metadata.is_expired(days):
                to_delete.append(image_id)

        if dry_run:
            # dry-run 모드: 예상 삭제 목록만 반환
            total_size = sum(
                self._images[img_id].size_bytes for img_id in to_delete
            )

            return {
                "success": True,
                "deleted_count": 0,
                "would_delete_count": len(to_delete),
                "freed_space_bytes": total_size,
                "deleted_images": [],
                "would_delete_images": to_delete,
            }

        # 실제 삭제 실행
        deleted_images = []
        freed_space = 0

        for image_id in to_delete:
            result = self.delete_image(image_id, confirm=True)
            if result["success"]:
                deleted_images.append(image_id)
                freed_space += self._images.get(image_id, ImageMetadata(
                    id="", filename="", filepath="", thumbnail_path=None,
                    created_at="", prompt="", style="", aspect_ratio="",
                    resolution="", format="", size_bytes=0, generation_params={}
                )).size_bytes

        return {
            "success": True,
            "deleted_count": len(deleted_images),
            "would_delete_count": 0,
            "freed_space_bytes": freed_space,
            "deleted_images": deleted_images,
            "would_delete_images": [],
        }

    def validate_metadata(self) -> None:
        """
        메타데이터 일관성을 검증하고 복구합니다.

        파일이 존재하지 않는 메타데이터 항목을 제거합니다.
        """
        orphaned = []

        for image_id, metadata in list(self._images.items()):
            image_file = Path(metadata.filepath)
            if not image_file.exists():
                orphaned.append(image_id)

        if orphaned:
            logger.warning(f"고아 메타데이터 {len(orphaned)}개 발견, 삭제 중")
            for image_id in orphaned:
                del self._images[image_id]

            self._save_metadata()
