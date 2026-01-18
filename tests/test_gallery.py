"""
SPEC-GALLERY-001: 이미지 갤러리 시스템 단위 테스트

테스트 시나리오:
- TC-001 ~ TC-003: 이미지 목록 조회 (list_images)
- TC-004 ~ TC-008: 이미지 검색 (search_images)
- TC-009 ~ TC-010: 이미지 상세 조회 (get_image_details)
- TC-011 ~ TC-014: 이미지 삭제 (delete_image)
- TC-015 ~ TC-017: 오래된 이미지 정리 (cleanup_old_images)
- TC-018 ~ TC-020: 메타데이터 일관성
- TC-021 ~ TC-024: 썸네일 기능
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gallery.models import ImageMetadata
from gallery.image_gallery import ImageGallery


class TestImageMetadata:
    """ImageMetadata 데이터클래스 테스트"""

    def test_create_metadata(self):
        """메타데이터 생성"""
        metadata = ImageMetadata(
            id="img_20250119_abc123",
            filename="image_20250119_abc123.png",
            filepath="/output/images/image_20250119_abc123.png",
            thumbnail_path="/output/thumbnails/thumb_abc123.png",
            created_at="2025-01-19T10:30:00Z",
            prompt="A beautiful sunset",
            style="cinematic",
            aspect_ratio="16:9",
            resolution="1024x576",
            format="png",
            size_bytes=245678,
            generation_params={},
        )

        assert metadata.id == "img_20250119_abc123"
        assert metadata.style == "cinematic"
        assert metadata.format == "png"

    def test_to_dict(self):
        """메타데이터를 딕셔너리로 변환"""
        metadata = ImageMetadata(
            id="img_test",
            filename="test.png",
            filepath="/path/to/test.png",
            thumbnail_path=None,
            created_at="2025-01-19T10:00:00Z",
            prompt="test prompt",
            style="anime",
            aspect_ratio="1:1",
            resolution="512x512",
            format="png",
            size_bytes=100000,
            generation_params={},
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "img_test"
        assert result["style"] == "anime"

    def test_from_dict(self):
        """딕셔너리에서 메타데이터 생성"""
        data = {
            "id": "img_test",
            "filename": "test.png",
            "filepath": "/path/to/test.png",
            "thumbnail_path": None,
            "created_at": "2025-01-19T10:00:00Z",
            "prompt": "test prompt",
            "style": "anime",
            "aspect_ratio": "1:1",
            "resolution": "512x512",
            "format": "png",
            "size_bytes": 100000,
            "generation_params": {},
        }

        metadata = ImageMetadata.from_dict(data)

        assert metadata.id == "img_test"
        assert metadata.style == "anime"


class TestImageGalleryInitialization:
    """ImageGallery 초기화 테스트 (TC-INT-001)"""

    def test_creates_metadata_file_if_not_exists(self):
        """메타데이터 파일이 없으면 생성함"""
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "metadata.json"

            _gallery = ImageGallery(
                images_dir=Path(temp_dir) / "images",
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            assert metadata_path.exists()

    def test_loads_existing_metadata(self):
        """기존 메타데이터를 로드함"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            # 기존 메타데이터 생성
            test_data = {
                "images": [
                    {
                        "id": "img_001",
                        "filename": "test.png",
                        "filepath": str(images_dir / "test.png"),
                        "thumbnail_path": None,
                        "created_at": "2025-01-19T10:00:00Z",
                        "prompt": "test",
                        "style": "cinematic",
                        "aspect_ratio": "16:9",
                        "resolution": "1024x576",
                        "format": "png",
                        "size_bytes": 100000,
                        "generation_params": {},
                    }
                ],
                "last_updated": "2025-01-19T10:00:00Z",
                "total_count": 1,
            }

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            # 갤러리 초기화
            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            assert len(gallery._images) == 1
            assert "img_001" in gallery._images


