"""
Characterization Tests for Template System (SPEC-TEMPLATE-001)

이 테스트는 DDD PRESERVE 단계의 일부로, 새로운 템플릿 시스템의 동작을 캡처합니다.
기존 banana_styles.json의 동작을 보존하는지 검증합니다.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from src.templates.models import ContentType, TemplateMetadata
from src.templates.repository import TemplateRepository
from src.templates.validators import TemplateValidator, ValidationResult
from src.templates.registry import TemplateRegistry, get_registry


class TestTemplateMetadata:
    """TemplateMetadata 데이터클래스의 동작을 캡처합니다."""

    def test_characterize_create_image_template(self):
        """
        CHARACTERIZATION: 이미지 템플릿 생성 동작
        이 테스트는 현재 구현의 동작을 문서화합니다.
        """
        # Setup
        data = {
            "template_id": "test_template",
            "name": "Test Template",
            "content_type": "image",
            "keywords": "Test keywords",
            "description": "Test description",
            "style_name": "Legacy Style",
            "tags": ["tag1", "tag2"],
            "aspect_ratios": ["16:9", "1:1"],
            "formats": ["png", "jpeg"],
            "version": "1.0.0",
        }

        # Execute
        metadata = TemplateMetadata.from_dict(data)

        # Verify (현재 동작 캡처)
        assert metadata.template_id == "test_template"
        assert metadata.name == "Test Template"
        assert metadata.content_type == ContentType.IMAGE
        assert metadata.keywords == "Test keywords"
        assert metadata.description == "Test description"
        assert metadata.style_name == "Legacy Style"
        assert metadata.tags == ["tag1", "tag2"]
        assert metadata.aspect_ratios == ["16:9", "1:1"]
        assert metadata.formats == ["png", "jpeg"]
        assert metadata.version == "1.0.0"
        # created_at과 updated_at은 자동 생성됨
        assert metadata.created_at != ""
        assert metadata.updated_at != ""

    def test_characterize_to_dict(self):
        """
        CHARACTERIZATION: to_dict() 메서드 동작
        """
        # Setup
        metadata = TemplateMetadata(
            template_id="test",
            name="Test",
            content_type=ContentType.IMAGE,
            keywords="test",
        )

        # Execute
        data = metadata.to_dict()

        # Verify
        assert data["template_id"] == "test"
        assert data["content_type"] == "image"  # enum이 문자열로 변환됨
        assert "created_at" in data
        assert "updated_at" in data

    def test_characterize_supports_aspect_ratio(self):
        """
        CHARACTERIZATION: supports_aspect_ratio() 메서드 동작
        """
        # Setup
        metadata = TemplateMetadata(
            template_id="test",
            name="Test",
            content_type=ContentType.IMAGE,
            keywords="test",
            aspect_ratios=["16:9", "1:1"],
        )

        # Execute & Verify
        assert metadata.supports_aspect_ratio("16:9") is True
        assert metadata.supports_aspect_ratio("1:1") is True
        assert metadata.supports_aspect_ratio("4:3") is False

    def test_characterize_get_legacy_style_name(self):
        """
        CHARACTERIZATION: get_legacy_style_name() 메서드 동작
        """
        # Case 1: style_name이 있는 경우
        metadata1 = TemplateMetadata(
            template_id="test",
            name="Test",
            content_type=ContentType.IMAGE,
            keywords="test",
            style_name="Legacy Name",
        )
        assert metadata1.get_legacy_style_name() == "Legacy Name"

        # Case 2: style_name이 없는 경우
        metadata2 = TemplateMetadata(
            template_id="test2",
            name="Test2",
            content_type=ContentType.IMAGE,
            keywords="test",
        )
        assert metadata2.get_legacy_style_name() == "test2"


class TestTemplateRepository:
    """TemplateRepository의 동작을 캡처합니다."""

    @pytest.fixture
    def temp_data_file(self, tmp_path):
        """임시 데이터 파일을 생성합니다."""
        data_path = tmp_path / "templates.json"
        return data_path

    def test_characterize_register_and_get_template(self, temp_data_file):
        """
        CHARACTERIZATION: 템플릿 등록 및 조회 동작
        """
        # Setup
        repo = TemplateRepository(temp_data_file, auto_save=True)
        metadata = TemplateMetadata(
            template_id="test",
            name="Test",
            content_type=ContentType.IMAGE,
            keywords="test",
        )

        # Execute
        repo.register_template(metadata)
        retrieved = repo.get_template("test")

        # Verify
        assert retrieved is not None
        assert retrieved.template_id == "test"
        assert retrieved.name == "Test"

    def test_characterize_list_templates(self, temp_data_file):
        """
        CHARACTERIZATION: 템플릿 목록 조회 동작
        """
        # Setup
        repo = TemplateRepository(temp_data_file)
        repo.register_template(
            TemplateMetadata(
                template_id="test1",
                name="A Template",
                content_type=ContentType.IMAGE,
                keywords="test1",
            )
        )
        repo.register_template(
            TemplateMetadata(
                template_id="test2",
                name="B Template",
                content_type=ContentType.IMAGE,
                keywords="test2",
            )
        )

        # Execute
        templates = repo.list_templates(sort_by="name", sort_order="asc")

        # Verify
        assert len(templates) == 2
        assert templates[0].template_id == "test1"
        assert templates[1].template_id == "test2"

    def test_characterize_search_templates(self, temp_data_file):
        """
        CHARACTERIZATION: 템플릿 검색 동작
        """
        # Setup
        repo = TemplateRepository(temp_data_file)
        repo.register_template(
            TemplateMetadata(
                template_id="test1",
                name="Corporate Template",
                content_type=ContentType.IMAGE,
                keywords="corporate",
                tags=["business", "professional"],
            )
        )
        repo.register_template(
            TemplateMetadata(
                template_id="test2",
                name="Creative Template",
                content_type=ContentType.IMAGE,
                keywords="creative",
                tags=["artistic"],
            )
        )

        # Execute - keyword search
        results = repo.search_templates({"keyword": "corporate"})

        # Verify
        assert len(results) == 1
        assert results[0].template_id == "test1"

        # Execute - tag search
        results_tag = repo.search_templates({"tag": "artistic"})

        # Verify
        assert len(results_tag) == 1
        assert results_tag[0].template_id == "test2"


class TestTemplateValidator:
    """TemplateValidator의 동작을 캡처합니다."""

    def test_characterize_validate_valid_template(self):
        """
        CHARACTERIZATION: 유효한 템플릿 검증 동작
        """
        # Setup
        validator = TemplateValidator(strict_mode=False)
        metadata = TemplateMetadata(
            template_id="valid_test",
            name="Valid Template",
            content_type=ContentType.IMAGE,
            keywords="test keywords",
            aspect_ratios=["16:9"],
            formats=["png"],
        )

        # Execute
        result = validator.validate(metadata)

        # Verify
        assert result.valid is True
        assert len(result.errors) == 0

    def test_characterize_validate_invalid_template(self):
        """
        CHARACTERIZATION: 유효하지 않은 템플릿 검증 동작
        """
        # Setup
        validator = TemplateValidator(strict_mode=False)
        metadata = TemplateMetadata(
            template_id="",  # Invalid: empty
            name="",  # Invalid: empty
            content_type=ContentType.IMAGE,
            keywords="",  # Invalid: empty
        )

        # Execute
        result = validator.validate(metadata)

        # Verify
        assert result.valid is False
        assert len(result.errors) > 0
        # 필수 필드 오류 확인
        error_fields = [err.field for err in result.errors]
        assert "template_id" in error_fields
        assert "name" in error_fields
        assert "keywords" in error_fields


class TestTemplateRegistry:
    """TemplateRegistry의 동작을 캡처합니다."""

    @pytest.fixture
    def temp_data_file(self, tmp_path):
        """임시 데이터 파일을 생성합니다."""
        data_path = tmp_path / "templates.json"
        return data_path

    def test_characterize_singleton_behavior(self, temp_data_file):
        """
        CHARACTERIZATION: 싱글톤 동작
        """
        # Execute - 두 번 호출
        registry1 = get_registry(temp_data_file)
        registry2 = get_registry(temp_data_file)

        # Verify - 같은 인스턴스여야 함
        assert registry1 is registry2

    def test_characterize_cache_behavior(self, temp_data_file):
        """
        CHARACTERIZATION: LRU 캐시 동작
        """
        # Setup
        registry = TemplateRegistry(temp_data_file, cache_size=2)
        registry.register_template(
            TemplateMetadata(
                template_id="test1",
                name="Test 1",
                content_type=ContentType.IMAGE,
                keywords="test1",
            )
        )
        registry.register_template(
            TemplateMetadata(
                template_id="test2",
                name="Test 2",
                content_type=ContentType.IMAGE,
                keywords="test2",
            )
        )

        # Execute - 첫 번째 조회 (캐시 미스)
        tmpl1_first = registry.get_template("test1")

        # Execute - 두 번째 조회 (캐시 히트 예상)
        tmpl1_second = registry.get_template("test1")

        # Verify
        assert tmpl1_first is not None
        assert tmpl1_second is not None

        # 캐시 통계 확인
        stats = registry.get_cache_stats()
        assert stats["cache_size"] >= 1


class TestBackwardCompatibility:
    """
    하위 호환성 테스트

    기존 banana_styles.json과 새로운 템플릿 시스템 간의 호환성을 검증합니다.
    """

    def test_characterize_legacy_style_mapping(self):
        """
        CHARACTERIZATION: 레거시 스타일 이름 매핑
        """
        # Setup - 기존 banana_styles.json 데이터와 호환되는 템플릿
        template = TemplateMetadata(
            template_id="flat_corporate",
            name="Flat Corporate",
            content_type=ContentType.IMAGE,
            keywords="Flat illustration, Corporate, Memphis",
            description="Professional, flat design suitable for business presentations",
            style_name="Flat Corporate",  # 레거시 스타일 이름
        )

        # Execute
        legacy_name = template.get_legacy_style_name()

        # Verify
        assert legacy_name == "Flat Corporate"
        assert template.template_id == "flat_corporate"

    def test_characterize_default_template_fallback(self):
        """
        CHARACTERIZATION: 기본 템플릿 폴백 동작
        """
        # Setup - 임시 레지스트리
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_path = Path(tmp_dir) / "templates.json"
            registry = TemplateRegistry(data_path)

            # 템플릿 없음
            default = registry.get_default_template()

            # Verify - 없으면 None 반환
            assert default is None

            # 기본 템플릿 설정
            registry.register_template(
                TemplateMetadata(
                    template_id="default_test",
                    name="Default",
                    content_type=ContentType.IMAGE,
                    keywords="default",
                )
            )
            registry.set_default_template("default_test")

            # Execute
            default_after = registry.get_default_template()

            # Verify
            assert default_after is not None
            assert default_after.template_id == "default_test"


class TestTemplateDataFiles:
    """
    템플릿 데이터 파일 동작 테스트

    실제 템플릿 JSON 파일의 로드 및 검증을 테스트합니다.
    """

    def test_characterize_load_templates_image(self):
        """
        CHARACTERIZATION: templates_image.json 로드 동작
        """
        # Setup
        project_root = Path(__file__).parent.parent
        data_path = project_root / "src" / "resources" / "templates_image.json"

        if not data_path.exists():
            pytest.skip(f"Data file not found: {data_path}")

        # Execute
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify
        assert "templates" in data
        assert len(data["templates"]) > 0

        # 첫 번째 템플릿 검증
        first_tmpl_data = data["templates"][0]
        template = TemplateMetadata.from_dict(first_tmpl_data)

        assert template.template_id != ""
        assert template.content_type == ContentType.IMAGE
        assert template.is_image_template() is True

    def test_characterize_load_skywork_templates(self):
        """
        CHARACTERIZATION: Skywork 템플릿 로드 동작
        """
        # Setup
        project_root = Path(__file__).parent.parent
        templates_dir = project_root / "src" / "resources"

        skywork_files = [
            "templates_doc.json",
            "templates_ppt.json",
            "templates_excel.json",
        ]

        for filename in skywork_files:
            data_path = templates_dir / filename

            if not data_path.exists():
                continue

            # Execute
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify
            assert "templates" in data
            assert len(data["templates"]) > 0

            # 모든 템플릿이 문서 타입인지 확인
            for tmpl_data in data["templates"]:
                template = TemplateMetadata.from_dict(tmpl_data)
                assert template.is_document_template() is True
