import os
import logging
import json
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


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

    def generate(
        self, prompt: str, style_name: Optional[str] = None, aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """
        Generates an image based on prompt and style using Google Imagen 3 via SDK.
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

    async def _generate_single_async(
        self,
        prompt: str,
        style_name: Optional[str] = None,
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """
        REQ-IMG-002: 비동기 단일 이미지 생성
        기존 동기 generate() 메서드를 async로 래핑
        """
        # 동기 메서드를 별도 스레드에서 실행
        result = await asyncio.to_thread(
            self.generate, prompt, style_name, aspect_ratio
        )
        # 결과에 원본 프롬프트 추가
        result["prompt"] = prompt
        return result

    async def generate_batch(
        self,
        prompts: List[str],
        style_name: Optional[str] = None,
        max_concurrent: int = 3,
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """
        REQ-IMG-001: 배치 이미지 생성
        REQ-IMG-003: Semaphore로 동시성 제어
        REQ-IMG-004: 진행 상황 로깅
        REQ-IMG-005: 부분 실패 처리
        REQ-IMG-006: 결과 형식 정의
        """
        # TC-005: 빈 프롬프트 목록 처리
        if not prompts:
            return {
                "total": 0,
                "success_count": 0,
                "failure_count": 0,
                "results": [],
            }

        # 동시성 제어를 위한 Semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0
        total = len(prompts)

        async def generate_with_semaphore(prompt: str) -> Dict[str, Any]:
            nonlocal completed
            async with semaphore:
                result = await self._generate_single_async(
                    prompt, style_name, aspect_ratio
                )
                completed += 1
                # REQ-IMG-004: 진행 상황 로깅
                logger.info(f"Progress: {completed}/{total} - Prompt: {prompt[:50]}...")
                return result

        # 모든 작업을 병렬로 실행 (Semaphore로 동시성 제한)
        results = await asyncio.gather(
            *[generate_with_semaphore(p) for p in prompts],
            return_exceptions=True,
        )

        # 결과 집계
        processed_results = []
        success_count = 0
        failure_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 예외 발생 시 실패 처리
                processed_results.append(
                    {
                        "prompt": prompts[i],
                        "success": False,
                        "error": str(result),
                    }
                )
                failure_count += 1
            elif result.get("success"):
                processed_results.append(result)
                success_count += 1
            else:
                processed_results.append(result)
                failure_count += 1

        return {
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "results": processed_results,
        }


def get_image_generator():
    styles_path = Path(__file__).parent.parent / "resources" / "banana_styles.json"
    with open(styles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ImageGenerator(data)