class TestImageRegistration:
    """이미지 등록 테스트 (TC-018)"""

    def test_register_image_saves_metadata(self):
        """이미지 등록 시 메타데이터가 저장됨"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            # 테스트 이미지 파일 생성
            test_image = images_dir / "test.png"
            test_image.write_bytes(b"fake image data")

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(test_image),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test prompt",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=len(b"fake image data"),
                generation_params={},
            )

            gallery.register_image(metadata)

            # 메타데이터가 저장되었는지 확인
            assert "img_001" in gallery._images

            # 파일도 저장되었는지 확인
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["total_count"] == 1
            assert len(data["images"]) == 1

    def test_register_thumbnail_when_enabled(self):
        """썸네일 활성화 시 썸네일 생성 (TC-021)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            thumbnails_dir = Path(temp_dir) / "thumbnails"
            metadata_path = Path(temp_dir) / "metadata.json"

            # 테스트 이미지 파일 생성 (실제 PNG 파일)
            from PIL import Image

            test_image = images_dir / "test.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_image)

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=True,
                thumbnail_dir=thumbnails_dir,
                thumbnail_size=64,
            )

            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(test_image),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test prompt",
                style="cinematic",
                aspect_ratio="1:1",
                resolution="100x100",
                format="png",
                size_bytes=test_image.stat().st_size,
                generation_params={},
            )

            gallery.register_image(metadata)

            # 썸네일이 생성되었는지 확인
            assert metadata.thumbnail_path is not None
            assert Path(metadata.thumbnail_path).exists()


class TestListImages:
    """이미지 목록 조회 테스트 (TC-001 ~ TC-003)"""

    def test_list_all_images(self):
        """모든 이미지 목록 반환 (TC-001)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 4개 이미지 등록
            for i in range(4):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=(datetime.now() - timedelta(days=i)).isoformat(),
                    prompt=f"prompt {i}",
                    style="cinematic" if i % 2 == 0 else "anime",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000 + i * 1000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 목록 조회
            images = gallery.list_images(
                limit=50, offset=0, sort_by="created_at", sort_order="desc"
            )

            assert len(images) == 4

    def test_pagination(self):
        """페이지네이션 동작 (TC-002)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 10개 이미지 등록
            for i in range(10):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=datetime.now().isoformat(),
                    prompt=f"prompt {i}",
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 첫 페이지
            page1 = gallery.list_images(
                limit=5, offset=0, sort_by="created_at", sort_order="desc"
            )
            assert len(page1) == 5

            # 두 번째 페이지
            page2 = gallery.list_images(
                limit=5, offset=5, sort_by="created_at", sort_order="desc"
            )
            assert len(page2) == 5

            # 서로 다른 이미지인지 확인
            page1_ids = {img.id for img in page1}
            page2_ids = {img.id for img in page2}
            assert len(page1_ids & page2_ids) == 0  # 교집합 없음

    def test_sort_by_size(self):
        """크기 기준 정렬 (TC-003)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 다양한 크기의 이미지 등록
            sizes = [500000, 100000, 300000, 200000, 400000]
            for i, size in enumerate(sizes):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=datetime.now().isoformat(),
                    prompt=f"prompt {i}",
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=size,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 크기 오름차순 정렬
            images = gallery.list_images(
                limit=10, offset=0, sort_by="size", sort_order="asc"
            )

            sizes_result = [img.size_bytes for img in images]
            assert sizes_result == sorted(sizes)

    def test_sort_by_style(self):
        """스타일 기준 정렬 (TC-003)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 다양한 스타일의 이미지 등록
            styles = ["anime", "cinematic", "watercolor", "anime", "cinematic"]
            for i, style in enumerate(styles):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=datetime.now().isoformat(),
                    prompt=f"prompt {i}",
                    style=style,
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 스타일 내림차순 정렬
            images = gallery.list_images(
                limit=10, offset=0, sort_by="style", sort_order="desc"
            )

            styles_result = [img.style for img in images]
            assert styles_result == sorted(styles, reverse=True)


