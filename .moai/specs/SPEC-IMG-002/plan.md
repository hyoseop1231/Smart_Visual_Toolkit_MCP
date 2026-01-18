# SPEC-IMG-002: 구현 계획

## TAG BLOCK
**SPEC_ID**: SPEC-IMG-002
**DOCUMENT**: plan.md
**VERSION**: 1.0.0
**STATUS**: Planned
**LAST_UPDATED**: 2025-01-18
**TAG_BLOCK_END**
---

## 1. 개요 (Overview)

다중 이미지 형식 지원 시스템의 구현 전략과 기술 접근 방식을 정의합니다.

---

## 2. 구현 마일스톤 (Milestones)

### 2.1 1단계: 핵심 형식 지원 (Priority: HIGH)

**목표**: PNG, JPEG, WebP 세 가지 형식에 대한 기본 지원 구현

- [ ] 형식 매개변수 처리 로직 구현
- [ ] PNG 형식 저장 (기존 기능 유지)
- [ ] JPEG 형식 저장 구현
- [ ] WebP 형식 저장 구현
- [ ] 기본 형식으로 PNG 설정

### 2.2 2단계: 품질 제어 (Priority: HIGH)

**목표**: JPEG와 WebP에 대한 품질 매개변수 지원

- [ ] 품질 매개변수 검증 로직 (1-100 범위)
- [ ] JPEG 품질 적용
- [ ] WebP 품질 적용
- [ ] 기본 품질값 95 설정

### 2.3 3단계: 투명도 처리 (Priority: MEDIUM)

**목표**: JPEG 형식에서의 투명도 처리 개선

- [ ] RGBA → RGB 변환 로직
- [ ] 흰색 배경 합성 구현
- [ ] 사용자 정의 배경색 옵션 (선택사항)

### 2.4 4단계: 고급 기능 (Priority: LOW)

**목표**: 선택적 고급 기능 구현

- [ ] 파일 확장자 기반 형식 자동 감지
- [ ] 프로그레시브 JPEG 지원
- [ ] WebP 애니메이션 지원 (필요 시)

---

## 3. 기술 접근 방식 (Technical Approach)

### 3.1 아키텍처 설계

#### 3.1.1 형식 변환기 패턴

전략 패턴(Strategy Pattern)을 사용하여 형식별 처리를 분리:

```python
from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO

class ImageFormatHandler(ABC):
    @abstractmethod
    def save(self, image: Image.Image, output: BytesIO, **kwargs) -> None:
        pass

class PNGHandler(ImageFormatHandler):
    def save(self, image: Image.Image, output: BytesIO, **kwargs) -> None:
        image.save(output, format='PNG', optimize=True)

class JPEGHandler(ImageFormatHandler):
    def save(self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs) -> None:
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        image.save(output, format='JPEG', quality=quality)

class WebPHandler(ImageFormatHandler):
    def save(self, image: Image.Image, output: BytesIO, quality: int = 95, **kwargs) -> None:
        image.save(output, format='WebP', quality=quality)

# 형식 핸들러 레지스트리
FORMAT_HANDLERS = {
    'png': PNGHandler(),
    'jpeg': JPEGHandler(),
    'jpg': JPEGHandler(),
    'webp': WebPHandler(),
}
```

#### 3.1.2 통합 인터페이스

```python
def save_image(
    image: Image.Image,
    format: str = 'png',
    quality: int = 95,
    output_path: str = None
) -> BytesIO:
    """
    지정된 형식으로 이미지 저장

    Args:
        image: PIL 이미지 객체
        format: 출력 형식 (png, jpeg, webp)
        quality: JPEG/WebP 품질 (1-100)
        output_path: 저장 경로 (None인 경우 BytesIO 반환)

    Returns:
        BytesIO: 이미지 데이터

    Raises:
        ValueError: 지원하지 않는 형식이거나 품질 범위가 잘못된 경우
    """
    format = format.lower()
    if format not in FORMAT_HANDLERS:
        raise ValueError(f"Unsupported format: {format}. Supported: {list(FORMAT_HANDLERS.keys())}")

    if quality < 1 or quality > 100:
        raise ValueError(f"Quality must be between 1 and 100, got {quality}")

    output = BytesIO()
    handler = FORMAT_HANDLERS[format]
    handler.save(image, output, quality=quality)
    output.seek(0)

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(output.getvalue())

    return output
```

