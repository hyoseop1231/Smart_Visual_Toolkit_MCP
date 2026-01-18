---
id: SPEC-GALLERY-001
related_spec: spec.md
version: "1.0.0"
status: "draft"
created: "2026-01-19"
updated: "2026-01-19"
author: "Hyoseop"
tags: ["gallery", "image-management", "implementation-plan"]
---

# SPEC-GALLERY-001: 구현 계획

## 1. 개요

본 문서는 이미지 갤러리 및 히스토리 관리 기능의 구현 계획을 정의합니다.

---

## 2. 마일스톤 (우선순위 기반)

### 2.1 1차 마일스톤: 핵심 기능 (HIGH Priority)

**목표**: 기본적인 갤러리 기능 제공

**작업 항목**:
1. ImageGallery 클래스 구현
2. 메타데이터 관리 (로드/저장/등록)
3. MCP 도구 구현 (list_images, search_images, get_image_details)
4. 기존 ImageGenerator와의 통합
5. 기본 테스트 코드 작성

**완료 기준**:
- 이미지 목록 조회 가능
- 스타일/날짜/키워드 필터링 동작
- 메타데이터 자동 저장/로드

### 2.2 2차 마일스톤: 삭제 및 정리 기능 (MEDIUM Priority)

**목표**: 이미지 관리 기능 강화

**작업 항목**:
1. delete_image 도구 구현
2. cleanup_old_images 도구 구현
3. 파일 존재 검증 로직
4. 메타데이터 일관성 유지
5. 삭제 관련 테스트 코드

**완료 기준**:
- 안전한 이미지 삭제 (confirm 플래그)
- 일괄 정리 기능 동작
- 고아 메타데이터 정리

### 2.3 3차 마일스톤: 썸네일 및 고급 기능 (LOW Priority)

**목표**: 사용자 경험 개선

**작업 항목**:
1. 썸네일 생성 기능 구현
2. 이미지 통계 도구 (get_gallery_stats)
3. 페이지네이션 최적화
4. 성능 개선 (대량 이미지 처리)
5. 통합 테스트

**완료 기준**:
- 썸네일 자동 생성
- 통계 정보 제공
- 1000개 이상 이미지 처리 시나리오 통과

---

## 3. 기술 접근 방식

### 3.1 아키텍처 설계

**3-Tier 아키텍처**:

```
MCP Tools Layer (main.py)
    ↓
Gallery Service Layer (src/gallery/image_gallery.py)
    ↓
File System Layer (output/images/, metadata.json)
```

**설계 원칙**:
- 단일 책임: ImageGallery는 갤러리 관리만 담당
- 인터페이스 분리: MCP 도구와 갤러리 로직 분리
- 의존성 주입: ImageGenerator에 ImageGallery 주입

### 3.2 메타데이터 관리 전략

**저장 방식**: JSON 파일 기반

**장점**:
- 데이터베이스 불필요 (간단한 배포)
- 사람이 읽을 수 있는 형식
- 버전 관리 용이
- 마이그레이션 간단

**단점**:
- 대량 데이터 시 성능 저하 (초기에는 문제 없음)
- 동시성 제한 (단일 프로세스 환경에서는 문제 없음)

**향후 확장성**: SQLite 또는 외부 DB로 마이그레이션 가능한 구조 유지

### 3.3 썸네일 생성 전략

**Pillow 라이브러리 사용**:

```python
from PIL import Image

def generate_thumbnail(
    source_path: str,
    dest_path: str,
    size: int = 256
) -> bool:
    """썸네일 생성"""
    try:
        with Image.open(source_path) as img:
            img.thumbnail((size, size))
            img.save(dest_path, format="PNG", optimize=True)
        return True
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}")
        return False
```

**최적화**:
- Lazy generation: 목록 조회 시 최초 1회 생성
- 캐싱: 생성된 썸네일 재사용
- 선택적 활성화: 환경 변수로 제어

### 3.4 검색 및 필터링 구현

**구현 방식**: Python list comprehension + filter

