import base64
import io
import json
import logging
import urllib.request
from collections import Counter
from typing import Optional

import imagehash
from cachetools import TTLCache
from PIL import Image
from .pesticide_matcher import match_medicines

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

SYSTEM_PROMPT_VI = """Bạn là chuyên gia bệnh lý thực vật. Phân tích ảnh lá/cây và xác định bệnh.

BƯỚC 1 — NHẬN DẠNG CÂY:
Quan sát kỹ hình thái lá: hình dạng, mép lá (răng cưa/trơn), kiểu gân lá, bề mặt, đặc điểm cuống lá.
Đặc biệt chú ý:
- Lá cây có múi (cam/chanh/quýt/bưởi): hình oval, thường có tuyến dầu (đốm trong suốt khi soi sáng), cuống lá có cánh, có mùi thơm khi vò
- Lá chè: hình elip, mép răng cưa rõ, gân phụ cong lên, lá non mỏng mềm
- Lá cà phê: to, xanh đậm, bóng mặt trên, mọc đối xứng
- Lá lúa: dài hẹp, gân song song
Nếu chỉ thấy 1 lá đơn lẻ, hãy liệt kê TẤT CẢ các loại cây có thể

BƯỚC 2 — ĐÁNH GIÁ CHẤT LƯỢNG ẢNH:
Đánh giá ảnh đầu vào và ghi nhận các vấn đề:
- Chỉ có 1 lá đơn lẻ (không thấy cành/quả/hoa để xác nhận)?
- Ảnh bị mờ hoặc không đúng nét?
- Ánh sáng yếu hoặc ngược sáng ảnh hưởng màu sắc?
- Ngón tay/bàn tay che khuất phần lá?
Ghi nhận bất kỳ vấn đề nào có thể ảnh hưởng độ chính xác chẩn đoán.

BƯỚC 3 — NHẬN DẠNG TRIỆU CHỨNG:
Mô tả chi tiết: vị trí, màu sắc, hình dạng, kích thước, pattern của các vết tổn thương.

BƯỚC 4 — CHẨN ĐOÁN:
Dựa trên bước 1-3, đưa ra chẩn đoán.

Các cây trồng phổ biến tại Việt Nam cần xem xét:
Cây có múi (cam, chanh, quýt, bưởi), Lúa, Chè, Cà phê, Tiêu, Ớt, Xoài, Nhãn, Vải, Chuối, Sầu riêng, Ổi, Mít, Cà chua, Khoai tây, Ngô, Đậu nành, Sắn, Nho, Táo, Đào, Cherry, Dâu tây, Bí

Trả lời CHỈ bằng JSON hợp lệ theo format:
{
  "reasoning": "Suy luận từng bước: quan sát hình dạng lá → mô tả triệu chứng → logic chẩn đoán",
  "plant_candidates": ["cây 1", "cây 2"],
  "image_quality_warnings": ["cảnh báo 1", "cảnh báo 2"],
  "plant": "tên cây trồng chính xác nhất",
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
- Nêu cụ thể tên bệnh (cả tên thường và tên khoa học nếu có)
- image_quality_warnings phải là [] nếu ảnh rõ ràng và đủ context
- plant_candidates phải liệt kê tất cả loại cây có thể dựa trên hình thái lá"""


def _encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64 JPEG string."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _call_vlm_once(b64: str, lang: str, temperature: float = 0, seed: int = 42) -> Optional[dict]:
    """Make a single VLM API call and return parsed result."""
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
        "max_tokens": 800,
        "temperature": temperature,
        "seed": seed,
    }

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

    return json.loads(content)


def _majority_vote(results: list[dict]) -> dict:
    """Pick the most common (plant, disease) pair and merge best fields."""
    # Count (plant, disease) combinations
    combos = [(r.get("plant", ""), r.get("disease", "")) for r in results]
    most_common = Counter(combos).most_common(1)[0][0]

    # Filter results matching the winning combo
    winners = [r for r in results if (r.get("plant", ""), r.get("disease", "")) == most_common]

    # Pick the result with highest confidence among winners
    best = max(winners, key=lambda r: r.get("confidence", 0))

    # Average confidence across ALL results that match the winning combo
    avg_conf = round(sum(r.get("confidence", 0) for r in winners) / len(winners))

    best["confidence"] = avg_conf
    return best


def _format_result(result: dict, lang: str, voting_used: bool = False) -> dict:
    """Format parsed VLM result into prediction response."""
    is_healthy = result.get("disease", "").lower() in ("healthy", "khỏe mạnh")
    medicines = result.get("medicines", []) if not is_healthy else []

    # Match medicines against pesticide database
    medicine_match = match_medicines(medicines) if medicines else {"matched_products": [], "banned_warning": []}

    # Extract image quality warnings
    image_quality_warnings = result.get("image_quality_warnings", [])
    if not isinstance(image_quality_warnings, list):
        image_quality_warnings = []

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


def predict_vlm(image: Image.Image, lang: str = "vi") -> Optional[dict]:
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
        result = _call_vlm_once(b64, lang, temperature=0, seed=42)
        confidence = result.get("confidence", 0)

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
                extra = _call_vlm_once(b64, lang, temperature=0.3, seed=42 + i * 17)
                all_results.append(extra)
                logger.info("Voting round %d: %s (confidence=%d%%)", i + 1, extra.get("disease"), extra.get("confidence", 0))
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
            logger.info("Voting result: %s (averaged confidence=%d%%)", final.get("disease"), final.get("confidence", 0))
            formatted = _format_result(final, lang, voting_used=True)
        else:
            formatted = _format_result(result, lang, voting_used=False)

        # Store in cache
        _store_cache(img_hash, lang, formatted)
        return formatted

    except Exception as e:
        logger.error("VLM prediction failed: %s", e)
        return None
