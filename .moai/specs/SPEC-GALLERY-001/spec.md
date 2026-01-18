---
id: SPEC-GALLERY-001
version: "1.0.0"
status: "draft"
created: "2026-01-19"
updated: "2026-01-19"
author: "Hyoseop"
priority: "MEDIUM"
lifecycle: "spec-anchored"
tags: ["gallery", "image-management", "metadata", "mcp-tools"]
---

# SPEC-GALLERY-001: 이미지 갤러리 및 히스토리 관리

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-19 | Hyoseop | 초기 SPEC 작성 |

---

## 1. Environment (환경)

### 1.1 현재 시스템 컨텍스트

```
현재 구현 상태:
├── src/main.py                    # MCP 서버
│   ├── generate_image()           # 단일 이미지 생성
│   ├── generate_images_batch()    # 배치 이미지 생성
│   └── [이미지 관리 도구 없음]     # 기능 공백
├── src/generators/image_gen.py    # ImageGenerator 클래스
│   └── generate()                 # 이미지를 output/images/에 저장
├── src/resources/banana_styles.json # 15가지 스타일 정의
└── output/images/                 # 생성된 이미지 저장소
    ├── image_20250119_*.png       # 파일명: 이미지_날짜_해시.png
    └── [메타데이터 없음]           # 기능 공백

기술 스택:
├── Python 3.10+
├── FastMCP 0.1.0+
├── google-genai SDK (Imagen 4.0)
├── pathlib (파일 시스템 관리)
└── json (메타데이터 저장)
```

### 1.2 현재 제한사항

| 제한사항 | 설명 | 영향 |
|---------|------|------|
| 갤러리 기능 없음 | 생성된 이미지를 조회/관리할 수 없음 | 사용자 경험 저하 |
| 메타데이터 부족 | 이미지 생성 정보(스타일, 프롬프트 등) 추적 불가 | 재사용/학습 어려움 |
| 검색/필터 없음 | 원하는 이미지를 찾을 수 없음 | 생산성 저하 |
| 정리 기능 없음 | 오래된 이미지 삭제/관리 불가 | 디스크 공간 낭비 |

### 1.3 외부 의존성

| 의존성 | 버전 | 제약사항 |
|--------|------|---------|
| Python pathlib | 표준 라이브러리 | 파일 시스템 접근 |
| Python json | 표준 라이브러리 | 메타데이터 저장 |
| PIL/Pillow | 10.0+ | 썸네일 생성 (선택적) |

---

## 2. Assumptions (가정)

### 2.1 기술적 가정

| ID | 가정 | 신뢰도 | 검증 방법 |
|----|------|--------|----------|
| A-001 | output/images/ 디렉토리에 생성된 모든 이미지 파일이 존재함 | HIGH | 기존 이미지 생성 로직 확인 |
| A-002 | 파일명에서 날짜/해시 정보를 추출할 수 있음 | HIGH | 현재 파일 네이밍 규칙 분석 |
| A-003 | JSON 메타데이터 파일로 충분한 정보 저장 가능 | HIGH | 메타데이터 스키마 설계 |
| A-004 | 파일 시스템 기반 검색으로 성능 충분 | MEDIUM | 이미지 수 천개 미만 가정 |
| A-005 | 썸네일 생성은 PIL/Pillow로 가능함 | HIGH | Pillow 라이브러리 검증 |

### 2.2 비즈니스 가정

| ID | 가정 | 신뢰도 | 위험 시 대응 |
|----|------|--------|-------------|
| B-001 | 사용자가 이전에 생성한 이미지를 재사용하려는 니즈가 있음 | HIGH | 사용자 피드백 수집 |
| B-002 | 스타일/프롬프트별 필터링이 주요 사용 패턴임 | MEDIUM | 통계 추적으로 검증 |
| B-003 | 대량 이미지 정리 기능이 필요함 | MEDIUM | 디스크 사용량 모니터링 |

### 2.3 5 Whys 분석 (근본 원인 분석)

**표면적 문제**: 생성된 이미지를 찾거나 관리할 수 없음

