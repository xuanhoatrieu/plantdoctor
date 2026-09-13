import base64
import io
import json
import logging
import urllib.request
from collections import Counter
from typing import Optional

import imagehash
from cachetools import TTLCache
from PIL import Image, ImageOps
from .pesticide_matcher import match_medicines
from ..database.models import Setting, SessionLocal

logger = logging.getLogger(__name__)

API_URL = "http://152.67.112.145:8317/v1/chat/completions"
API_KEY = "ai-teaching-assistant-prod"
MODEL = "gpt-5.5"

# Confidence threshold: below this triggers self-consistency voting
VOTING_CONFIDENCE_THRESHOLD = 75
VOTING_ROUNDS = 3  # Total calls including the first one

# pHash caching: same image → same result (100% consistency)
# Max 500 entries, expire after 24 hours
_prediction_cache: TTLCache = TTLCache(maxsize=500, ttl=86400)
HASH_SIMILARITY_THRESHOLD = 10  # Hamming distance < 10 = same/very similar image

SYSTEM_PROMPT = """You are an expert plant pathologist. Analyze the leaf/plant image and identify any disease.

STEP 1 — IDENTIFY THE PLANT:
Carefully observe leaf morphology: shape, leaf margins (serrated/smooth), venation pattern, surface texture, petiole characteristics.
Pay special attention to:
- Citrus leaves (orange/lemon/lime/mandarin/pomelo): oval, often have oil glands (translucent dots when backlit), winged petioles, aromatic when crushed
- Tea leaves: elliptical with clearly serrated margins, curved secondary veins, young leaves are thin and soft
- Coffee leaves: large, dark green, waxy, opposite arrangement
- Rice: long narrow blades with parallel venation
If only a single detached leaf is visible, list ALL possible plant candidates

STEP 2 — ASSESS IMAGE QUALITY:
Evaluate the input image and note any issues:
- Is only a single detached leaf visible (no branch/fruit/flower for context)?
- Is the image blurry or out of focus?
- Is there poor lighting or backlighting affecting color accuracy?
- Are fingers/hands obscuring parts of the leaf?
Report any issues that may reduce diagnosis accuracy.

STEP 3 — IDENTIFY SYMPTOMS:
Describe in detail: location, color, shape, size, pattern of any lesions or abnormalities.

STEP 4 — DIAGNOSIS:
Based on steps 1-3, provide your diagnosis.

Common Vietnamese crops to consider:
Citrus (cam, chanh, quýt, bưởi), Rice (lúa), Tea (chè), Coffee (cà phê), Pepper (tiêu, ớt), Mango (xoài), Longan (nhãn), Lychee (vải), Banana (chuối), Durian (sầu riêng), Guava (ổi), Jackfruit (mít), Tomato (cà chua), Potato (khoai tây), Corn (ngô), Soybean (đậu nành), Cassava (sắn), Grape (nho), Apple (táo), Peach (đào), Cherry, Strawberry (dâu tây), Squash (bí)

Respond ONLY with valid JSON in this exact format:
{
  "reasoning": "Step-by-step reasoning: leaf shape observation → symptom description → diagnosis logic",
  "plant_candidates": ["plant1", "plant2"],
  "image_quality_warnings": ["warning1", "warning2"],
  "plant": "most likely plant name in English",
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
- Include both common and scientific name if possible
- image_quality_warnings should be empty [] if the image is clear and has sufficient context
- plant_candidates should list all plausible plants based on leaf morphology"""