**성능 최적화**:
- 인덱싱: 딕셔너리 기반 O(1) 조회
- 조기 필터링: 가장 좁은 조건 먼저 적용
- 페이지네이션: 전체 로드 방지 (향후 개선)

**향상 계획**:
- 역인덱스 구축 (키워드 검색)
- 날짜 기반 파티셔닝

---

## 4. 구현 상세

### 4.1 파일 구조

```
src/
├── gallery/
│   ├── __init__.py
│   ├── image_gallery.py      # ImageGallery 클래스
│   ├── models.py              # ImageMetadata 데이터 클래스
│   └── utils.py               # 유틸리티 함수
├── generators/
│   └── image_gen.py           # 기존 (수정됨)
└── main.py                    # MCP 서버 (수정됨)

tests/
├── test_gallery.py            # 갤러리 테스트
└── test_integration.py        # 통합 테스트

output/
├── images/
│   └── metadata.json          # 메타데이터 저장소
└── thumbnails/                # 썸네일 저장소 (선택적)
```

### 4.2 핵심 클래스 인터페이스

**ImageGallery**:

```python
class ImageGallery:
    def __init__(self, metadata_path: str, enable_thumbnails: bool)
    def register_image(self, metadata: ImageMetadata) -> None
    def list_images(self, limit: int, offset: int, sort_by: str) -> List[ImageMetadata]
    def search_images(self, filters: Dict[str, Any]) -> List[ImageMetadata]
    def get_image_details(self, image_id: str) -> Optional[ImageMetadata]
    def delete_image(self, image_id: str) -> bool
    def cleanup_old_images(self, days: int, dry_run: bool) -> Dict[str, Any]
    def validate_metadata(self) -> None
    def _load_metadata(self) -> None
    def _save_metadata(self) -> None
```

**ImageMetadata**:

```python
@dataclass
class ImageMetadata:
    id: str
    filename: str
    filepath: str
    thumbnail_path: Optional[str]
    created_at: str  # ISO 8601
    prompt: str
    style: str
    aspect_ratio: str
    resolution: str
    format: str
    size_bytes: int
    generation_params: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImageMetadata
```

### 4.3 기존 시스템 통합

**수정 위치**: `src/generators/image_gen.py`

**변경 사항**:
```python
class ImageGenerator:
    def __init__(self, styles_data: Dict[str, Any]):
        # ... 기존 코드 ...
        self._gallery = ImageGallery(
            metadata_path=os.getenv("GALLERY_METADATA_PATH", "output/images/metadata.json"),
            enable_thumbnails=os.getenv("GALLERY_THUMBNAILS_ENABLED", "false").lower() == "true"
        )

    def generate(self, prompt: str, style_name: Optional[str] = None,
                 aspect_ratio: str = "16:9", **kwargs) -> Dict[str, Any]:
        # ... 기존 이미지 생성 로직 ...

        # 성공 시 갤러리에 등록
        if result.get("success"):
            metadata = ImageMetadata(
                id=self._generate_image_id(result["filepath"]),
                filename=os.path.basename(result["filepath"]),
                filepath=result["filepath"],
                thumbnail_path=None,  # 썸네일은 비동기 생성
                created_at=datetime.now().isoformat(),
                prompt=prompt,
                style=style_name or self.default_style,
                aspect_ratio=aspect_ratio,
                resolution=result.get("resolution", "unknown"),
                format=result.get("format", "png"),
                size_bytes=os.path.getsize(result["filepath"]),
                generation_params=kwargs
            )
            self._gallery.register_image(metadata)

        return result
```

### 4.4 MCP 도구 등록

**추가 위치**: `src/main.py`