1. **Why?** 이미지 목록을 보여주는 기능이 없음
2. **Why?** 이미지 메타데이터를 저장/관리하는 시스템이 없음
3. **Why?** 초기 MVP 개발 시 이미지 생성 기능에만 집중함
4. **Why?** 사용자가 생성된 이미지를 어떻게 사용할지 불확실했음
5. **근본 원인**: 이미지 라이프사이클 관리(생성-저장-검색-정리)에 대한 아키텍처 미설계

**해결 방향**: 메타데이터 기반 이미지 갤러리 + 검색/필터 + 정리 기능

---

## 3. Requirements (요구사항) - EARS 형식

### 3.1 Ubiquitous Requirements (항상 적용)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-U-001** | 시스템은 **항상** 이미지 메타데이터를 JSON 형식으로 저장해야 한다 | 데이터 호환성 |
| **REQ-U-002** | 시스템은 **항상** 메타데이터와 이미지 파일 간 일관성을 유지해야 한다 | 데이터 무결성 |
| **REQ-U-003** | 시스템은 **항상** 이미지 파일 존재 여부를 검증해야 한다 | 안전성 보장 |
| **REQ-U-004** | 시스템은 **항상** MCP 도구 응답을 구조화된 형식으로 반환해야 한다 | 기존 패턴 준수 |

### 3.2 Event-Driven Requirements (이벤트 기반)

| ID | WHEN (이벤트) | THEN (동작) |
|----|--------------|-------------|
| **REQ-E-001** | **WHEN** `list_images()` 도구가 호출되면 | **THEN** 시스템은 저장된 모든 이미지 목록을 메타데이터와 함께 반환해야 한다 |
| **REQ-E-002** | **WHEN** `search_images()` 도구가 필터 조건과 함께 호출되면 | **THEN** 시스템은 조건에 맞는 이미지만 필터링하여 반환해야 한다 |
| **REQ-E-003** | **WHEN** `get_image_details()` 도구가 호출되면 | **THEN** 시스템은 해당 이미지의 상세 메타데이터를 반환해야 한다 |
| **REQ-E-004** | **WHEN** `delete_image()` 도구가 호출되면 | **THEN** 시스템은 이미지 파일과 메타데이터를 안전하게 삭제해야 한다 |
| **REQ-E-005** | **WHEN** `cleanup_old_images()` 도구가 호출되면 | **THEN** 시스템은 지정된 기간보다 오래된 이미지를 삭제해야 한다 |
| **REQ-E-006** | **WHEN** 새로운 이미지가 생성되면 | **THEN** 시스템은 자동으로 메타데이터를 생성/갱신해야 한다 |
| **REQ-E-007** | **WHEN** 썸네일 생성이 활성화되면 | **THEN** 시스템은 이미지 목록 조회 시 썸네일을 포함해야 한다 |

### 3.3 State-Driven Requirements (상태 기반)

| ID | IF (조건) | THEN (동작) |
|----|----------|-------------|
| **REQ-S-001** | **IF** 이미지 파일이 존재하지 않으면 | **THEN** 시스템은 메타데이터에서 해당 항목를 제거해야 한다 |
| **REQ-S-002** | **IF** 검색 결과가 없으면 | **THEN** 시스템은 빈 목록과 명확한 메시지를 반환해야 한다 |
| **REQ-S-003** | **IF** 썸네일 생성이 비활성화되어 있으면 | **THEN** 시스템은 원본 이미지 경로만 반환해야 한다 |
| **REQ-S-004** | **IF** 메타데이터 파일이 손상되었으면 | **THEN** 시스템은 이미지 파일에서 정보를 복구 시도해야 한다 |

### 3.4 Unwanted Behavior Requirements (금지 사항)

| ID | 요구사항 | 근거 |
|----|---------|------|
| **REQ-N-001** | 시스템은 **절대** 이미지 삭제 시 사용자 확인 없이 영구 삭제**하지 않아야 한다** | 데이터 보호 |
| **REQ-N-002** | 시스템은 **절대** 메타데이터 없이 이미지를 반환**하지 않아야 한다** | 일관성 보장 |
| **REQ-N-003** | 시스템은 **절대** 디렉토리 외부의 파일에 접근**하지 않아야 한다** | 보안 |
| **REQ-N-004** | 시스템은 **절대** 썸네일 생성 실패로 인해 목록 조회를 중단**하지 않아야 한다** | 가용성 보장 |