### 3.2 데이터 모델

#### 3.2.1 이미지 생성 요청 모델

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ImageGenerationRequest(BaseModel):
    prompt: str
    format: Literal['png', 'jpeg', 'jpg', 'webp'] = Field(default='png')
    quality: int = Field(default=95, ge=1, le=100)
    size: tuple[int, int] = (1024, 1024)

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "A sunset over mountains",
                    "format": "webp",
                    "quality": 90,
                    "size": (1024, 1024)
                }
            ]
        }
    }
```

### 3.3 기술 스택

- **이미지 처리**: Pillow 10.0.0+
- **데이터 검증**: Pydantic 2.0+
- **테스트**: pytest, pytest-asyncio
- **타입 검사**: mypy

---

## 4. 파일 구조 (File Structure)

```
src/
├── image_processing/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── base.py          # ImageFormatHandler 기본 클래스
│   │   ├── png.py           # PNGHandler
│   │   ├── jpeg.py          # JPEGHandler
│   │   └── webp.py          # WebPHandler
│   ├── models.py            # ImageGenerationRequest 모델
│   └── converter.py         # save_image 통합 함수
tests/
├── test_format_handlers.py  # 형식 핸들러 단위 테스트
├── test_converter.py        # 변환기 통합 테스트
└── test_quality.py          # 품질 매개변수 테스트
```

---

## 5. 품질 게이트 (Quality Gates)

### 5.1 코드 품질

- [ ] `ruff` 린터 통과 (0 경고)
- [ ] `mypy` 타입 검증 통과
- [ ] `black` 포매터 적용
- [ ] 테스트 커버리지 85% 이상

### 5.2 기능 테스트

- [ ] 모든 형식(PNG, JPEG, WebP) 저장 테스트 통과
- [ ] 품질 매개변수 경계값 테스트 통과
- [ ] 잘못된 형식 요청 시 예외 발생 확인
- [ ] JPEG 투명도 처리 테스트 통과

### 5.3 성능 테스트

- [ ] 1024x1024 이미지 WebP 변환: < 1초
- [ ] 1024x1024 이미지 JPEG 변환: < 0.5초
- [ ] 메모리 사용량: < 100MB (단일 이미지)

---

## 6. 위험 및 대응 계획 (Risks and Mitigation)

### 6.1 기술적 위험

| 위험 | 영향 | 확률 | 대응 계획 |
|------|------|------|-----------|
| WebP 라이브러리 미설치 | HIGH | MEDIUM | 설치 검증 로직 추가, 명확한 에러 메시지 제공 |
| JPEG 투명도 손실 | MEDIUM | HIGH | 흰색 배경 합성 기본 제공, 사용자 정의 옵션 |
| WebP 디코딩 호환성 | MEDIUM | MEDIUM | PNG fallback 메커니즘 문서화 |

### 6.2 사용자 경험 위험

| 위험 | 영향 | 확률 | 대응 계획 |
|------|------|------|-----------|
| 기본 형식 변경으로 인한 혼란 | MEDIUM | LOW | 기본값을 PNG로 유지하여 후방 호환성 보장 |
| 품질 매개변수 오해 | LOW | MEDIUM | 문서에 품질 범위와 효과 명확히 설명 |

---

## 7. 구현 의존성 (Dependencies)

### 7.1 외부 의존성

```
Pillow>=10.0.0
pydantic>=2.0.0
```

### 7.2 내부 의존성

- SPEC-IMG-001: 기본 이미지 생성 시스템
- 기존 MCP 서버 인프라

---

## 8. 롤아웃 계획 (Rollout Plan)

### 8.1 테스트 환경

1. 단위 테스트 작성 및 통과
2. 통합 테스트 작성 및 통과
3. 수동 테스트 수행 (다양한 이미지 및 형식 조합)

### 8.2 배포 단계

1. **Alpha**: 개발자 테스트
2. **Beta**: 제한된 사용자 그룹 테스트
3. **GA**: 일반 배포

---

## 9. 모니터링 및 메트릭 (Monitoring)

### 9.1 성능 메트릭

- 형식별 변환 시간
- 형식별 출력 파일 크기
- 형식별 사용 빈도

### 9.2 오류 메트릭

- 형식 지원 실패율
- 품질 매개변수 오류율
- 라이브러리 설치 실패율

---

**TAG BLOCK END**
