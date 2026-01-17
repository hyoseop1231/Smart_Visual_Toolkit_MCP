import os
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

    def generate(self, prompt: str, style_name: Optional[str] = None, aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """
        Generates an image based on prompt and style using Google Imagen 3 via SDK.
        """
        if not self.client:
             return {"success": False, "error": "Google GenAI Client is not initialized (Check GOOGLE_API_KEY)."}

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
                model='imagen-4.0-fast-generate-001',
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio if aspect_ratio in ["1:1", "16:9", "9:16", "4:3", "3:4"] else "16:9",
                )
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
                    "status": "Image generated with Imagen 3 and saved successfully."
                }
            else:
                 return {"success": False, "error": "No images returned."}

        except Exception as e:
            logging.error(f"Image generation failed: {e}")
            return {"success": False, "error": str(e)}

def get_image_generator():
    styles_path = Path(__file__).parent.parent / "resources" / "banana_styles.json"
    with open(styles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ImageGenerator(data)
