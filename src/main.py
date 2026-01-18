import json
import os
import hashlib
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import logging
import sys

# Skywork client import (refactored module with URL validation, retry logic, exception handling)
from skywork.client import call_skywork_tool as _call_skywork_tool_impl

# Configure logging to stderr to avoid interfering with MCP stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

try:
    from src.generators.image_gen import get_image_generator
except ImportError:
    # If run as script from src/ dir
    from generators.image_gen import get_image_generator

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Smart Visual Toolkit")

# Initialize Generators
image_gen = get_image_generator()

# Load styles for internal use
STYLES_PATH = Path(__file__).parent / "resources" / "banana_styles.json"
try:
    with open(STYLES_PATH, "r", encoding="utf-8") as f:
        STYLE_DATA = json.load(f)
        STYLES = {s["name"]: s for s in STYLE_DATA["styles"]}
        DEFAULT_STYLE = STYLE_DATA.get("default_style", "Flat Corporate")
except Exception as e:
    logging.warning(f"Failed to load styles from {STYLES_PATH}: {e}")
    STYLES = {}
    DEFAULT_STYLE = "default"


@mcp.tool()
def list_styles() -> str:
    """Lists all available visual styles for image generation."""
    if not STYLES:
        return "No styles available."

    result = ["Available Styles:"]
    for name, data in STYLES.items():
        result.append(f"- {name}: {data['description']} (Keywords: {data['keywords']})")

    return "\n".join(result)


@mcp.tool()
def generate_image(prompt: str, style_name: Optional[str] = None) -> str:
    """
    Generates an image using Nano Banana Pro style patterns.
    - prompt: Visual description of the image.
    - style_name: Optional style name from list_styles().
    """
    result = image_gen.generate(prompt, style_name)
    if result["success"]:
        return f"Image generation request successful.\nPrompt used: {result['prompt']}\nStatus: {result['status']}\nLocal Path: {result.get('local_path')}"
    else:
        return f"Error: {result['error']}"


@mcp.tool()
def get_skywork_config(
    secret_id: Optional[str] = None, secret_key: Optional[str] = None
) -> str:
    """
    Generates the signed SSE URL for Skywork MCP Server configuration.

    If secret_id or secret_key are not provided, it attempts to read
    SKYWORK_SECRET_ID and SKYWORK_SECRET_KEY from environment variables.

    Use this URL to add Skywork (PPT/Doc/Excel generation) to your Obsidian config.
    """
    # 1. Fallback to Env Vars if args missing
    if not secret_id:
        secret_id = os.getenv("SKYWORK_SECRET_ID")
    if not secret_key:
        secret_key = os.getenv("SKYWORK_SECRET_KEY")

    # 2. Validation
    if not secret_id or not secret_key:
        return """
Error: Missing Credentials.
Please provide `secret_id` and `secret_key` as arguments, OR set `SKYWORK_SECRET_ID` and `SKYWORK_SECRET_KEY` in your `.env` file.
"""

    # Create Signature: md5(SecretID:SecretKey)
    raw_str = f"{secret_id}:{secret_key}"
    sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

    url = f"https://api.skywork.ai/open/sse?secret_id={secret_id}&sign={sign}"

    config_example = {"mcpServers": {"skywork-office-tool": {"url": url}}}

    return f"""
Here is your signed Skywork URL. 

### 1. Obsidian Smart Composer Configuration
Add this to your MCP client configuration (e.g., `settings.json`):

```json
{json.dumps(config_example, indent=2)}
```

### 2. Cursor IDE Configuration
1. Go to **Settings** > **Models** > **MCP**.
2. Click **Add New MCP Server**.
3. Enter the following:
   - **Name**: Skywork-Office-Tool
   - **Type**: SSE
   - **URL**: {url}

### 🌟 Available Tools
Once configured, you will have access to:
- **gen_doc**: Create/Edit Word documents
- **gen_excel**: Analyze data & create Excel sheets
- **gen_ppt**: Generate PowerPoint presentations
- **gen_ppt_fast**: Quick PPT generation
"""


# Validates environment and args
# --- Skywork Proxy Logic ---
# 리팩토링된 Skywork 클라이언트 모듈 사용 (imported at top)
# 개선 사항: URL 검증, 재시도 로직, 적절한 예외 처리, 리소스 정리


async def _call_skywork_tool(
    tool_name: str,
    query: str,
    use_network: str,
    timeout: float = 300.0,  # noqa: ARG001
) -> str:
    """
    Internal helper to call Skywork API via SSE/HTTP.

    개선된 skywork.client 모듈을 사용합니다:
    - 지수 백오프 재시도 로직
    - URL 검증 (호스트 일치 확인)
    - 적절한 예외 처리 (bare except 제거)
    - 안전한 리소스 정리 (태스크 및 futures)

    Note: timeout 파라미터는 하위 호환성을 위해 유지되지만,
    실제 타임아웃은 SkyworkConfig에서 설정됩니다.
    """
    return await _call_skywork_tool_impl(tool_name, query, use_network)


# --- Public MCP Tools (Proxies) ---


@mcp.tool()
async def gen_doc(query: str, use_network: str = "true") -> str:
    """
    [Skywork Proxy] Generate a Word document.
    - query: Description of the document.
    - use_network: "true" or "false" (string).
    """
    return await _call_skywork_tool("gen_doc", query, use_network)


@mcp.tool()
async def gen_excel(query: str, use_network: str = "true") -> str:
    """
    [Skywork Proxy] Generate an Excel spreadsheet.
    - query: Description of the data/table.
    - use_network: "true" or "false" (string).
    """
    return await _call_skywork_tool("gen_excel", query, use_network)


@mcp.tool()
async def gen_ppt(query: str, use_network: str = "true") -> str:
    """
    [Skywork Proxy] Generate a PowerPoint presentation.
    - query: Description of the slides.
    - use_network: "true" or "false" (string).
    """
    return await _call_skywork_tool("gen_ppt", query, use_network)


@mcp.tool()
async def gen_ppt_fast(query: str, use_network: str = "true") -> str:
    """
    [Skywork Proxy] Fast PowerPoint generation.
    - query: Description of the slides.
    - use_network: "true" or "false" (string).
    """
    return await _call_skywork_tool("gen_ppt_fast", query, use_network)


if __name__ == "__main__":
    mcp.run()
