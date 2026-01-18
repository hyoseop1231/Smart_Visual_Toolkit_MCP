```yaml
SPEC_ID: SPEC-IMG-002
TITLE: 다중 이미지 형식 지원 시스템
STATUS: Planned
PRIORITY: HIGH
AUTHOR: Hyoseop
CREATED: 2025-01-18
DOMAIN: Image Processing
LIFECYCLE: spec-anchored
RELATED: []
VERSION: 1.0.0
```

# SPEC-IMG-002: 다중 이미지 형식 지원 시스템

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2025-01-18 | 초기 SPEC 작성 | Hyoseop |

---

## 1. 개요 (Overview)

이 SPEC은 Smart Visual Toolkit MCP의 이미지 생성 시스템에서 WebP, JPEG, PNG 형식을 지원하기 위한 다중 형식 출력 기능을 정의합니다.

### 1.1 배경

현재 시스템은 PNG 형식만 지원하여 파일 크기가 크고 호환성이 제한적입니다. WebP와 JPEG 형식 지원을 통해 파일 크기 최적화와 더 넓은 호환성을 제공해야 합니다.

### 1.2 목표

- WebP 형식 지원으로 파일 크기 최적화
- JPEG 형식 지원으로 광범위한 호환성 제공
- PNG 형식 유지로 무손실 품질 보장
- 사용자가 출력 형식을 선택할 수 있는 유연성 제공

---

## 2. 환경 (Environment)

### 2.1 실행 환경

- **OS**: macOS, Linux, Windows
- **Python 버전**: 3.11+
- **MCP 서버**: Model Context Protocol 서버 환경

### 2.2 의존성

- **Pillow**: 이미지 처리 및 형식 변환 (>= 10.0.0)
- **io**: 이미지 메모리 처리

### 2.3 제약사항

- WebP 지원은 libwebp가 필요한 환경에서만 작동
- JPEG 품질 매개변수는 1-100 범위로 제한
- PNG는 무손실이므로 품질 매개변수가 적용되지 않음

---

## 3. 가정 (Assumptions)

### 3.1 기술적 가정

- 사용자의 MCP 클라이언트가 WebP 형식을 디코딩할 수 있다고 가정
- JPEG/WebP 변환에 필요한 시스템 라이브러리가 설치되어 있다고 가정

### 3.2 비즈니스 가정

- 사용자는 파일 크기와 이미지 품질 간의 트레이드오프를 이해한다고 가정
- PNG 형식을 기본값으로 유지하면 기존 사용자에게 영향이 없다고 가정

---

## 4. 요구사항 (Requirements)

### 4.1 필수 요구사항 (SHALL)

#### REQ-IMG-001: WebP 형식 지원
**EARS Pattern**: Event-Driven
**한국어**: WHEN 사용자가 WebP 형식을 요청하면, 시스템은 WebP 형식으로 이미지를 출력해야 한다
**영어**: WHEN the user requests WebP format, the system SHALL output the image in WebP format

#### REQ-IMG-002: JPEG 형식 지원
**EARS Pattern**: Event-Driven
**한국어**: WHEN 사용자가 JPEG 형식을 요청하면, 시스템은 JPEG 형식으로 이미지를 출력해야 한다
**영어**: WHEN the user requests JPEG format, the system SHALL output the image in JPEG format

#### REQ-IMG-003: PNG 형식 유지
**EARS Pattern**: Ubiquitous
**한국어**: 시스템은 항상 PNG 형식 지원을 유지해야 한다
**영어**: The system SHALL ALWAYS maintain PNG format support

#### REQ-IMG-004: 형식 매개변수 지정
**EARS Pattern**: Event-Driven
**한국어**: WHEN 이미지 생성 요청이 들어오면, 시스템은 형식 매개변수를 허용해야 한다
**영어**: WHEN an image generation request is received, the system SHALL accept format parameter

#### REQ-IMG-005: JPEG 품질 제어
**EARS Pattern**: State-Driven
**한국어**: IF 형식이 JPEG이면, 시스템은 1-100 범위의 품질 매개변수를 지원해야 한다
**영어**: IF the format is JPEG, the system SHALL support quality parameter in range 1-100

#### REQ-IMG-006: WebP 품질 제어
**EARS Pattern**: State-Driven
**한국어**: IF 형식이 WebP이면, 시스템은 품질 제어를 지원해야 한다
**영어**: IF the format is WebP, the system SHALL support quality control

