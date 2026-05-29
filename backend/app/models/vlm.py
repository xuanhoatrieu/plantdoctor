import base64
import io
import json
import logging
import urllib.request
from typing import Optional

from PIL import Image
from .pesticide_matcher import match_medicines

logger = logging.getLogger(__name__)

API_URL = "http://152.67.112.145:8317/v1/chat/completions"
API_KEY = "ai-teaching-assistant-prod"
MODEL = "gpt-5.5"

SYSTEM_PROMPT = """You are an expert plant pathologist. Analyze the leaf/plant image and identify any disease.

Respond ONLY with valid JSON in this exact format:
{
  "plant": "plant name in English",
  "disease": "disease name or 'Healthy'",
  "confidence": 85,
  "severity": "mild/moderate/severe/none",
  "description": "brief description of symptoms observed",
  "treatment": "recommended treatment",
  "medicines": ["medicine1", "medicine2"]
}

Rules:
- If the image is not a plant/leaf, set disease to "Not a plant image" and confidence to 0
- If healthy, set severity to "none" and medicines to []
- Confidence is 0-100 integer
- Be specific about the disease name
- Include both common and scientific name if possible"""

SYSTEM_PROMPT_VI = """Bạn là chuyên gia bệnh lý thực vật. Phân tích ảnh lá/cây và xác định bệnh.

Trả lời CHỈ bằng JSON hợp lệ theo format:
{
  "plant": "tên cây trồng",
  "disease": "tên bệnh hoặc 'Khỏe mạnh'",
  "confidence": 85,
  "severity": "nhẹ/trung bình/nặng/không",
  "description": "mô tả triệu chứng quan sát được",
  "treatment": "khuyến nghị điều trị",
  "medicines": ["thuốc1", "thuốc2"]
}

Quy tắc:
- Nếu ảnh không phải cây/lá, set disease = "Không phải ảnh cây trồng", confidence = 0
- Nếu khỏe mạnh, severity = "không", medicines = []
- Confidence là số nguyên 0-100
- Nêu cụ thể tên bệnh (cả tên thường và tên khoa học nếu có)"""


def predict_vlm(image: Image.Image, lang: str = "vi") -> Optional[dict]:
    """Use GPT-5.5 vision to identify plant disease."""
    # Convert image to base64
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    prompt = SYSTEM_PROMPT_VI if lang == "vi" else SYSTEM_PROMPT

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": "Phân tích bệnh cây trong ảnh này." if lang == "vi" else "Identify the plant disease in this image."},
            ]},
        ],
        "max_tokens": 500,
        "temperature": 0,
    }

    try:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]

        # Parse JSON from response (handle markdown code blocks)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        result = json.loads(content)

        # Format to match existing prediction response
        is_healthy = result.get("disease", "").lower() in ("healthy", "khỏe mạnh")
        medicines = result.get("medicines", []) if not is_healthy else []
        
        # Match medicines against pesticide database
        medicine_match = match_medicines(medicines) if medicines else {"matched_products": [], "banned_warning": []}

        predictions = [{
            "label": result.get("disease", "Unknown"),
            "confidence": result.get("confidence", 0),
            "name": f"{result.get('plant', '')} - {result.get('disease', '')}",
            "description": result.get("description", ""),
            "treatment": result.get("treatment", "") if not is_healthy else "",
            "medicines": medicines,
            "severity": result.get("severity", ""),
            "matched_products": medicine_match["matched_products"],
            "banned_warning": medicine_match["banned_warning"],
        }]

        return {
            "model_id": "plantdoctor_ai",
            "model_name": "PlantDoctor AI",
            "predictions": predictions,
        }

    except Exception as e:
        logger.error("VLM prediction failed: %s", e)
        return None
