# 나노바나나 문서 생성 MCP 서버

Claude 및 기타 MCP 클라이언트를 위한 **문서 생성 + 이미지 생성 통합 도구 서버**입니다.

## 주요 기능

### 문서 생성 (Skywork API)

| 도구 | 설명 | 예시 |
|------|------|------|
| `gen_doc` | Word 문서 생성 | "회의록 템플릿 만들어줘" |
| `gen_excel` | Excel 스프레드시트 생성 | "월별 매출 데이터 표 만들어줘" |
| `gen_ppt` | PowerPoint 생성 (고품질) | "AI 기술 소개 10페이지" |
| `gen_ppt_fast` | PowerPoint 생성 (빠른) | "회사 소개 5장" |

### 이미지 생성 (Google Imagen)

| 도구 | 설명 | 예시 |
|------|------|------|
| `generate_image` | 스타일 기반 이미지 생성 | "산 풍경", 스타일: "Watercolor Dreams" |
| `list_styles` | 사용 가능한 스타일 목록 | 15종 이상의 나노바나나 스타일 |

### 설정 도구

| 도구 | 설명 |
|------|------|
| `get_skywork_config` | Skywork SSE URL 자동 생성 |

## 설치

### 요구사항

- Python 3.10+
- uv (권장) 또는 pip

### 설치 방법

```bash
# uv 사용 (권장)
uv sync

# 또는 pip 사용
pip install -e .
```

### API 키 설정

프로젝트 루트에 `.env` 파일 생성:

```ini
# Google Gemini API Key (이미지 생성용)
# https://aistudio.google.com/app/apikey 에서 발급
GOOGLE_API_KEY=your_google_api_key_here

# Skywork API Credentials (문서 생성용)
# https://skywork.ai/ 에서 발급
SKYWORK_SECRET_ID=your_secret_id
SKYWORK_SECRET_KEY=your_secret_key
```

## 실행

```bash
# MCP 서버 실행
uv run src/main.py
```

## MCP 클라이언트 설정

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uv",
      "args": ["run", "src/main.py"],
      "cwd": "/path/to/Smart_Visual_Toolkit_MCP"
    }
  }
}
```

### Cursor IDE

1. **Settings** → **Models** → **MCP**
2. **Add New MCP Server**
3. 설정:
   - Name: `nanobanana`
   - Type: `stdio`
   - Command: `uv run src/main.py`

### Obsidian Smart Composer

```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uv",
      "args": ["run", "src/main.py"],
      "cwd": "/path/to/Smart_Visual_Toolkit_MCP"
    }
  }
}
```

## 사용 예시

### 문서 생성

```
"회의록 양식 Word 문서 만들어줘"
→ gen_doc 호출 → .docx 다운로드 URL 반환

"2024년 월별 매출 데이터 Excel 만들어줘"
→ gen_excel 호출 → .xlsx 다운로드 URL 반환

"인공지능 기초 교육 자료 PPT 10페이지"
→ gen_ppt 호출 → .pptx 다운로드 URL 반환 (5-10분 소요)

"회사 소개 PPT 빠르게 만들어줘"
→ gen_ppt_fast 호출 → .pptx 다운로드 URL 반환 (1-2분)
```

### 이미지 생성

```
"산 풍경 이미지 만들어줘"
→ generate_image 호출 → 이미지 생성

"Clay 3D 스타일로 귀여운 캐릭터 그려줘"
→ generate_image(style_name="Clay 3D") 호출

"사용 가능한 스타일 보여줘"
→ list_styles 호출 → 15종 스타일 목록
```

## 프로젝트 구조

```
smart-visual-toolkit/
├── src/
│   ├── main.py                 # MCP 서버 진입점 + 도구 정의
│   ├── generators/
│   │   ├── image_gen.py        # Google Imagen 통합 + 캐시
│   │   └── cache.py            # LRU + TTL 캐시
│   ├── skywork/
│   │   └── client.py           # Skywork SSE/JSON-RPC 클라이언트
│   └── resources/
│       └── banana_styles.json  # 나노바나나 스타일 정의
├── tests/                      # 단위 테스트 (59개)
├── .env                        # 환경 변수 (API 키)
├── pyproject.toml              # 프로젝트 설정
└── README.md
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (Claude)                   │
└─────────────────────────┬───────────────────────────────┘
                          │ MCP Protocol (stdio)
                          ▼
┌─────────────────────────────────────────────────────────┐
│              나노바나나 문서 생성 MCP 서버               │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    FastMCP Layer                    ││
│  │  list_styles / generate_image / get_skywork_config  ││
│  │  gen_doc / gen_excel / gen_ppt / gen_ppt_fast       ││
│  └─────────────────────────────────────────────────────┘│
│  ┌───────────────────────┬──────────────────────────┐   │
│  │     ImageGenerator    │     SkyworkClient        │   │
│  │     + Cache (LRU)     │   (SSE + JSON-RPC)       │   │
│  └───────────┬───────────┴───────────┬──────────────┘   │
└──────────────┼───────────────────────┼──────────────────┘
               │                       │
               ▼                       ▼
      ┌────────────────┐      ┌────────────────────┐
      │ Google Imagen  │      │   Skywork API      │
      │     API        │      │   (SSE Endpoint)   │
      └────────────────┘      └────────────────────┘
```

## 개발

### 테스트 실행

```bash
# 전체 테스트
uv run pytest tests/ -v

# 커버리지 포함
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### 현재 테스트 상태

- 총 59개 테스트
- 100% 통과
- 커버리지: 73% (main.py 제외 시 89%)

## 기술 스택

- **언어**: Python 3.10+
- **MCP 프레임워크**: FastMCP (mcp>=0.1.0)
- **HTTP 클라이언트**: httpx (비동기)
- **이미지 생성**: Google Generative AI (Imagen 4.0)
- **문서 생성**: Skywork API (SSE + JSON-RPC 2.0)

## 라이선스

MIT License

## 관련 SPEC

- SPEC-NANOBANANA-001: 나노바나나 문서 생성 MCP 서버
- SPEC-SKYWORK-001: Skywork API 품질 개선
- SPEC-CACHE-001: 이미지 캐시 시스템
- SPEC-IMG-001: 배치 이미지 생성 시스템