SYSTEM_PROMPT_VI = """You are an expert plant pathologist. Analyze the leaf/plant image and identify any plant disease.

STEP 1 — IDENTIFY THE PLANT:
Carefully observe leaf morphology: shape, leaf margins (serrated/smooth), venation pattern, surface texture, petiole characteristics.
Pay special attention to common Vietnamese crops:
- Citrus leaves (cam, chanh, quýt, bưởi): oval, often with oil glands (translucent dots when backlit), winged petioles, aromatic when crushed
- Tea leaves (chè): elliptical with clearly serrated margins, curved secondary veins, young leaves thin and soft
- Coffee leaves (cà phê): large, dark green, waxy surface, opposite arrangement
- Rice leaves (lúa): long narrow blades with parallel venation
- Other common crops: Pepper (tiêu, ớt), Mango (xoài), Longan (nhãn), Lychee (vải), Banana (chuối), Durian (sầu riêng), Guava (ổi), Jackfruit (mít), Tomato (cà chua), Potato (khoai tây), Corn (ngô), Soybean (đậu nành), Cassava (sắn), Grape (nho), Squash (bí)
If only a single detached leaf is visible, list ALL plausible plant candidates.

STEP 2 — ASSESS IMAGE QUALITY:
Evaluate the input image and note any issues:
- Is only a single detached leaf visible (no branch/fruit/flower for context)?
- Is the image blurry, low-resolution, or out of focus?
- Is there poor lighting or backlighting affecting color accuracy?
- Are fingers or objects obscuring parts of the leaf?
Report any issues that may reduce diagnosis accuracy.

STEP 3 — IDENTIFY SYMPTOMS:
Describe in detail: location, color, shape, size, pattern of any lesions or abnormalities.

STEP 4 — DIAGNOSIS:
Based on steps 1-3, provide your diagnosis.

OUTPUT FORMAT & LANGUAGE REQUIREMENT:
Respond ONLY with a valid JSON object in this exact schema.
All JSON keys MUST remain in English, but ALL textual values MUST be in natural, fluent Vietnamese for Vietnamese farmers:
{
  "reasoning": "Suy luận từng bước bằng tiếng Việt: quan sát hình thái lá → mô tả triệu chứng → logic chẩn đoán",
  "plant_candidates": ["cây 1", "cây 2"],
  "image_quality_warnings": ["cảnh báo nếu có"],
  "plant": "tên cây trồng chính xác nhất bằng tiếng Việt (ví dụ: Lúa, Cam, Chè)",
  "disease": "tên bệnh bằng tiếng Việt (ví dụ: Bệnh đạo ôn lá, Bệnh đốm mắt cua) hoặc 'Khỏe mạnh' hoặc 'Không phải ảnh cây trồng'",
  "confidence": 85,
  "severity": "nhẹ/trung bình/nặng/không",
  "description": "mô tả chi tiết triệu chứng quan sát được bằng tiếng Việt",
  "treatment": "khuyến nghị biện pháp phòng trừ và kỹ thuật canh tác bằng tiếng Việt",
  "medicines": ["tên thuốc BVTV hoặc hoạt chất khuyến nghị 1", "thuốc 2"]
}

Rules:
- All JSON keys MUST remain in English as specified above.
- All values MUST be written in natural Vietnamese for farmers in Vietnam.
- If the image is not a plant or leaf: set disease to 'Không phải ảnh cây trồng', confidence to 0, severity to 'không', medicines to [].
- If the plant is healthy: set disease to 'Khỏe mạnh', severity to 'không', medicines to [].
- Confidence is an integer between 0 and 100.
- Be specific about the disease name in Vietnamese.
- image_quality_warnings should be [] if the image is clear and has sufficient context.
- plant_candidates should list all plausible plants based on leaf morphology."""


