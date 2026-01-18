# Smart Visual Toolkit (MCP Server)

> **Version 0.1.0** | AI 이미지 생성 및 문서 자동화를 위한 MCP 서버

Obsidian Smart Composer와 연동하여 **나노바나나(Nano Banana) 스타일의 AI 이미지 생성**을 제공하고, **Skywork MCP Server**를 통한 문서 생성 기능을 통합한 올인원 툴킷입니다.

---

## 주요 기능

### 1. AI 이미지 생성 (`generate_image`)
- **나노바나나 스타일 적용**: 15종의 시각적 스타일 패턴을 자동으로 프롬프트에 적용
- **Google Imagen 4.0-fast**: 최신 고품질 이미지 생성 모델 사용
- **Obsidian 연동**: 노트 내용을 기반으로 LLM이 적절한 스타일을 추천하여 이미지 생성

### 2. 스타일 탐색 (`list_styles`)
- 사용 가능한 모든 시각적 스타일과 키워드를 조회

### 3. Skywork 문서 생성 (통합 Proxy)
- **`gen_doc`**: Word 문서 생성/편집
- **`gen_excel`**: Excel 스프레드시트 생성
- **`gen_ppt`**: PowerPoint 프레젠테이션 생성
- **`gen_ppt_fast`**: 빠른 PPT 생성

### 4. Skywork 설정 도우미 (`get_skywork_config`)
- Skywork MCP Server의 인증 URL을 자동 생성
- MD5 서명 계산을 대신 처리하여 바로 사용 가능한 JSON 설정 제공

---

## 사용 가능한 스타일 (15종)

| 스타일명 | 설명 | 키워드 |
|---------|------|--------|
| Corporate Memphis | 모던 테크 기업 스타일 | Corporate Memphis, 3D Render, Confetti |
| Flat Corporate | 비즈니스 프레젠테이션용 플랫 디자인 | Flat illustration, Corporate, Memphis |
| Isometric Infographic | 데이터 시각화용 3D 인포그래픽 | Infographic, Isometric, Colorful |
| Minimal Line Art | 심플하고 우아한 흑백 드로잉 | Minimal, Monochrome, Line Art |
| Doodle Notebook | 손으로 그린 듯한 캐주얼 스타일 | Doodle, Notebook, Blue Ink |
| Clay 3D | 귀여운 클레이 모델링 스타일 | Clay, Stopmotion, Cute |
| Watercolor Map | 수채화 페인팅 스타일 | Watercolor, Map, Fantasy |
| Pixel Art | 레트로 게임 미학 | Pixel Art, Retro Game, 8-bit |
| Glassmorphism | 반투명 현대 UI 트렌드 | Glassmorphism, Dark, Blur |
| Cyberpunk | 미래적 네온 하이테크 | Cyberpunk, Blue, Circuit |
| Synthwave | 80년대 레트로 퓨처리스틱 | Synthwave, Sunset, Retro Grid |
| Paper Cutout | 레이어와 그림자가 있는 종이 컷아웃 | Paper Cutout, Layered, Shadow |
| Ukiyo-e Pop | 일본 레트로 팝아트 | Ukiyo-e, City Pop, Halftone |
| Low Poly | 기하학적 3D 추상 | Low Poly, 3D, Geometric |
| Abstract Fluid | 유체 그라디언트 추상 | Abstract, Fluid, Gradient |

---

## 프로젝트 구조

```text
Smart_Visual_Toolkit_MCP/
├── src/
│   ├── generators/
│   │   └── image_gen.py      # 이미지 생성 로직 (Imagen 4.0 API)
│   ├── resources/
│   │   └── banana_styles.json # 나노바나나 스타일 템플릿 DB
│   └── main.py               # MCP 서버 엔트리포인트 (Tools 정의)
├── output/
│   └── images/               # 생성된 이미지 저장 폴더
├── .env                      # 환경 변수 (API 키)
├── pyproject.toml            # 프로젝트 설정 및 의존성
└── README.md                 # 문서
```

---

## 설치 및 실행 방법

### 1. 환경 설정

Python 3.10 이상이 필요합니다.

```bash
# 저장소 클론
git clone https://github.com/hyoseop1231/Smart_Visual_Toolkit_MCP.git
cd Smart_Visual_Toolkit_MCP

# uv를 사용한 설치 (권장)
uv sync

# 또는 pip 사용
pip install -e .
```

### 2. API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요.

```ini
# Google Gemini API Key (이미지 생성용 - 필수)
GOOGLE_API_KEY=your_google_api_key_here

# Skywork 자격증명 (문서 생성용 - 선택)
SKYWORK_SECRET_ID=your_skywork_secret_id
SKYWORK_SECRET_KEY=your_skywork_secret_key
```

### 3. 서버 실행

```bash
uv run src/main.py
```

---

## MCP 클라이언트 설정

### Obsidian Smart Composer

`mcpServers` 설정에 추가:

```json
{
  "mcpServers": {
    "smart-visual-toolkit": {
      "command": "uv",
      "args": ["run", "/path/to/Smart_Visual_Toolkit_MCP/src/main.py"]
    }
  }
}
```

### Cursor IDE

1. **Settings** > **Models** > **MCP** 이동
2. **Add New MCP Server** 클릭
3. 설정:
   - **Name**: Smart-Visual-Toolkit
   - **Type**: stdio
   - **Command**: `uv run /path/to/Smart_Visual_Toolkit_MCP/src/main.py`

---

## 사용 예시

### 이미지 생성
```
"이 노트의 내용을 요약해서 'Clay 3D' 스타일로 귀여운 이미지를 만들어줘."
"Cyberpunk 스타일로 미래 도시 이미지 생성해줘."
```

### 스타일 조회
```
"사용 가능한 이미지 스타일 목록 보여줘."
```

### 문서 생성 (Skywork 연동)
```
"이 노트를 바탕으로 발표 자료(PPT)를 만들어줘."
"프로젝트 보고서를 Word 문서로 만들어줘."
```

### Skywork 설정 생성
```
"내 SecretID는 foo, Key는 bar야. Skywork 설정 좀 만들어줘."
```

---

## 기술 스택

- **언어**: Python 3.10+
- **프레임워크**: Model Context Protocol (MCP) SDK
- **이미지 생성**: Google Imagen 4.0-fast (`google-genai`)
- **문서 생성**: Skywork AI API (통합 Proxy)
- **의존성**: `mcp`, `requests`, `python-dotenv`, `httpx`, `google-genai`

---

## 라이선스

MIT License

---

## 기여

버그 리포트 및 기능 제안은 [Issues](https://github.com/hyoseop1231/Smart_Visual_Toolkit_MCP/issues)에 등록해주세요.