### 3.5 Optional Requirements (선택적 기능)

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| **REQ-O-001** | **가능하면** 썸네일 자동 생성 기능을 제공한다 | MEDIUM |
| **REQ-O-002** | **가능하면** 이미지 통계(개수, 총 크기, 스타일별 분포)를 제공한다 | LOW |
| **REQ-O-003** | **가능하면** 이미지 태그/라벨링 기능을 제공한다 | LOW |
| **REQ-O-004** | **가능하면** 이미지 일괄 다운로드 기능을 제공한다 | LOW |

---

## 4. Specifications (세부 명세)

### 4.1 메타데이터 스키마

```json
{
  "images": [
    {
      "id": "img_20250119_abc123",
      "filename": "image_20250119_abc123.png",
      "filepath": "/absolute/path/to/output/images/image_20250119_abc123.png",
      "thumbnail_path": "/absolute/path/to/output/thumbnails/thumb_abc123.png",
      "created_at": "2025-01-19T10:30:00Z",
      "prompt": "A beautiful sunset over mountains",
      "style": "cinematic",
      "aspect_ratio": "16:9",
      "resolution": "1024x576",
      "format": "png",
      "size_bytes": 245678,
      "generation_params": {
        "negative_prompt": null,
        "style_intensity": "normal",
        "seed": 12345
      }
    }
  ],
  "last_updated": "2025-01-19T10:30:00Z",
  "total_count": 1
}
```

### 4.2 MCP 도구 정의

#### 4.2.1 list_images

```python
@mcp.tool()
def list_images(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    저장된 모든 이미지 목록을 반환합니다.

    Args:
        limit: 반환할 최대 이미지 수 (기본값: 50)
        offset: 건너뛸 이미지 수 (페이지네이션용)
        sort_by: 정렬 기준 (created_at, style, size)
        sort_order: 정렬 순서 (asc, desc)

    Returns:
        {
            "success": true,
            "images": [메타데이터 목록],
            "total_count": 전체 개수,
            "returned_count": 반환된 개수
        }
    """
```

#### 4.2.2 search_images

```python
@mcp.tool()
def search_images(
    style: Optional[str] = None,
    date_from: Optional[str] = None,  # ISO 8601 format
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,    # 프롬프트 검색
    format: Optional[str] = None,     # png, jpeg, webp
    min_resolution: Optional[str] = None
) -> Dict[str, Any]:
    """
    조건에 맞는 이미지를 검색합니다.

    Args:
        style: 스타일 필터 (예: "cinematic", "anime")
        date_from: 시작 날짜 (ISO 8601)
        date_to: 종료 날짜 (ISO 8601)
        keyword: 프롬프트 포함 키워드
        format: 이미지 형식
        min_resolution: 최소 해상도 (예: "1024x576")

    Returns:
        {
            "success": true,
            "images": [필터링된 메타데이터],
            "matched_count": 일치하는 개수
        }
    """
```

#### 4.2.3 get_image_details

```python
@mcp.tool()
def get_image_details(image_id: str) -> Dict[str, Any]:
    """
    특정 이미지의 상세 정보를 반환합니다.

    Args:
        image_id: 이미지 ID (예: "img_20250119_abc123")

    Returns:
        {
            "success": true,
            "image": {상세 메타데이터},
            "exists": true
        }
    """
```

#### 4.2.4 delete_image

```python
@mcp.tool()
def delete_image(
    image_id: str,
    confirm: bool = False
) -> Dict[str, Any]:
    """
    특정 이미지를 삭제합니다.

    Args:
        image_id: 이미지 ID
        confirm: 삭제 확인 (안전장치)

    Returns:
        {
            "success": true,
            "deleted": true,
            "message": "이미지가 삭제되었습니다"
        }
    """
```

#### 4.2.5 cleanup_old_images

```python
@mcp.tool()
def cleanup_old_images(
    days: int = 30,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    지정된 일수보다 오래된 이미지를 정리합니다.

    Args:
        days: 보관 기간 (일)
        dry_run: true인 경우 실제 삭제 없이 목록만 반환

    Returns:
        {
            "success": true,
            "deleted_count": 10,
            "freed_space_bytes": 2456780,
            "deleted_images": [삭제된 이미지 ID 목록]
        }
    """
```

