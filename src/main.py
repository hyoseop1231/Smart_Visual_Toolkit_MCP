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
    from generators.image_gen import get_image_generator  # type: ignore[no-redef]

try:
    from src.gallery.image_gallery import ImageGallery
except ImportError:
    from gallery.image_gallery import ImageGallery  # type: ignore[no-redef]

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Smart Visual Toolkit")

# Initialize Generators
image_gen = get_image_generator()

# Initialize Gallery (SPEC-GALLERY-001)
output_dir = Path("output/images")
metadata_path = Path("output/metadata.json")
gallery = ImageGallery(
    images_dir=output_dir,
    metadata_path=metadata_path,
    enable_thumbnails=os.getenv("ENABLE_THUMBNAILS", "false").lower() == "true",
)

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
def generate_image_advanced(
    prompt: str,
    style_name: Optional[str] = None,
    aspect_ratio: str = "16:9",
    format: str = "png",
    quality: int = 95,
    width: Optional[int] = None,
    height: Optional[int] = None,
    negative_prompt: Optional[str] = None,
    style_intensity: str = "normal",
    enhance_prompt: bool = True,
) -> str:
    """
    Advanced image generation with fine-grained control (SPEC-IMG-004).

    Features:
    - Resolution Control: Custom width/height (256-2048 range)
    - Negative Prompts: Exclude unwanted elements
    - Style Intensity: weak/normal/strong keyword count
    - Prompt Enhancement: Auto style keyword addition

    Args:
        prompt: Visual description of the image
        style_name: Optional style name from list_styles()
        aspect_ratio: Image aspect ratio (default: "16:9")
        format: Output format - png, jpeg, webp (default: "png")
        quality: Image quality 1-100 for JPEG/WebP (default: 95)
        width: Custom width in pixels 256-2048 (optional)
        height: Custom height in pixels 256-2048 (optional)
        negative_prompt: Elements to exclude from generation (optional)
        style_intensity: Style strength - weak/normal/strong (default: "normal")
        enhance_prompt: Enable automatic style keyword addition (default: True)

    Style Intensity Guide:
    - weak: 1-2 style keywords added
    - normal: 2-4 style keywords added
    - strong: 4-6 style keywords added

    Examples:
    - High resolution portrait: width=1024, height=1536, aspect_ratio="2:3"
    - Exclude elements: negative_prompt="blurry, low quality, distorted"
    - Subtle styling: style_intensity="weak", enhance_prompt=True
    """
    # 파라미터 검증
    valid_formats = ["png", "jpeg", "webp", "jpg"]
    if format not in valid_formats:
        return f"Error: Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}"

    if not 1 <= quality <= 100:
        return f"Error: Quality must be between 1 and 100, got {quality}"

    valid_intensities = ["weak", "normal", "strong"]
    if style_intensity not in valid_intensities:
        return f"Error: Invalid style_intensity '{style_intensity}'. Must be one of: {', '.join(valid_intensities)}"

    # 해상도 검증
    if width and height:
        from models.prompt_enhancer import validate_resolution

        adj_width, adj_height, was_adjusted = validate_resolution(width, height)
        if was_adjusted:
            return f"Warning: Resolution adjusted from {width}x{height} to {adj_width}x{adj_height} (must be 256-2048). Please retry with valid dimensions."
    elif width or height:
        # 둘 중 하나만 제공된 경우
        return "Error: Both width and height must be provided together for custom resolution."

    result = image_gen.generate_advanced(
        prompt=prompt,
        style_name=style_name,
        aspect_ratio=aspect_ratio,
        format=format,
        quality=quality,
        width=width,
        height=height,
        negative_prompt=negative_prompt,
        style_intensity=style_intensity,
        enhance_prompt=enhance_prompt,
    )

    if result["success"]:
        response_parts = [
            "Advanced image generation successful.",
            f"Prompt: {result['prompt']}",
        ]

        # 선택적 정보 추가
        if "width" in result and "height" in result:
            response_parts.append(f"Resolution: {result['width']}x{result['height']}")

        if result.get("negative_prompt"):
            response_parts.append(
                f"Negative Prompt: {result['negative_prompt'][:50]}..."
            )

        if result.get("cached"):
            response_parts.append("(Cached result)")

        response_parts.append(f"Status: {result['status']}")
        response_parts.append(f"Local Path: {result.get('local_path')}")

        return "\n".join(response_parts)
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


# --- Gallery Tools (SPEC-GALLERY-001) ---