def _encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64 JPEG string with EXIF auto-orientation and downscaling."""
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    img_rgb = image.convert("RGB")
    # Downscale so max dimension is at most 1024px for fast VLM inference and small payload
    max_dim = 1024
    if max(img_rgb.width, img_rgb.height) > max_dim:
        img_rgb.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _extract_json(content: str) -> dict:
    """Safely extract and parse JSON from model response even if formatted with markdown or commentary."""
    content = content.strip()

    # 1. Look for markdown code blocks (```json ... ``` or ``` ... ```)
    if "```" in content:
        for block in content.split("```"):
            b = block.strip()
            if b.startswith("json"):
                b = b[4:].strip()
            if b.startswith("{") and b.endswith("}"):
                try:
                    return json.loads(b)
                except Exception:
                    pass

    # 2. Extract substring between first '{' and last '}'
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = content[first_brace : last_brace + 1]
        try:
            return json.loads(json_str)
        except Exception:
            pass

    # 3. Direct JSON parse
    return json.loads(content)


def _call_vlm_once(b64: str, lang: str, temperature: float = 0, seed: int = 42, db = None) -> Optional[dict]:
    """Make a single VLM API call and return parsed result based on configured provider."""
    # Get settings from db (or use defaults)
    provider = "cliproxy"
    api_url = "http://152.67.112.145:8317/v1/chat/completions"
    api_key = "ai-teaching-assistant-prod"
    model_name = "gpt-5.5"

    if db is not None:
        p_setting = db.query(Setting).filter(Setting.key == "llm_provider").first()
        if p_setting:
            provider = p_setting.value
        
        url_setting = db.query(Setting).filter(Setting.key == "llm_api_url").first()
        if url_setting:
            api_url = url_setting.value
            
        key_setting = db.query(Setting).filter(Setting.key == "llm_api_key").first()
        if key_setting:
            api_key = key_setting.value
            
        model_setting = db.query(Setting).filter(Setting.key == "llm_model_name").first()
        if model_setting:
            model_name = model_setting.value

    # If provider is cliproxy but setting is empty or defaults:
    # Use defaults if not set in db
    if not provider:
        provider = "cliproxy"
    if provider == "cliproxy":
        if not api_url:
            api_url = "http://152.67.112.145:8317/v1/chat/completions"
        if not api_key:
            api_key = "ai-teaching-assistant-prod"
        if not model_name:
            model_name = "gpt-5.5"
    elif provider == "openai":
        if not api_url:
            api_url = "https://api.openai.com/v1/chat/completions"
        if not model_name:
            model_name = "gpt-4o"
    elif provider == "google":
        if not model_name:
            model_name = "gemini-1.5-flash"

    prompt = SYSTEM_PROMPT_VI if lang == "vi" else SYSTEM_PROMPT

    if provider in ("cliproxy", "openai"):
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": "Phân tích bệnh cây trong ảnh này. Trả về JSON." if lang == "vi" else "Identify the plant disease in this image. Respond with JSON."},
                ]},
            ],
            "max_tokens": 2048,
            "temperature": temperature,
            "seed": seed,
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
    
    elif provider == "google":
        # Google Gemini native generateContent API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": b64
                            }
                        },
                        {
                            "text": "Phân tích bệnh cây trong ảnh này. Trả về JSON." if lang == "vi" else "Identify the plant disease in this image. Respond with JSON."
                        }
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": prompt}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return _extract_json(content)


def _majority_vote(results: list[dict]) -> dict:
    """Pick the most common (plant, disease) pair and merge best fields."""
    combos = [(str(r.get("plant") or "").strip(), str(r.get("disease") or "").strip()) for r in results]
    most_common = Counter(combos).most_common(1)[0][0]

    # Filter results matching the winning combo
    winners = [r for r in results if (str(r.get("plant") or "").strip(), str(r.get("disease") or "").strip()) == most_common]

    def _safe_conf(r):
        try:
            return int(float(str(r.get("confidence", 0)).replace('%', '').strip()))
        except Exception:
            return 0

    # Pick the result with highest confidence among winners
    best = max(winners, key=_safe_conf)

    # Average confidence across ALL results that match the winning combo
    avg_conf = round(sum(_safe_conf(r) for r in winners) / len(winners))

    best["confidence"] = avg_conf
    return best


def _format_result(result: dict, lang: str, voting_used: bool = False) -> dict:
    """Format parsed VLM result into prediction response."""
    disease_str = str(result.get("disease") or "Unknown").strip()
    is_healthy = disease_str.lower() in ("healthy", "khỏe mạnh")

    medicines = result.get("medicines", [])
    if not isinstance(medicines, list) or is_healthy:
        medicines = []
    else:
        medicines = [str(m).strip() for m in medicines if m]

    try:
        conf_val = int(float(str(result.get("confidence", 0)).replace('%', '').strip()))
    except Exception:
        conf_val = 0

    plant_str = str(result.get("plant") or "").strip()

    # Match medicines against pesticide database
    medicine_match = match_medicines(medicines) if medicines else {"matched_products": [], "banned_warning": []}

    # Extract image quality warnings
    image_quality_warnings = result.get("image_quality_warnings", [])
    if not isinstance(image_quality_warnings, list):
        image_quality_warnings = []
    else:
        image_quality_warnings = [str(w).strip() for w in image_quality_warnings if w]

    predictions = [{
        "label": disease_str,
        "confidence": conf_val,
        "name": f"{plant_str} - {disease_str}" if plant_str else disease_str,
        "description": str(result.get("description") or ""),
        "treatment": str(result.get("treatment") or "") if not is_healthy else "",
        "medicines": medicines,
        "severity": str(result.get("severity") or ""),
        "matched_products": medicine_match["matched_products"],
        "banned_warning": medicine_match["banned_warning"],
    }]

    return {
        "model_id": "plantdoctor_ai",
        "model_name": "PlantDoctor AI",
        "predictions": predictions,
        "image_quality_warnings": image_quality_warnings,
        "voting_used": voting_used,
    }


def _get_image_hash(image: Image.Image) -> imagehash.ImageHash:
    """Compute perceptual hash of an image."""
    return imagehash.phash(image.convert("RGB").resize((224, 224)))


def _find_cached(img_hash: imagehash.ImageHash, lang: str) -> Optional[dict]:
    """Find cached prediction for a similar image."""
    cache_key = f"{img_hash}_{lang}"
    # Exact match first (fastest)
    if cache_key in _prediction_cache:
        logger.info("Cache exact hit: hash=%s", img_hash)
        return _prediction_cache[cache_key]
    # Near-match: check Hamming distance
    for key, value in _prediction_cache.items():
        stored_hash_str, stored_lang = key.rsplit("_", 1)
        if stored_lang != lang:
            continue
        stored_hash = imagehash.hex_to_hash(stored_hash_str)
        distance = img_hash - stored_hash
        if distance < HASH_SIMILARITY_THRESHOLD:
            logger.info("Cache near hit: hash=%s, stored=%s, distance=%d", img_hash, stored_hash, distance)
            return value
    return None


def _store_cache(img_hash: imagehash.ImageHash, lang: str, result: dict):
    """Store prediction result in cache."""
    cache_key = f"{img_hash}_{lang}"
    _prediction_cache[cache_key] = result
    logger.info("Cached prediction: hash=%s, entries=%d/%d", img_hash, len(_prediction_cache), _prediction_cache.maxsize)


def predict_vlm(image: Image.Image, lang: str = "vi", db = None) -> Optional[dict]:
    """Use GPT-5.5 vision to identify plant disease with pHash caching + self-consistency voting."""

    # Step 1: Check pHash cache
    img_hash = _get_image_hash(image)
    cached = _find_cached(img_hash, lang)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cached"] = True
        return cached_copy

    # Step 2: Call VLM (cache miss)
    b64 = _encode_image(image)

    try:
        # Round 1: deterministic call
        result = _call_vlm_once(b64, lang, temperature=0, seed=42, db=db)
        if not result or not isinstance(result, dict):
            raise ValueError(f"Invalid result from VLM round 1: {result}")

        try:
            confidence = int(float(str(result.get("confidence", 0)).replace('%', '').strip()))
        except Exception:
            confidence = 0

        # Fast path: high confidence → return immediately
        if confidence >= VOTING_CONFIDENCE_THRESHOLD:
            logger.info("VLM prediction: %s (confidence=%d%%, no voting needed)", result.get("disease"), confidence)
            formatted = _format_result(result, lang, voting_used=False)
            _store_cache(img_hash, lang, formatted)
            return formatted

        # Low confidence → self-consistency voting
        logger.info("VLM confidence=%d%% < %d%%, triggering voting (%d rounds total)",
                     confidence, VOTING_CONFIDENCE_THRESHOLD, VOTING_ROUNDS)
        all_results = [result]

        for i in range(1, VOTING_ROUNDS):
            try:
                extra = _call_vlm_once(b64, lang, temperature=0.3, seed=42 + i * 17, db=db)
                if extra and isinstance(extra, dict):
                    all_results.append(extra)
                    logger.info("Voting round %d: %s (confidence=%s)", i + 1, extra.get("disease"), extra.get("confidence", 0))
            except Exception as e:
                logger.warning("Voting round %d failed: %s", i + 1, e)

        # Majority vote if we have multiple results
        if len(all_results) > 1:
            final = _majority_vote(all_results)
            # Preserve image_quality_warnings from the best result
            if "image_quality_warnings" not in final or not final["image_quality_warnings"]:
                for r in all_results:
                    if r.get("image_quality_warnings"):
                        final["image_quality_warnings"] = r["image_quality_warnings"]
                        break
            logger.info("Voting result: %s (averaged confidence=%s)", final.get("disease"), final.get("confidence", 0))
            formatted = _format_result(final, lang, voting_used=True)
        else:
            formatted = _format_result(result, lang, voting_used=False)

        # Store in cache
        _store_cache(img_hash, lang, formatted)
        return formatted

    except Exception as e:
        import traceback
        logger.error("VLM prediction failed: %s\n%s", e, traceback.format_exc())
        return None