### 4.3 ImageGallery 클래스 설계

```python
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class ImageMetadata:
    """이미지 메타데이터 데이터 클래스"""
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

class ImageGallery:
    """
    이미지 갤러리 관리 시스템

    Features:
    - 메타데이터 기반 이미지 관리
    - 검색 및 필터링
    - 썸네일 생성
    - 일괄 정리
    """

    METADATA_FILE = "output/images/metadata.json"
    THUMBNAIL_DIR = "output/thumbnails"

    def __init__(self, enable_thumbnails: bool = False):
        self.images_dir = Path("output/images")
        self.metadata_path = Path(self.METADATA_FILE)
        self.thumbnail_dir = Path(self.THUMBNAIL_DIR)
        self.enable_thumbnails = enable_thumbnails

        # 초기화
        self._ensure_directories()
        self._load_metadata()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리 생성"""
        self.images_dir.mkdir(parents=True, exist_ok=True)
        if self.enable_thumbnails:
            self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> None:
        """메타데이터 로드"""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._images = {
                    img['id']: ImageMetadata(**img)
                    for img in data.get('images', [])
                }
        else:
            self._images = {}

    def _save_metadata(self) -> None:
        """메타데이터 저장"""
        data = {
            'images': [asdict(img) for img in self._images.values()],
            'last_updated': datetime.now().isoformat(),
            'total_count': len(self._images)
        }
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_image(
        self,
        filepath: str,
        prompt: str,
        style: str,
        aspect_ratio: str,
        resolution: str,
        generation_params: Dict[str, Any]
    ) -> ImageMetadata:
        """새로운 이미지 등록"""
        # ... 구현 ...

    def list_images(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at"
    ) -> List[ImageMetadata]:
        """이미지 목록 조회"""
        # ... 구현 ...

    def search_images(self, filters: Dict[str, Any]) -> List[ImageMetadata]:
        """이미지 검색"""
        # ... 구현 ...

    def delete_image(self, image_id: str) -> bool:
        """이미지 삭제"""
        # ... 구현 ...

    def cleanup_old_images(self, days: int, dry_run: bool = False) -> Dict[str, Any]:
        """오래된 이미지 정리"""
        # ... 구현 ...
```

### 4.4 환경 변수 설정

| 환경 변수 | 기본값 | 설명 |
|----------|--------|------|
| `GALLERY_THUMBNAILS_ENABLED` | `false` | 썸네일 생성 활성화 여부 |
| `GALLERY_THUMBNAIL_SIZE` | `256` | 썸네일 크기 (픽셀) |
| `GALLERY_METADATA_PATH` | `output/images/metadata.json` | 메타데이터 파일 경로 |

### 4.5 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Client (Claude Code 등)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │ list_images(), search_images()
                             │ delete_image(), cleanup_old_images()
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       main.py (MCP Server)                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                       MCP Tools                                  │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │ │
│  │  │  list_images()   │  │  search_images() │  │ delete_image()│ │ │
│  │  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │ │
│  └───────────┼────────────────────┼──────────────────────┼─────────┘ │
│              │                    │                      │           │
│              ▼                    ▼                      ▼           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     ImageGallery                                 │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │                  Metadata Management                      │  │ │
│  │  │                                                          │  │ │
│  │  │  1. _load_metadata()  ←→  metadata.json                 │  │ │
│  │  │  2. _save_metadata()  ←→  메타데이터 영속화              │  │ │
│  │  │  3. register_image()  ←→  새 이미지 등록                 │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │                  Search & Filter                          │  │ │
│  │  │                                                          │  │ │
│  │  │  • Style, Date, Keyword, Format filters                  │  │ │
│  │  │  • Pagination support                                    │  │ │
│  │  │  • Sorting options                                       │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │                  File Operations                          │  │ │
│  │  │                                                          │  │ │
│  │  │  • Delete: file + metadata cleanup                       │  │ │
│  │  │  • Validation: existence checks                          │  │ │
│  │  │  • Cleanup: old image removal                            │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   File System           │          │    Optional             │
│                         │          │                         │
│  ┌───────────────────┐  │          │  ┌───────────────────┐  │
│  │ output/images/    │  │          │  │ output/thumbnails/│  │
│  │ *.png, *.jpeg     │  │          │  │ thumb_*.png       │  │
│  └───────────────────┘  │          │  └───────────────────┘  │
│                         │          │                         │
│  ┌───────────────────┐  │          │  (Pillow-based)        │
│  │ metadata.json     │  │          │  thumbnail generation  │
│  └───────────────────┘  │          │                         │
└─────────────────────────┘          └─────────────────────────┘
```

### 4.6 기존 시스템과의 통합

```python
# src/generators/image_gen.py 수정

