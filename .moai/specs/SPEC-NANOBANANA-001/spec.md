# SPEC-NANOBANANA-001: 나노바나나 문서 생성 MCP 서버

## 메타데이터

| 항목 | 값 |
|------|-----|
| SPEC ID | SPEC-NANOBANANA-001 |
| 버전 | 1.0.0 |
| 상태 | Draft |
| 작성일 | 2026-01-17 |
| 작성자 | Alfred (Orchestrator) |

---

## 1. 개요

### 1.1 목적

나노바나나 문서 생성 MCP 서버는 Claude 및 기타 MCP 클라이언트가 다양한 문서와 이미지를 생성할 수 있도록 하는 통합 도구 서버입니다.

### 1.2 범위

**포함:**
- Skywork API 통합 (Word, Excel, PowerPoint 생성)
- Google Imagen API 통합 (이미지 생성)
- 스타일 기반 이미지 생성
- 완성된 문서화

**제외:**
- 프롬프트 자동 최적화 (Claude가 자체 처리)
- 문서 편집 기능 (생성만 지원)

---

## 2. 요구사항 (EARS 형식)

### 2.1 문서 생성 도구

#### REQ-DOC-001: Word 문서 생성
**[Event-driven]** 사용자가 `gen_doc` 도구를 쿼리와 함께 호출하면, 시스템은 Skywork API를 통해 Word 문서(.docx)를 생성하고 다운로드 URL을 반환해야 한다.

**인수 테스트:**
- 쿼리: "회의록 템플릿"
- 기대 결과: `.docx` 다운로드 URL 반환
- 타임아웃: 60초 이내

#### REQ-DOC-002: Excel 스프레드시트 생성
**[Event-driven]** 사용자가 `gen_excel` 도구를 쿼리와 함께 호출하면, 시스템은 Skywork API를 통해 Excel 파일(.xlsx)을 생성하고 다운로드 URL을 반환해야 한다.

**인수 테스트:**
- 쿼리: "월별 매출 데이터 표"
- 기대 결과: `.xlsx` 다운로드 URL 반환
- 타임아웃: 60초 이내

#### REQ-DOC-003: PowerPoint 프레젠테이션 생성 (표준)
**[Event-driven]** 사용자가 `gen_ppt` 도구를 쿼리와 함께 호출하면, 시스템은 Skywork API를 통해 고품질 PowerPoint 파일(.pptx)을 생성하고 다운로드 URL을 반환해야 한다.

**인수 테스트:**
- 쿼리: "인공지능 기초 교육 자료 10페이지"
- 기대 결과: `.pptx` 다운로드 URL 반환
- 타임아웃: 600초 (10분) 이내

#### REQ-DOC-004: PowerPoint 프레젠테이션 생성 (빠른)
**[Event-driven]** 사용자가 `gen_ppt_fast` 도구를 쿼리와 함께 호출하면, 시스템은 Skywork API를 통해 빠르게 PowerPoint 파일(.pptx)을 생성하고 다운로드 URL을 반환해야 한다.

**인수 테스트:**
- 쿼리: "AI 기술 소개 프레젠테이션 5장"
- 기대 결과: `.pptx` 다운로드 URL 반환
- 타임아웃: 120초 이내

### 2.2 이미지 생성 도구

#### REQ-IMG-001: 스타일 기반 이미지 생성
**[Event-driven]** 사용자가 `generate_image` 도구를 프롬프트와 선택적 스타일명으로 호출하면, 시스템은 Google Imagen API를 통해 이미지를 생성하고 결과를 반환해야 한다.

**인수 테스트:**
- 프롬프트: "A serene mountain landscape"
- 스타일: "Watercolor Dreams"
- 기대 결과: 이미지 생성 성공 메시지

#### REQ-IMG-002: 스타일 목록 조회
**[Event-driven]** 사용자가 `list_styles` 도구를 호출하면, 시스템은 사용 가능한 모든 이미지 스타일 목록을 반환해야 한다.

**인수 테스트:**
- 기대 결과: 15개 이상의 스타일 목록

### 2.3 설정 도구

#### REQ-CFG-001: Skywork 설정 조회
**[Event-driven]** 사용자가 `get_skywork_config` 도구를 호출하면, 시스템은 Skywork SSE 연결을 위한 서명된 URL을 생성하여 반환해야 한다.

**인수 테스트:**
- 기대 결과: `secret_id`, `sign`, `sse_url` 포함

### 2.4 비기능 요구사항

