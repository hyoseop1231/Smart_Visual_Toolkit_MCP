import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.cache import generate_cache_key, ImageCache
from generators.format_handlers import save_image
from models.prompt_enhancer import PromptEnhancer, validate_resolution

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

        # 프롬프트 강화기 초기화
        self.prompt_enhancer = PromptEnhancer()

    def generate(
        self,
        prompt: str,
        style_name: Optional[str] = None,
        aspect_ratio: str = "16:9",
        format: str = "png",
        quality: int = 95,
    ) -> Dict[str, Any]:
        """
        Generates an image based on prompt and style using Google Imagen 3 via SDK.

        Args:
            prompt: 이미지 생성 프롬프트
            style_name: 스타일 이름 (None인 경우 기본 스타일 사용)
            aspect_ratio: 이미지 비율 (기본값: "16:9")
            format: 출력 형식 (png, jpeg, webp) - 기본값: "png"
            quality: 이미지 품질 1-100 (JPEG/WebP용) - 기본값: 95

        Returns:
            생성 결과 딕셔너리

        캐시가 활성화된 경우:
        - 동일한 prompt + style + aspect_ratio + format + quality 조합에 대해 캐시된 결과 반환
        - 캐시 미스 시 API 호출 후 결과 캐싱
        """
        # 캐시 활성화 시 캐시 조회
        effective_style = style_name or self.default_style
        if self._cache_enabled and self._cache:
            cache_key = generate_cache_key(
                prompt, effective_style, aspect_ratio, format, quality
            )
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logging.info(f"캐시 HIT: {cache_key[:16]}...")
                # 캐시된 결과에 캐시 히트 표시 추가
                cached_result = cached_result.copy()
                cached_result["cached"] = True
                return cached_result

        # 캐시 미스 또는 캐시 비활성화 - API 호출
        result = self._generate_uncached(
            prompt, style_name, aspect_ratio, format, quality
        )

        # 성공한 결과만 캐싱
        if self._cache_enabled and self._cache and result.get("success"):
            cache_key = generate_cache_key(
                prompt, effective_style, aspect_ratio, format, quality
            )
            self._cache.set(cache_key, result)
            logging.info(f"캐시 저장: {cache_key[:16]}...")

        return result

    def _generate_uncached(
        self,
        prompt: str,
        style_name: Optional[str] = None,
        aspect_ratio: str = "16:9",
        format: str = "png",
        quality: int = 95,
    ) -> Dict[str, Any]:
        """
        캐시 없이 직접 API를 호출하여 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            style_name: 스타일 이름
            aspect_ratio: 이미지 비율
            format: 출력 형식 (png, jpeg, webp)
            quality: 이미지 품질 1-100

        Returns:
            생성 결과 딕셔너리
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
            # 3. Call Imagen 4
            response = self.client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio
                    if aspect_ratio
                    in [
                        "1:1",
                        "16:9",
                        "9:16",
                        "4:3",
                        "3:4",
                        # SPEC-IMG-003: 새로운 비율 지원
                        "21:9",  # Ultra-Wide
                        "2:3",  # Portrait SNS
                        "3:2",  # Photo DSLR
                        "5:4",  # Large Format
                    ]
                    else "16:9",
                ),
            )

            if response and response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes

                # BytesIO에서 PIL 이미지로 변환
                from io import BytesIO

                image = Image.open(BytesIO(image_bytes))

                # Generate filename
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_style = (style_name or "default").replace(" ", "_").lower()
                extension = format if format != "jpg" else "jpeg"
                filename = f"gen_{safe_style}_{timestamp}.{extension}"
                output_path = self.output_dir / filename

                # save_image() 사용하여 지정된 형식으로 저장
                save_image(
                    image, format=format, quality=quality, output_path=str(output_path)
                )
                logging.info(
                    f"Image saved to {output_path} (format: {format}, quality: {quality})"
                )

                return {
                    "success": True,
                    "prompt": final_prompt,
                    "local_path": str(output_path.absolute()),
                    "url": str(output_path.absolute()),
                    "format": format,
                    "quality": quality,
                    "status": f"Image generated with Imagen 4 and saved as {format.upper()}.",
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

    def generate_advanced(
        self,
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
    ) -> Dict[str, Any]:
        """
        고급 이미지 생성 - SPEC-IMG-004

        기본 generate() 메서드를 확장하여 다음 기능을 추가합니다:
        - 해상도 제어 (width, height): 256-2048 범위
        - 네거티브 프롬프트: 제외할 요소 지정
        - 스타일 강도: weak/normal/strong 키워드 수 조절
        - 프롬프트 강화: 자동 스타일 키워드 추가

        Args:
            prompt: 이미지 생성 프롬프트
            style_name: 스타일 이름 (None인 경우 기본 스타일 사용)
            aspect_ratio: 이미지 비율 (기본값: "16:9")
            format: 출력 형식 (png, jpeg, webp) - 기본값: "png"
            quality: 이미지 품질 1-100 (JPEG/WebP용) - 기본값: 95
            width: 사용자 정의 너비 (256-2048, 선택)
            height: 사용자 정의 높이 (256-2048, 선택)
            negative_prompt: 네거티브 프롬프트 (선택)
            style_intensity: 스타일 강도 ("weak", "normal", "strong") - 기본값: "normal"
            enhance_prompt: 프롬프트 강화 활성화 - 기본값: True

        Returns:
            생성 결과 딕셔너리
        """
        effective_style = style_name or self.default_style

        # 1. 프롬프트 강화 (활성화된 경우)
        final_prompt = prompt
        if enhance_prompt:
            style_obj = self.styles.get(effective_style)
            if style_obj:
                style_keywords = style_obj.get("keywords", "")
                final_prompt = self.prompt_enhancer.enhance(
                    prompt=prompt,
                    style=style_keywords,
                    intensity=style_intensity,
                )
                logging.info(f"프롬프트 강화 적용: {style_intensity} 강도")

        # 2. 프롬프트 길이 검증
        final_prompt, is_valid_length = self.prompt_enhancer.validate_length(
            final_prompt, max_length=1000
        )
        if not is_valid_length:
            logging.warning("프롬프트가 1000자를 초과하여 트리밍됨")

        # 3. 해상도 검증 및 조정
        adjusted_width = width
        adjusted_height = height
        resolution_adjusted = False

        if width and height:
            adjusted_width, adjusted_height, resolution_adjusted = validate_resolution(
                width, height
            )
            if resolution_adjusted:
                logging.warning(
                    f"해상도가 {width}x{height}에서 {adjusted_width}x{adjusted_height}로 조정됨"
                )

        # 4. 네거티브 프롬프트 구성
        final_negative_prompt = self.prompt_enhancer.build_negative_prompt(
            custom_negative=negative_prompt,
            style=effective_style,
        )

        # 5. 캐시 확인
        if self._cache_enabled and self._cache:
            from generators.cache import generate_cache_key_advanced

            cache_key = generate_cache_key_advanced(
                prompt=final_prompt,
                style=effective_style,
                aspect_ratio=aspect_ratio,
                format=format,
                quality=quality,
                width=adjusted_width,
                height=adjusted_height,
                negative_prompt=final_negative_prompt,
                style_intensity=style_intensity,
                enhance_prompt=enhance_prompt,
            )
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logging.info(f"캐시 HIT (advanced): {cache_key[:16]}...")
                cached_result = cached_result.copy()
                cached_result["cached"] = True
                return cached_result

        # 6. API 호출 (캐시 미스 또는 비활성화)
        result = self._generate_uncached_advanced(
            prompt=final_prompt,
            style_name=effective_style,
            aspect_ratio=aspect_ratio,
            format=format,
            quality=quality,
            width=adjusted_width,
            height=adjusted_height,
            negative_prompt=final_negative_prompt,
        )

        # 7. 성공한 결과만 캐싱
        if self._cache_enabled and self._cache and result.get("success"):
            from generators.cache import generate_cache_key_advanced

            cache_key = generate_cache_key_advanced(
                prompt=final_prompt,
                style=effective_style,
                aspect_ratio=aspect_ratio,
                format=format,
                quality=quality,
                width=adjusted_width,
                height=adjusted_height,
                negative_prompt=final_negative_prompt,
                style_intensity=style_intensity,
                enhance_prompt=enhance_prompt,
            )
            self._cache.set(cache_key, result)
            logging.info(f"캐시 저장 (advanced): {cache_key[:16]}...")

        return result

    def _generate_uncached_advanced(
        self,
        prompt: str,
        style_name: Optional[str] = None,
        aspect_ratio: str = "16:9",
        format: str = "png",
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        캐시 없이 직접 API를 호출하여 고급 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            style_name: 스타일 이름
            aspect_ratio: 이미지 비율
            format: 출력 형식
            quality: 이미지 품질
            width: 조정된 너비
            height: 조정된 높이
            negative_prompt: 네거티브 프롬프트

        Returns:
            생성 결과 딕셔너리
        """
        if not self.client:
            return {
                "success": False,
                "error": "Google GenAI Client is not initialized (Check GOOGLE_API_KEY).",
            }

        # 스타일 선택
        style = self.styles.get(style_name, self.styles.get(self.default_style))
        style_keywords = style["keywords"] if style else ""

        # 프롬프트 조합
        final_prompt = f"{prompt}. Style details: {style_keywords}"
        if aspect_ratio:
            final_prompt += f", Aspect Ratio: {aspect_ratio}"

        # 네거티브 프롬프트가 있는 경우 로그에 기록
        if negative_prompt:
            logging.info(f"네거티브 프롬프트 적용: {negative_prompt[:50]}...")

        logging.info(f"Generating advanced image with prompt: {final_prompt}")

        try:
            # Imagen 4 호출
            response = self.client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio
                    if aspect_ratio
                    in [
                        "1:1",
                        "16:9",
                        "9:16",
                        "4:3",
                        "3:4",
                        "21:9",
                        "2:3",
                        "3:2",
                        "5:4",
                    ]
                    else "16:9",
                ),
            )

            if response and response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes

                # BytesIO에서 PIL 이미지로 변환
                from io import BytesIO

                image = Image.open(BytesIO(image_bytes))

                # 해상도 조정이 필요한 경우 리사이즈
                if width and height:
                    # 현재 이미지 크기 가져오기
                    original_width, original_height = image.size

                    # 요청된 크기와 다른 경우만 리사이즈
                    if original_width != width or original_height != height:
                        image = image.resize((width, height), Image.Resampling.LANCZOS)  # type: ignore[assignment]
                        logging.info(f"이미지 리사이즈: {width}x{height}")

                # 파일명 생성
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_style = (style_name or "default").replace(" ", "_").lower()
                extension = format if format != "jpg" else "jpeg"
                filename = f"gen_adv_{safe_style}_{timestamp}.{extension}"
                output_path = self.output_dir / filename

                # save_image() 사용하여 지정된 형식으로 저장
                save_image(
                    image, format=format, quality=quality, output_path=str(output_path)
                )
                logging.info(
                    f"Advanced image saved to {output_path} (format: {format}, quality: {quality})"
                )

                result = {
                    "success": True,
                    "prompt": final_prompt,
                    "local_path": str(output_path.absolute()),
                    "url": str(output_path.absolute()),
                    "format": format,
                    "quality": quality,
                    "width": width if width else image.size[0],
                    "height": height if height else image.size[1],
                    "negative_prompt": negative_prompt,
                    "status": f"Advanced image generated with Imagen 4 and saved as {format.upper()}.",
                }

                return result
            else:
                return {"success": False, "error": "No images returned."}

        except Exception as e:
            logging.error(f"Advanced image generation failed: {e}")
            return {"success": False, "error": str(e)}


def get_image_generator():
    styles_path = Path(__file__).parent.parent / "resources" / "banana_styles.json"
    with open(styles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ImageGenerator(data)
