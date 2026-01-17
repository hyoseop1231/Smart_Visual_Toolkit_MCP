import os
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

from generators.cache import generate_cache_key, ImageCache

load_dotenv()


class ImageGenerator:
    def __init__(self, styles_data: Dict[str, Any]):
        self.styles = {s["name"]: s for s in styles_data.get("styles", [])}
        self.default_style = styles_data.get("default_style", "Flat Corporate")

        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logging.error(f"Failed to initialize Google GenAI Client: {e}")
        else:
            logging.warning("GOOGLE_API_KEY is not set. Image generation will fail.")

        # Ensure output directory exists
        self.output_dir = Path("output/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 캐시 설정 (환경 변수 기반)
        self._cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self._cache: Optional[ImageCache] = None

        if self._cache_enabled:
            max_size = int(os.getenv("CACHE_MAX_SIZE", "100"))
            ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
            self._cache = ImageCache(max_size=max_size, ttl_seconds=ttl_seconds)
            logging.info(f"캐시 활성화: max_size={max_size}, ttl={ttl_seconds}초")

    def generate(
        self, prompt: str, style_name: Optional[str] = None, aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """
        Generates an image based on prompt and style using Google Imagen 3 via SDK.

        캐시가 활성화된 경우:
        - 동일한 prompt + style + aspect_ratio 조합에 대해 캐시된 결과 반환
        - 캐시 미스 시 API 호출 후 결과 캐싱
        """
        # 캐시 활성화 시 캐시 조회
        effective_style = style_name or self.default_style
        if self._cache_enabled and self._cache:
            cache_key = generate_cache_key(prompt, effective_style, aspect_ratio)
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logging.info(f"캐시 HIT: {cache_key[:16]}...")
                # 캐시된 결과에 캐시 히트 표시 추가
                cached_result = cached_result.copy()
                cached_result["cached"] = True
                return cached_result

        # 캐시 미스 또는 캐시 비활성화 - API 호출
        result = self._generate_uncached(prompt, style_name, aspect_ratio)

        # 성공한 결과만 캐싱
        if self._cache_enabled and self._cache and result.get("success"):
            cache_key = generate_cache_key(prompt, effective_style, aspect_ratio)
            self._cache.set(cache_key, result)
            logging.info(f"캐시 저장: {cache_key[:16]}...")

        return result

    def _generate_uncached(
        self, prompt: str, style_name: Optional[str] = None, aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """
        캐시 없이 직접 API를 호출하여 이미지 생성
        """
        if not self.client:
            return {
                "success": False,
                "error": "Google GenAI Client is not initialized (Check GOOGLE_API_KEY).",
            }

        # 1. Select Style
        style = self.styles.get(style_name, self.styles.get(self.default_style))
        style_keywords = style["keywords"] if style else ""

        # 2. Combine Prompt
        final_prompt = f"{prompt}. Style details: {style_keywords}"
        if aspect_ratio:
            final_prompt += f", Aspect Ratio: {aspect_ratio}"

        logging.info(f"Generating image with prompt: {final_prompt}")

        try:
            # 3. Call Imagen 3 (Updated to 4.0-fast based on availability)
            # Ref: https://github.com/googleapis/python-genai
            # Ensure using the correct model ID for Imagen
            response = self.client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio
                    if aspect_ratio in ["1:1", "16:9", "9:16", "4:3", "3:4"]
                    else "16:9",
                ),
            )

            if response and response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes

                # Generate filename
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_style = (style_name or "default").replace(" ", "_").lower()
                filename = f"gen_{safe_style}_{timestamp}.png"
                output_path = self.output_dir / filename

                # Save
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logging.info(f"Image saved to {output_path}")

                return {
                    "success": True,
                    "prompt": final_prompt,
                    "local_path": str(output_path.absolute()),
                    "url": str(output_path.absolute()),
                    "status": "Image generated with Imagen 3 and saved successfully.",
                }
            else:
                return {"success": False, "error": "No images returned."}

        except Exception as e:
            logging.error(f"Image generation failed: {e}")
            return {"success": False, "error": str(e)}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회

        Returns:
            캐시 통계 딕셔너리 또는 캐시 비활성화 시 상태 메시지
        """
        if not self._cache_enabled or not self._cache:
            return {"enabled": False, "message": "캐시가 비활성화되어 있습니다."}

        stats = self._cache.get_stats()
        stats["enabled"] = True
        return stats

    def clear_cache(self) -> Dict[str, Any]:
        """
        캐시 초기화

        Returns:
            초기화 결과 딕셔너리
        """
        if not self._cache_enabled or not self._cache:
            return {"success": False, "message": "캐시가 비활성화되어 있습니다."}

        count = self._cache.clear()
        return {"success": True, "cleared_count": count}


def get_image_generator():
    styles_path = Path(__file__).parent.parent / "resources" / "banana_styles.json"
    with open(styles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ImageGenerator(data)