class ImageGenerator:
    def __init__(self, styles_data: Dict[str, Any]):
        # ... 기존 초기화 코드 ...

        # 갤러리 시스템 초기화
        self._gallery = ImageGallery(
            enable_thumbnails=os.getenv("GALLERY_THUMBNAILS_ENABLED", "false").lower() == "true"
        )

    def generate(self, prompt: str, style_name: Optional[str] = None,
                 aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """이미지 생성 및 갤러리 등록"""

        # ... 기존 이미지 생성 로직 ...

        if result.get("success"):
            # 갤러리에 이미지 등록
            self._gallery.register_image(
                filepath=result["filepath"],
                prompt=prompt,
                style=style or self.default_style,
                aspect_ratio=aspect_ratio,
                resolution=result.get("resolution", "unknown"),
                generation_params={
                    "negative_prompt": negative_prompt,
                    "style_intensity": style_intensity
                }
            )

        return result
```

---

## 5. 추적성 (Traceability)

### 5.1 요구사항 → 구현 매핑

| 요구사항 ID | 구현 위치 | 테스트 시나리오 |
|------------|----------|----------------|
| REQ-U-001 | `_save_metadata()` | TC-001 |
| REQ-U-002 | `delete_image()` | TC-005 |
| REQ-U-003 | `_validate_file_exists()` | TC-006 |
| REQ-U-004 | MCP 도구 반환 형식 | TC-007 |
| REQ-E-001 | `list_images()` | TC-001 |
| REQ-E-002 | `search_images()` | TC-002 |
| REQ-E-003 | `get_image_details()` | TC-003 |
| REQ-E-004 | `delete_image()` | TC-005 |
| REQ-E-005 | `cleanup_old_images()` | TC-008 |
| REQ-E-006 | `register_image()` | TC-004 |
| REQ-E-007 | 썸네일 생성 로직 | TC-009 |
| REQ-S-001 | `_validate_orphaned_entries()` | TC-010 |
| REQ-S-002 | 빈 결과 처리 | TC-011 |
| REQ-S-003 | 썸네일 비활성화 분기 | TC-012 |
| REQ-S-004 | 메타데이터 복구 | TC-013 |
| REQ-N-001 | `confirm` 파라미터 검증 | TC-014 |
| REQ-N-002 | 메타데이터 필수 검증 | TC-015 |
| REQ-N-003 | 경로 검증 | TC-016 |
| REQ-N-004 | 썸네일 예외 처리 | TC-017 |

### 5.2 관련 SPEC

| 관련 SPEC | 관계 | 설명 |
|-----------|------|------|
| SPEC-IMG-001 | 선행 | 이미지 생성 기능 (갤러리 등록 대상) |
| SPEC-IMG-004 | 선행 | 고급 이미지 제어 (메타데이터 포함) |
| SPEC-CACHE-001 | 병렬 | 캐싱 시스템 (메타데이터 참조 가능) |

---

## 6. Constitution 참조

### 6.1 기술 스택 준수

| 항목 | Constitution 정의 | 본 SPEC 준수 |
|------|------------------|--------------|
| Python 버전 | 3.10+ | 준수 (dataclasses, typing 사용) |
| 표준 라이브러리 | pathlib, json | 준수 |
| 환경 변수 관리 | python-dotenv | 준수 |
| 로깅 | logging 모듈 | 준수 |
| 데이터 포맷 | JSON | 준수 |

### 6.2 금지 패턴

- 외부 데이터베이스 사용 금지 (파일 시스템 기반만 허용)
- 전역 상태 변경 금지 (클래스 인스턴스 내부에서만 상태 관리)
- 기존 MCP 도구 인터페이스 변경 금지
- 하드코딩된 경로 사용 금지 (환경 변수/설정 사용)