class TestSearchImages:
    """이미지 검색 테스트 (TC-004 ~ TC-008)"""

    def test_search_by_style(self):
        """스타일 필터링 (TC-004)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 다양한 스타일의 이미지 등록
            styles = ["cinematic", "cinematic", "anime", "watercolor"]
            for i, style in enumerate(styles):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=datetime.now().isoformat(),
                    prompt=f"prompt {i}",
                    style=style,
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # cinematic 스타일 검색
            results = gallery.search_images(filters={"style": "cinematic"})

            assert len(results) == 2
            assert all(img.style == "cinematic" for img in results)

    def test_search_by_date_range(self):
        """날짜 범위 필터링 (TC-005)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 다른 날짜의 이미지 등록
            base_date = datetime.now()
            dates = [
                base_date - timedelta(days=3),  # 3일 전
                base_date - timedelta(days=2),  # 2일 전
                base_date - timedelta(days=1),  # 1일 전
            ]

            for i, date in enumerate(dates):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=date.isoformat(),
                    prompt=f"prompt {i}",
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 2일 전~1일 전 검색
            date_from = (base_date - timedelta(days=2)).isoformat()
            date_to = base_date.isoformat()

            results = gallery.search_images(
                filters={"date_from": date_from, "date_to": date_to}
            )

            assert len(results) == 2  # 2일 전, 1일 전

    def test_search_by_keyword(self):
        """키워드 검색 (TC-006)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 다양한 프롬프트의 이미지 등록
            prompts = [
                "A beautiful sunset over mountains",
                "A serene mountain landscape",
                "Ocean waves at sunset",
            ]

            for i, prompt in enumerate(prompts):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=datetime.now().isoformat(),
                    prompt=prompt,
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # "sunset" 키워드 검색
            results = gallery.search_images(filters={"keyword": "sunset"})

            assert len(results) == 2
            assert all("sunset" in img.prompt.lower() for img in results)

    def test_search_with_multiple_filters(self):
        """복합 조건 검색 (TC-007)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            base_date = datetime.now()

            # 다양한 조건의 이미지 등록
            test_data = [
                {
                    "style": "cinematic",
                    "date": base_date - timedelta(days=1),
                    "prompt": "beautiful sunset",
                },
                {
                    "style": "cinematic",
                    "date": base_date - timedelta(days=3),
                    "prompt": "beautiful sunset",
                },
                {
                    "style": "anime",
                    "date": base_date - timedelta(days=1),
                    "prompt": "beautiful sunset",
                },
                {
                    "style": "cinematic",
                    "date": base_date - timedelta(days=1),
                    "prompt": "mountain view",
                },
            ]

            for i, data in enumerate(test_data):
                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(images_dir / f"test_{i}.png"),
                    thumbnail_path=None,
                    created_at=data["date"].isoformat(),
                    prompt=data["prompt"],
                    style=data["style"],
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=100000,
                    generation_params={},
                )
                gallery.register_image(metadata)

            # cinematic + beautiful + 최근 2일
            date_from = (base_date - timedelta(days=2)).isoformat()
            results = gallery.search_images(
                filters={
                    "style": "cinematic",
                    "keyword": "beautiful",
                    "date_from": date_from,
                }
            )

            assert len(results) == 1  # 첫 번째 항목만 매칭

    def test_search_no_results(self):
        """검색 결과 없음 (TC-008)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록
            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(images_dir / "test.png"),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test prompt",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=100000,
                generation_params={},
            )
            gallery.register_image(metadata)

            # 존재하지 않는 스타일 검색
            results = gallery.search_images(filters={"style": "nonexistent"})

            assert len(results) == 0


class TestGetImageDetails:
    """이미지 상세 조회 테스트 (TC-009 ~ TC-010)"""

    def test_get_existing_image_details(self):
        """존재하는 이미지 상세 조회 (TC-009)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록
            original_metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(images_dir / "test.png"),
                thumbnail_path=None,
                created_at="2025-01-19T10:00:00Z",
                prompt="A beautiful sunset",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=245678,
                generation_params={"negative_prompt": None},
            )
            gallery.register_image(original_metadata)

            # 상세 조회
            details = gallery.get_image_details("img_001")

            assert details is not None
            assert details.id == "img_001"
            assert details.prompt == "A beautiful sunset"
            assert details.style == "cinematic"
            assert details.resolution == "1024x576"
            assert details.size_bytes == 245678

    def test_get_nonexistent_image_details(self):
        """존재하지 않는 이미지 조회 (TC-010)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 존재하지 않는 ID 조회
            details = gallery.get_image_details("nonexistent")

            assert details is None


class TestDeleteImage:
    """이미지 삭제 테스트 (TC-011 ~ TC-014)"""

    def test_delete_without_confirm(self):
        """confirm 없는 삭제 시도 (TC-011)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록
            test_image = images_dir / "test.png"
            test_image.write_bytes(b"fake image")

            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(test_image),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=len(b"fake image"),
                generation_params={},
            )
            gallery.register_image(metadata)

            # confirm=False로 삭제 시도
            result = gallery.delete_image("img_001", confirm=False)

            assert result["success"] is False
            assert result["deleted"] is False
            assert "confirm" in result["message"].lower()

            # 파일과 메타데이터가 여전히 존재하는지 확인
            assert test_image.exists()
            assert "img_001" in gallery._images

    def test_delete_with_confirm(self):
        """confirm 있는 삭제 (TC-012)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록
            test_image = images_dir / "test.png"
            test_image.write_bytes(b"fake image")

            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(test_image),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=len(b"fake image"),
                generation_params={},
            )
            gallery.register_image(metadata)

            # confirm=True로 삭제
            result = gallery.delete_image("img_001", confirm=True)

            assert result["success"] is True
            assert result["deleted"] is True

            # 파일과 메타데이터가 삭제되었는지 확인
            assert not test_image.exists()
            assert "img_001" not in gallery._images

    def test_delete_nonexistent_image(self):
        """존재하지 않는 이미지 삭제 (TC-013)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 존재하지 않는 이미지 삭제 시도
            result = gallery.delete_image("nonexistent", confirm=True)

            assert result["success"] is False
            assert (
                "not found" in result["message"].lower()
                or "찾을 수 없습니다" in result["message"]
            )