```python
# ImageGallery 인스턴스 생성
gallery = ImageGallery(
    metadata_path=os.getenv("GALLERY_METADATA_PATH", "output/images/metadata.json"),
    enable_thumbnails=os.getenv("GALLERY_THUMBNAILS_ENABLED", "false").lower() == "true"
)

@mcp.tool()
def list_images(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """저장된 모든 이미지 목록을 반환합니다."""
    images = gallery.list_images(limit=limit, offset=offset, sort_by=sort_by)
    return {
        "success": True,
        "images": [img.to_dict() for img in images],
        "total_count": len(images)
    }

@mcp.tool()
def search_images(
    style: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    format: Optional[str] = None
) -> Dict[str, Any]:
    """조건에 맞는 이미지를 검색합니다."""
    filters = {k: v for k, v in {
        "style": style,
        "date_from": date_from,
        "date_to": date_to,
        "keyword": keyword,
        "format": format
    }.items() if v is not None}

    images = gallery.search_images(filters)
    return {
        "success": True,
        "images": [img.to_dict() for img in images],
        "matched_count": len(images)
    }

# ... 기타 도구들 ...
```

---

## 5. 테스트 전략

### 5.1 단위 테스트

**대상**: ImageGallery 클래스

**테스트 케이스**:
- 메타데이터 로드/저장
- 이미지 등록
- 검색 필터링 (각 조건별)
- 삭제 및 정리
- 파일 존재 검증

### 5.2 통합 테스트

**대상**: MCP 도구

**테스트 시나리오**:
- 이미지 생성 후 갤러리 조회
- 검색 기능 종합 테스트
- 정리 기능 테스트
- 썸네일 생성 테스트

### 5.3 테스트 커버리지 목표

- 최소 85% 커버리지
- 모든 MCP 도구 테스트 커버
- 에러 케이스 테스트 포함

---

## 6. 위험 요소 및 대응 계획

### 6.1 기술적 위험

| 위험 | 영향 | 확률 | 대응 계획 |
|------|------|------|----------|
| 메타데이터 손상 | HIGH | LOW | 정기 백업, 복구 메커니즘 |
| 대량 파일 성능 저하 | MEDIUM | LOW | 페이지네이션, 인덱싱 |
| Pillow 설치 실패 | LOW | LOW | 선택적 의존성, 예외 처리 |

### 6.2 사용자 경험 위험

| 위험 | 영향 | 대응 계획 |
|------|------|----------|
| 복잡한 검색 인터페이스 | 사용성 저하 | 명확한 도구 설명, 예시 제공 |
| 실수로 이미지 삭제 | 데이터 손실 | confirm 플래그, dry-run 모드 |

### 6.3 운영 위험

| 위험 | 영향 | 대응 계획 |
|------|------|----------|
| 디스크 공간 부족 | 서비스 중단 | 정리 알림, 크기 모니터링 |
| 메타데이터 파일 크기 | 성능 저하 | 주기적인 최적화 |

---

## 7. 성능 최적화 계획

### 7.1 초기 최적화

1. **메모리 캐싱**: 메타데이터 메모리 상 유지
2. **지연 로딩**: 이미지 파일은 필요시만 로드
3. **썸네일 최적화**: 크기 제한, 포맷 최적화

### 7.2 향후 개선

1. **역인덱스**: 키워드 검색용 인덱스
2. **파일 기반 파티셔닝**: 날짜별 파일 분리
3. **데이터베이스 마이그레이션**: 대규모 데이터용 SQLite

---

## 8. 롤백 계획

### 8.1 기능 플래그

환경 변수로 기능 활성화/비활성화:

```bash
# 갤러리 기능 비활성화 시 기존 동작 유지
GALLERY_ENABLED=false
```

### 8.2 데이터 복구

- 메타데이터 자동 백업 (metadata.json.bak)
- 삭제 시 confirm 플래그 필수
- dry-run 모드로 사전 확인

---

## 9. 다음 단계 (Implementation Ready)

본 구현 계획이 승인되면:

1. **/moai:2-run SPEC-GALLERY-001** 명령어로 TDD 구현 시작
2. RED 단계: 실패하는 테스트 작성
3. GREEN 단계: 테스트 통과하는 최소 구현
4. REFACTOR 단계: 코드 품질 개선

**준비 완료 상태**:
- ✅ 요구사항 정의 완료 (spec.md)
- ✅ 구현 계획 수립 완료 (plan.md)
- ✅ 수락 기준 정의 완료 (acceptance.md)
- ✅ 기술 스택 검증 완료
- ✅ 위험 분석 완료
