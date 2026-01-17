# Smart Visual Toolkit (MCP Server)

Obsidian Smart Composer와 연동하여 **나노바나나(Nano Banana) 스타일의 AI 이미지 생성**을 제공하고, **Skywork MCP Server**와의 연동을 도와주는 툴킷입니다.

## 🌟 주요 기능

1.  **AI 이미지 생성 (`generate_image`)**
    *   **나노바나나 스타일 적용**: 15종 이상의 바나나 X 스타일 패턴(Corporate Memphis, Clay 3D, Pixel Art 등)을 자동으로 프롬프트에 적용합니다.
    *   **Obsidian 연동**: 노트 내용을 기반으로 LLM이 적절한 스타일을 추천하여 이미지를 생성합니다.
    *   **API**: **Google Gemini (Imagen)** 모델을 사용하여 고품질 이미지를 생성합니다.

2.  **스타일 탐색 (`list_styles`)**
    *   사용 가능한 모든 시각적 스타일과 키워드를 조회합니다.

3.  **Skywork 설정 도우미 (`get_skywork_config`)**
    *   PPT, Word, Excel 생성을 위한 **Skywork MCP Server**의 인증 URL을 자동으로 생성해줍니다.
    *   복잡한 MD5 서명 계산 과정을 대신 처리하여, Obsidian 설정에 바로 붙여넣을 수 있는 JSON 설정을 제공합니다.

## 📂 프로젝트 구조

```text
smart-visual-toolkit/
├── src/
│   ├── generators/
│   │   └── image_gen.py    # 이미지 생성 로직 (스타일 합성 및 API 호출)
│   ├── resources/
│   │   └── banana_styles.json  # 나노바나나 스타일 템플릿 DB
│   └── main.py             # MCP 서버 엔트리포인트 (Tools 정의)
├── pyproject.toml          # 프로젝트 설정 및 의존성
└── README.md               # 문서
```

## 🚀 설치 및 실행 방법

### 1. 환경 설정

Python 3.10 이상이 필요합니다.

```bash
# 가상환경 생성 및 활성화 (선택)
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 의존성 설치
pip install -e .
```

### 2. API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요. (이미지 생성을 위해 필요)

```ini
# Google Gemini API Key (Imagen 사용)
GOOGLE_API_KEY=your_google_api_key_here

# Option: Pre-configure Skywork Credentials (for easy config generation)
SKYWORK_SECRET_ID=your_skywork_secret_id
SKYWORK_SECRET_KEY=your_skywork_secret_key
```

### 3. 서버 실행

```bash
uv run src/main.py
```

## 🔗 External Tools Integration

### Skywork MCP (Office Tools)
Provides professional document generation capabilities.

**Available Tools:**
*   `gen_doc`: Create and edit Word documents.
*   `gen_excel`: Data analysis and Excel sheet creation.
*   `gen_ppt`: Standard PowerPoint generation.
*   `gen_ppt_fast`: Fast PowerPoint generation.

#### Configuration

**Step 1: Get Credentials**
1.  Sign up at [Skywork AI Open Platform](https://skywork.ai/).
2.  Get your `SecretID` and `SecretKey`.

**Step 2: Generate Config**
Use this MCP server to generate your signed URL:
> "내 SecretID는 `foo`, Key는 `bar`야. Skywork 설정 좀 만들어줘."

**Step 3-A: Obsidian Smart Composer**
Add the generated JSON to your `mcpServers` config:
```json
{
  "mcpServers": {
    "skywork-office-tool": {
      "url": "https://api.skywork.ai/open/sse?secret_id=...&sign=..."
    }
  }
}
```

**Step 3-B: Cursor IDE**
1.  Go to **Settings** > **Models** > **MCP**.
2.  Click **Add New MCP Server**.
3.  Name: `Skywork-Office-Tool`
4.  Type: `SSE`
5.  URL: (Paste the signed URL generated in Step 2)

## 🎨 사용 예시 (Obsidian 채팅)

*   **이미지 생성**: "이 노트의 내용을 요약해서 'Clay 3D' 스타일로 귀여운 이미지를 하나 만들어줘."
*   **PPT 생성**: "이 노트를 바탕으로 발표 자료를 만들어줘. (Skywork가 자동으로 처리)"
*   **스타일 조회**: "사용 가능한 이미지 스타일 목록 보여줘."

## 🛠️ 개발 정보

*   **언어**: Python 3.10+
*   **프레임워크**: Model Context Protocol (MCP) SDK
*   **라이브러리**: `requests`, `python-dotenv`