### 4.2 권장 요구사항 (SHOULD)

#### REQ-IMG-007: 기본 형식 유지
**EARS Pattern**: Ubiquitous
**한국어**: 시스템은 기본 형식으로 PNG를 사용해야 한다
**영어**: The system SHOULD use PNG as the default format

#### REQ-IMG-008: 형식 자동 감지
**EARS Pattern**: Event-Driven
**한국어**: WHEN 파일 확장자가 제공되면, 시스템은 형식을 자동으로 감지해야 한다
**영어**: WHEN a file extension is provided, the system SHOULD automatically detect the format

### 4.3 선택 요구사항 (MAY)

#### REQ-IMG-009: 프로그레시브 JPEG
**EARS Pattern**: Optional
**한국어**: 가능하면 시스템은 프로그레시브 JPEG를 지원해야 한다
**영어**: WHERE POSSIBLE, the system MAY support progressive JPEG

#### REQ-IMG-010: WebP 애니메이션
**EARS Pattern**: Optional
**한국어**: 가능하면 시스템은 WebP 애니메이션을 지원해야 한다
**영어**: WHERE POSSIBLE, the system MAY support WebP animation

---

## 5. 상세 사양 (Specifications)

### 5.1 API 인터페이스

#### 5.1.1 이미지 생성 매개변수

```python
{
    "format": "png" | "jpeg" | "webp",  # 출력 형식
    "quality": int,                      # JPEG/WebP 품질 (1-100, 선택사항)
    "prompt": str,                       # 이미지 생성 프롬프트
    "size": tuple[int, int]              # 이미지 크기
}
```

#### 5.1.2 MIME 타입 매핑

| 형식 | MIME 타입 | 파일 확장자 |
|------|-----------|-------------|
| PNG | image/png | .png |
| JPEG | image/jpeg | .jpg, .jpeg |
| WebP | image/webp | .webp |

### 5.2 형식별 처리 로직

#### 5.2.1 PNG 처리

```python
def save_as_png(image, output_path):
    """무손실 PNG 저장"""
    image.save(output_path, format='PNG', optimize=True)
```

#### 5.2.2 JPEG 처리

```python
def save_as_jpeg(image, output_path, quality=95):
    """JPEG 저장 (품질 제어)"""
    if not (1 <= quality <= 100):
        raise ValueError("Quality must be between 1 and 100")
    # RGB 변환 (JPEG는 투명도 미지원)
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    image.save(output_path, format='JPEG', quality=quality)
```

#### 5.2.3 WebP 처리

```python
def save_as_webp(image, output_path, quality=95):
    """WebP 저장 (품질 제어)"""
    if not (1 <= quality <= 100):
        raise ValueError("Quality must be between 1 and 100")
    image.save(output_path, format='WebP', quality=quality)
```

### 5.3 기본값 동작

- **format**: 명시되지 않은 경우 "png" 사용
- **quality**: JPEG/WebP의 경우 기본값 95
- **fallback**: 지원하지 않는 형식 요청 시 ValueError 발생

---

## 6. 추적성 (Traceability)

### 6.1 요구사항-구현 매핑

| 요구사항 ID | 구현 요소 | 상태 |
|-------------|-----------|------|
| REQ-IMG-001 | save_image() WebP 분기 | Planned |
| REQ-IMG-002 | save_image() JPEG 분기 | Planned |
| REQ-IMG-003 | save_image() PNG 분기 | Planned |
| REQ-IMG-004 | format 매개변수 처리 | Planned |
| REQ-IMG-005 | JPEG quality 검증 | Planned |
| REQ-IMG-006 | WebP quality 검증 | Planned |
| REQ-IMG-007 | 기본값 format="png" | Planned |
| REQ-IMG-008 | 확장자 기반 감지 로직 | Planned |

### 6.2 테스트 커버리지

- 모든 형식(PNG, JPEG, WebP)에 대한 단위 테스트 필요
- 품질 매개변수 경계값 테스트 필요
- 잘못된 형식 요청에 대한 예외 처리 테스트 필요

---

## 7. 참조 (References)

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [WebP Specification](https://developers.google.com/speed/webp)
- [JPEG Specification](https://www.w3.org/Graphics/JPEG/)
- SPEC-IMG-001: 기본 이미지 생성 시스템

---

**TAG BLOCK END**
