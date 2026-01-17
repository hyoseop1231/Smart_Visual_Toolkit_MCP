import json
import os
import hashlib
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import logging
import sys

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
async def generate_images_batch(
    prompts: list[str],
    style_name: Optional[str] = None,
    max_concurrent: int = 3,
) -> str:
    """
    Generates multiple images in batch using async processing.
    - prompts: List of visual descriptions for images.
    - style_name: Optional style name from list_styles() (applied to all images).
    - max_concurrent: Maximum number of concurrent image generations (default: 3).

    Returns a summary of batch generation results including success/failure counts.
    """
    if not prompts:
        return "Error: prompts list cannot be empty."

    result = await image_gen.generate_batch(
        prompts=prompts,
        style_name=style_name,
        max_concurrent=max_concurrent,
    )

    # 결과 포맷팅
    output_lines = [
        f"Batch Image Generation Complete",
        f"Total: {result['total']} | Success: {result['success_count']} | Failed: {result['failure_count']}",
        "",
        "Results:",
    ]

    for i, item in enumerate(result["results"], 1):
        if item.get("success"):
            output_lines.append(
                f"  {i}. ✓ {item['prompt'][:50]}... → {item.get('local_path', 'N/A')}"
            )
        else:
            output_lines.append(
                f"  {i}. ✗ {item['prompt'][:50]}... → Error: {item.get('error', 'Unknown')}"
            )

    return "\n".join(output_lines)


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
def _validate_skywork_creds(secret_id, secret_key):
    if not secret_id:
        secret_id = os.getenv("SKYWORK_SECRET_ID")
    if not secret_key:
        secret_key = os.getenv("SKYWORK_SECRET_KEY")
    return secret_id, secret_key


# --- Skywork Proxy Logic (Internal) ---
import httpx
import asyncio
import hashlib


async def _call_skywork_tool(
    tool_name: str, query: str, use_network: str, timeout: float = 300.0
) -> str:
    """Internal helper to call Skywork API via SSE/HTTP"""
    secret_id, secret_key = _validate_skywork_creds(None, None)
    if not secret_id or not secret_key:
        return "Error: SKYWORK_SECRET_ID and SKYWORK_SECRET_KEY must be set in .env"

    # Signature
    raw_str = f"{secret_id}:{secret_key}"
    sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()
    sse_url = f"https://api.skywork.ai/open/sse?secret_id={secret_id}&sign={sign}"

    # SSE Client Logic
    client = httpx.AsyncClient(timeout=timeout)
    endpoint = None
    endpoint_event = asyncio.Event()
    futures = {}

    async def process_sse():
        nonlocal endpoint
        try:
            async with client.stream("GET", sse_url) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if not data:
                            continue
                        if not endpoint and (
                            data.startswith("/") or data.startswith("http")
                        ):
                            if data.startswith("/"):
                                from urllib.parse import urlparse

                                u = urlparse(sse_url)
                                endpoint = f"{u.scheme}://{u.netloc}{data}"
                            else:
                                endpoint = data
                            endpoint_event.set()
                        elif "jsonrpc" in data:
                            try:
                                msg = json.loads(data)
                                if "id" in msg and msg["id"] in futures:
                                    futures[msg["id"]].set_result(msg)
                            except:
                                pass
        except Exception as e:
            logging.error(f"SSE Error: {e}")

    listener = asyncio.create_task(process_sse())

    try:
        # Wait for endpoint
        try:
            await asyncio.wait_for(endpoint_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            return "Error: Could not connect to Skywork SSE endpoint."

        # Helper to send
        async def send(method, params=None, rid=1):
            fut = asyncio.Future()
            futures[rid] = fut
            await client.post(
                endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": rid,
                    "method": method,
                    "params": params or {},
                },
            )
            return await asyncio.wait_for(fut, timeout=timeout)

        # Handshake
        await send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "proxy", "version": "1.0"},
            },
            rid=1,
        )
        await send("notifications/initialized", rid=2)

        # Tool Call
        res = await send(
            "tools/call",
            {
                "name": tool_name,
                "arguments": {"query": query, "use_network": use_network},
            },
            rid=3,
        )

        # Parse Result
        if "result" in res and "content" in res["result"]:
            text_content = ""
            for item in res["result"]["content"]:
                if item.get("type") == "text":
                    text_content += item.get("text", "")
            return (
                text_content
                if text_content
                else "Success, but no text content returned."
            )

        return f"Error: {res}"

    except Exception as e:
        return f"Error during Skywork call: {e}"
    finally:
        listener.cancel()
        await client.aclose()


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