class TestCleanupOldImages:
    """오래된 이미지 정리 테스트 (TC-015 ~ TC-017)"""

    def test_cleanup_dry_run(self):
        """dry-run 모드 (TC-015)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            base_date = datetime.now()

            # 다양한 날짜의 이미지 등록
            for i, days_ago in enumerate([30, 20, 10]):
                test_image = images_dir / f"test_{i}.png"
                test_image.write_bytes(b"fake image")

                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(test_image),
                    thumbnail_path=None,
                    created_at=(base_date - timedelta(days=days_ago)).isoformat(),
                    prompt="test",
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=len(b"fake image"),
                    generation_params={},
                )
                gallery.register_image(metadata)

            # dry-run 모드로 정리
            result = gallery.cleanup_old_images(days=30, dry_run=True)

            assert result["success"] is True
            assert result["deleted_count"] == 0  # 실제 삭제 없음
            assert result["would_delete_count"] >= 1  # 삭제 예상 개수

            # 모든 파일이 여전히 존재하는지 확인
            for i in range(3):
                assert (images_dir / f"test_{i}.png").exists()

    def test_cleanup_actual_deletion(self):
        """실제 정리 실행 (TC-016)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            base_date = datetime.now()

            # 다양한 날짜의 이미지 등록
            for i, days_ago in enumerate([30, 20, 10]):
                test_image = images_dir / f"test_{i}.png"
                test_image.write_bytes(b"fake image")

                metadata = ImageMetadata(
                    id=f"img_00{i}",
                    filename=f"test_{i}.png",
                    filepath=str(test_image),
                    thumbnail_path=None,
                    created_at=(base_date - timedelta(days=days_ago)).isoformat(),
                    prompt="test",
                    style="cinematic",
                    aspect_ratio="16:9",
                    resolution="1024x576",
                    format="png",
                    size_bytes=len(b"fake image"),
                    generation_params={},
                )
                gallery.register_image(metadata)

            # 실제 정리 실행
            result = gallery.cleanup_old_images(days=30, dry_run=False)

            assert result["success"] is True
            assert result["deleted_count"] >= 1

            # 30일 이상된 이미지만 삭제되었는지 확인
            assert not (images_dir / "test_0.png").exists()  # 30일 전 - 삭제됨
            assert (images_dir / "test_1.png").exists()  # 20일 전 - 유지됨
            assert (images_dir / "test_2.png").exists()  # 10일 전 - 유지됨

    def test_cleanup_nothing_to_cleanup(self):
        """정리 대상 없음 (TC-017)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 최근 이미지만 등록 (7일 전)
            test_image = images_dir / "test.png"
            test_image.write_bytes(b"fake image")

            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(test_image),
                thumbnail_path=None,
                created_at=(datetime.now() - timedelta(days=7)).isoformat(),
                prompt="test",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=len(b"fake image"),
                generation_params={},
            )
            gallery.register_image(metadata)

            # 30일 기준으로 정리 시도
            result = gallery.cleanup_old_images(days=30, dry_run=False)

            assert result["success"] is True
            assert result["deleted_count"] == 0
            assert test_image.exists()  # 파일 여전히 존재


class TestMetadataConsistency:
    """메타데이터 일관성 테스트 (TC-019 ~ TC-020)"""

    def test_remove_orphaned_metadata(self):
        """고아 메타데이터 정리 (TC-019)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록 (파일 없음)
            metadata = ImageMetadata(
                id="img_orphaned",
                filename="nonexistent.png",
                filepath=str(images_dir / "nonexistent.png"),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=100000,
                generation_params={},
            )
            gallery.register_image(metadata)

            # 목록 조회 시 고아 메타데이터 정리
            images = gallery.list_images(
                limit=10, offset=0, sort_by="created_at", sort_order="desc"
            )

            # 고아 메타데이터가 제거되어야 함
            assert "img_orphaned" not in gallery._images
            assert len(images) == 0


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_gallery_list(self):
        """빈 갤러리 목록 조회"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            images = gallery.list_images(
                limit=10, offset=0, sort_by="created_at", sort_order="desc"
            )

            assert len(images) == 0

    def test_search_empty_gallery(self):
        """빈 갤러리 검색"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            results = gallery.search_images(filters={"style": "cinematic"})

            assert len(results) == 0

    def test_invalid_sort_field(self):
        """잘못된 정렬 필드"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            # 이미지 등록
            metadata = ImageMetadata(
                id="img_001",
                filename="test.png",
                filepath=str(images_dir / "test.png"),
                thumbnail_path=None,
                created_at=datetime.now().isoformat(),
                prompt="test",
                style="cinematic",
                aspect_ratio="16:9",
                resolution="1024x576",
                format="png",
                size_bytes=100000,
                generation_params={},
            )
            gallery.register_image(metadata)

            # 잘못된 정렬 필드 (기본값으로 대체되어야 함)
            images = gallery.list_images(
                limit=10, offset=0, sort_by="invalid_field", sort_order="desc"
            )

            # 기본 동작으로 정렬되어야 함
            assert len(images) == 1

    def test_concurrent_registration(self):
        """동시 등록 시나리오 (TC-INT-002)"""
        import threading

        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = Path(temp_dir) / "metadata.json"

            gallery = ImageGallery(
                images_dir=images_dir,
                metadata_path=metadata_path,
                enable_thumbnails=False,
            )

            errors = []

            def register_image(i: int):
                try:
                    metadata = ImageMetadata(
                        id=f"img_{i:03d}",
                        filename=f"test_{i}.png",
                        filepath=str(images_dir / f"test_{i}.png"),
                        thumbnail_path=None,
                        created_at=datetime.now().isoformat(),
                        prompt=f"prompt {i}",
                        style="cinematic",
                        aspect_ratio="16:9",
                        resolution="1024x576",
                        format="png",
                        size_bytes=100000,
                        generation_params={},
                    )
                    gallery.register_image(metadata)
                except Exception as e:
                    errors.append(e)

            # 동시에 10개 이미지 등록
            threads = [
                threading.Thread(target=register_image, args=(i,)) for i in range(10)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 에러 없이 모두 등록되어야 함
            assert len(errors) == 0
            assert len(gallery._images) == 10