#### REQ-NFR-001: 에러 처리
**[Ubiquitous]** 시스템은 모든 API 호출에서 발생하는 오류를 적절히 처리하고 사용자에게 명확한 오류 메시지를 반환해야 한다.

#### REQ-NFR-002: 재시도 로직
**[State-driven]** SSE 연결이 실패한 경우, 시스템은 지수 백오프(exponential backoff)를 사용하여 최대 3회까지 재시도해야 한다.

#### REQ-NFR-003: 리소스 정리
**[Event-driven]** 클라이언트 연결이 종료되면, 시스템은 모든 비동기 태스크와 HTTP 연결을 적절히 정리해야 한다.

---

## 3. 아키텍처

### 3.1 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (Claude)                   │
└─────────────────────────┬───────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Smart Visual Toolkit MCP Server             │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    FastMCP Layer                    ││
│  │  - list_styles()                                    ││
│  │  - generate_image()                                 ││
│  │  - get_skywork_config()                            ││
│  │  - gen_doc() / gen_excel() / gen_ppt()             ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│  ┌───────────────────────┼───────────────────────────┐  │
│  │                       ▼                           │  │
│  │  ┌─────────────┐  ┌─────────────────────────────┐ │  │
│  │  │ ImageGen    │  │     SkyworkClient           │ │  │
│  │  │ + Cache     │  │     (SSE + JSON-RPC)        │ │  │
│  │  └──────┬──────┘  └──────────────┬──────────────┘ │  │
│  └─────────┼────────────────────────┼────────────────┘  │
└────────────┼────────────────────────┼───────────────────┘
             │                        │
             ▼                        ▼
    ┌────────────────┐      ┌────────────────────┐
    │ Google Imagen  │      │   Skywork API      │
    │     API        │      │   (SSE Endpoint)   │
    └────────────────┘      └────────────────────┘
```

### 3.2 파일 구조

```
smart-visual-toolkit/
├── src/
│   ├── main.py                 # MCP 서버 진입점 + 도구 정의
│   ├── generators/
│   │   ├── image_gen.py        # Google Imagen 통합
│   │   └── cache.py            # LRU + TTL 캐시
│   ├── skywork/
│   │   └── client.py           # Skywork SSE/JSON-RPC 클라이언트
│   └── resources/
│       └── banana_styles.json  # 이미지 스타일 정의
├── tests/
│   ├── test_cache.py
│   ├── test_skywork_client.py
│   └── test_image_gen_cache.py
├── .env                        # 환경 변수 (API 키)
├── pyproject.toml              # 의존성 및 프로젝트 설정
└── README.md                   # 문서화
```

---

## 4. 구현 계획

### 4.1 현재 상태 (완료)

- [x] Skywork 클라이언트 구현 (SPEC-SKYWORK-001)
- [x] 이미지 생성기 구현
- [x] 캐시 시스템 구현 (SPEC-CACHE-001)
- [x] MCP 도구 등록
- [x] API 테스트 완료 (gen_doc, gen_excel, gen_ppt, gen_ppt_fast)

### 4.2 남은 작업

1. **품질 수정**
   - [ ] 실패한 테스트 수정 (request_timeout 300 → 600)
   - [ ] pyproject.toml에 린팅 도구 추가

2. **문서화**
   - [ ] README.md 완성
   - [ ] 도구별 사용 예시 추가
   - [ ] 설치 및 설정 가이드

3. **마무리**
   - [ ] Git 커밋 및 푸시

---

## 5. 테스트 계획

### 5.1 단위 테스트

| 테스트 파일 | 대상 | 상태 |
|------------|------|------|
| test_cache.py | ImageCache | ✅ 완료 |
| test_skywork_client.py | SkyworkClient | ⚠️ 1개 실패 |
| test_image_gen_cache.py | ImageGenerator | ✅ 완료 |

### 5.2 통합 테스트 (수동)

| 도구 | 테스트 결과 |
|------|------------|
| gen_doc | ✅ 회의록_템플릿.docx 생성 성공 |
| gen_excel | ✅ 2024년_월별_매출_데이터.xlsx 생성 성공 |
| gen_ppt | ✅ 인공지능 기초 교육 자료.pptx 생성 성공 |
| gen_ppt_fast | ✅ AI 기술 소개.pptx 생성 성공 |

---

## 6. 승인

| 역할 | 이름 | 날짜 | 서명 |
|------|------|------|------|
| 작성자 | Alfred | 2026-01-17 | ✓ |
| 검토자 | Hyoseop | - | - |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-01-17 | 초안 작성 |