@mcp.tool()
def list_images(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> str:
    """
    [SPEC-GALLERY-001] Lists generated images with pagination and sorting.

    Args:
        limit: Maximum number of images to return (default: 50)
        offset: Number of images to skip for pagination (default: 0)
        sort_by: Sort field - created_at, size, style, filename (default: created_at)
        sort_order: Sort order - asc or desc (default: desc)

    Returns:
        Formatted list of images with metadata
    """
    images = gallery.list_images(
        limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
    )

    if not images:
        return "No images found. Generate some images first!"

    result = [f"Found {len(images)} image(s):", ""]

    for img in images:
        result.append(f"ID: {img.id}")
        result.append(f"  File: {img.filename}")
        result.append(f"  Style: {img.style}")
        result.append(f"  Created: {img.created_at}")
        result.append(f"  Resolution: {img.resolution}")
        result.append(f"  Format: {img.format}")
        result.append(f"  Size: {img.get_file_size_mb():.2f} MB")
        result.append(f"  Prompt: {img.prompt[:80]}...")
        result.append("")

    return "\n".join(result)


@mcp.tool()
def search_images(
    style: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    format: Optional[str] = None,
) -> str:
    """
    [SPEC-GALLERY-001] Searches images by various criteria.

    Args:
        style: Filter by style name (optional)
        date_from: Start date in ISO format (optional)
        date_to: End date in ISO format (optional)
        keyword: Search in prompt text (optional)
        format: Image format - png, jpeg, webp (optional)

    Returns:
        Formatted list of matching images
    """
    filters = {}
    if style:
        filters["style"] = style
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if keyword:
        filters["keyword"] = keyword
    if format:
        filters["format"] = format

    images = gallery.search_images(filters)

    if not images:
        return "No matching images found."

    result = [f"Found {len(images)} matching image(s):", ""]

    for img in images:
        result.append(f"ID: {img.id}")
        result.append(f"  Style: {img.style}, Format: {img.format}")
        result.append(f"  Created: {img.created_at}")
        result.append(f"  Prompt: {img.prompt[:80]}...")
        result.append("")

    return "\n".join(result)


@mcp.tool()
def get_image_details(image_id: str) -> str:
    """
    [SPEC-GALLERY-001] Gets detailed metadata for a specific image.

    Args:
        image_id: Unique image identifier

    Returns:
        Detailed image metadata or error message
    """
    metadata = gallery.get_image_details(image_id)

    if not metadata:
        return f"Error: Image '{image_id}' not found."

    result = [
        f"Image Details: {metadata.id}",
        f"  Filename: {metadata.filename}",
        f"  Path: {metadata.filepath}",
        f"  Created: {metadata.created_at}",
        f"  Style: {metadata.style}",
        f"  Aspect Ratio: {metadata.aspect_ratio}",
        f"  Resolution: {metadata.resolution}",
        f"  Format: {metadata.format}",
        f"  Size: {metadata.get_file_size_mb():.2f} MB ({metadata.size_bytes} bytes)",
        f"  Prompt: {metadata.prompt}",
    ]

    if metadata.thumbnail_path:
        result.append(f"  Thumbnail: {metadata.thumbnail_path}")

    if metadata.generation_params:
        result.append(f"  Generation Params: {metadata.generation_params}")

    return "\n".join(result)


@mcp.tool()
def delete_image(image_id: str, confirm: bool = False) -> str:
    """
    [SPEC-GALLERY-001] Deletes an image (requires confirm=True).

    Args:
        image_id: Unique image identifier
        confirm: Must be True to actually delete (safety measure)

    Returns:
        Deletion result message
    """
    result = gallery.delete_image(image_id, confirm=confirm)

    if result["success"]:
        return f"✓ {result['message']}"
    else:
        return f"✗ {result['message']}"


@mcp.tool()
def cleanup_old_images(days: int = 30, dry_run: bool = True) -> str:
    """
    [SPEC-GALLERY-001] Cleans up images older than specified days.

    Args:
        days: Age threshold in days (default: 30)
        dry_run: If True, only show what would be deleted (default: True)

    Returns:
        Cleanup result summary
    """
    result = gallery.cleanup_old_images(days=days, dry_run=dry_run)

    if dry_run:
        if result["would_delete_count"] > 0:
            freed_mb = result["freed_space_bytes"] / (1024 * 1024)
            output = [
                f"Dry run: Would delete {result['would_delete_count']} old image(s)",
                f"  Would free: {freed_mb:.2f} MB",
                f"  Age threshold: {days} days",
                "",
                "Images to be deleted:",
            ]
            for img_id in result["would_delete_images"]:
                output.append(f"  - {img_id}")
            return "\n".join(output)
        else:
            return f"No images older than {days} days found."
    else:
        if result["deleted_count"] > 0:
            freed_mb = result["freed_space_bytes"] / (1024 * 1024)
            return (
                f"✓ Cleaned up {result['deleted_count']} old image(s)\n"
                f"  Freed: {freed_mb:.2f} MB"
            )
        else:
            return f"No images older than {days} days found."


if __name__ == "__main__":
    mcp.run()
