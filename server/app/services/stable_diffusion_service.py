import aiohttp
import base64
import json
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StableDiffusionService:
    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=1200)  # 20 минут для генерации

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "Euler a",
        seed: int = -1,
        **kwargs
    ) -> Optional[bytes]:
        url = f"{self.base_url}/sdapi/v1/txt2img"
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
            "seed": seed,
            "restore_faces": True,
            "enable_hr": False,
        }
        
        print(f"🎨 Sending request to Stable Diffusion at {url}")
        print(f"📝 Prompt: {prompt}")
        print(f"🔧 Parameters: {payload}")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    print(f"📡 Response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Stable Diffusion returned valid response")
                        
                        if 'images' in result and result['images']:
                            image_data = result['images'][0]
                            
                            if ',' in image_data:
                                image_data = image_data.split(',', 1)[1]
                            
                            image_bytes = base64.b64decode(image_data)
                            print(f"✅ Image generated successfully, size: {len(image_bytes)} bytes")
                            return image_bytes
                        else:
                            print("❌ No images in response")
                            return None
                    else:
                        error_text = await response.text()
                        print(f"❌ SD API error: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            print("❌ Stable Diffusion request timed out")
            return None
        except aiohttp.ClientConnectorError:
            print("❌ Cannot connect to Stable Diffusion API - is it running?")
            return None
        except Exception as e:
            print(f"❌ Error calling Stable Diffusion API: {str(e)}")
            return None

    async def generate_with_controlnet(
        self,
        prompt: str,
        init_image: bytes,
        controlnet_model: str = "control_v11p_sd15_openpose [cab727d4]",
        **kwargs
    ) -> Optional[bytes]:
        """
        Генерация с использованием ControlNet для сохранения позы
        """
        url = f"{self.base_url}/sdapi/v1/txt2img"
        
        # Кодируем исходное изображение в base64
        init_image_b64 = base64.b64encode(init_image).decode('utf-8')
        
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512,
            "steps": 20,
            "alwayson_scripts": {
                "controlnet": {
                    "args": [
                        {
                            "input_image": init_image_b64,
                            "model": controlnet_model,
                            "weight": 1.0,
                            "control_mode": "Balanced"
                        }
                    ]
                }
            }
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        image_data = result['images'][0]
                        image_bytes = base64.b64decode(image_data)
                        return image_bytes
                    else:
                        error_text = await response.text()
                        logger.error(f"ControlNet API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling ControlNet API: {str(e)}")
            return None

    async def img2img(
        self,
        prompt: str,
        init_image: bytes,
        denoising_strength: float = 0.7,
        **kwargs
    ) -> Optional[bytes]:
        """
        Генерация на основе существующего изображения
        """
        url = f"{self.base_url}/sdapi/v1/img2img"
        
        init_image_b64 = base64.b64encode(init_image).decode('utf-8')
        
        payload = {
            "init_images": [init_image_b64],
            "prompt": prompt,
            "denoising_strength": denoising_strength,
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        image_data = result['images'][0]
                        image_bytes = base64.b64decode(image_data)
                        return image_bytes
                    else:
                        error_text = await response.text()
                        logger.error(f"img2img API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling img2img API: {str(e)}")
            return None

# Глобальный экземпляр сервиса
stable_diffusion_service = StableDiffusionService()