import base64
import io
import json
import logging
import urllib.request
import uuid
from collections import Counter
from typing import Optional, Union, List

import imagehash
from cachetools import TTLCache
from PIL import Image, ImageOps
from .pesticide_matcher import match_medicines
from ..database.models import Setting

logger = logging.getLogger(__name__)

API_URL = "http://152.67.112.145:8317/v1/chat/completions"
API_KEY = "ai-teaching-assistant-prod"
MODEL = "gpt-5.5"

# Confidence threshold: below this triggers self-consistency voting
VOTING_CONFIDENCE_THRESHOLD = 75
VOTING_ROUNDS = 3  # Total calls including the first one

# pHash caching: same image(s) → same result (100% consistency)
_prediction_cache: TTLCache = TTLCache(maxsize=500, ttl=86400)
HASH_SIMILARITY_THRESHOLD = 10  # Hamming distance < 10 = same/very similar image

# Clarification sessions cache (stores pending sessions for interactive clarification)
# Max 300 sessions, expire after 30 minutes
_clarification_sessions: TTLCache = TTLCache(maxsize=300, ttl=1800)

SYSTEM_PROMPT = """You are an expert plant pathologist and agronomist. Analyze the provided plant/leaf image(s) and diagnose any disease.

STEP 1 — IDENTIFY THE PLANT:
- If multiple images are provided: Synthesize both. Use the overview image (plant/branch/whole leaves) to identify plant species and morphology, and use the close-up image to inspect fine lesion details.
- Carefully observe morphology: leaf shape, margins (serrated/smooth), venation, petiole, trunk/stem traits.
- If only a single detached leaf or a close-up lesion is visible, list ALL plausible plant candidates.
- If the image depicts ONLY a tree trunk, bark, or stem lesion (e.g. gummosis, canker, stem rot) without leaves: If the plant cannot be reliably identified, diagnose at the PATHOLOGICAL SYNDROME level (e.g. 'Stem Canker and Gummosis Syndrome' or 'Root Collar Rot').

STEP 2 — ASSESS IMAGE QUALITY & CONTEXT:
Evaluate the input:
- Is only a close-up lesion or detached leaf visible without wider context?
- Is the image blurry, poorly lit, or occluded?
Report any warnings in 'image_quality_warnings'.

STEP 3 — IDENTIFY SYMPTOMS:
Describe lesion morphology: color, concentric rings, halo, fungal fruiting bodies, moisture, necrosis.

STEP 4 — DIAGNOSIS:
If the user provides a plant hint, strictly prioritize diseases for that plant.

Respond ONLY with valid JSON in this exact format:
{
  "reasoning": "Step-by-step reasoning",
  "plant_candidates": ["plant1", "plant2"],
  "image_quality_warnings": ["warning1"],
  "plant": "most likely plant name in English",
  "disease": "disease name or 'Healthy'",
  "confidence": 85,
  "severity": "mild/moderate/severe/none",
  "description": "symptoms observed",
  "treatment": "recommended treatment and cultural practices",
  "medicines": ["active_ingredient1", "active_ingredient2"]
}

Rules:
- If not a plant, set disease to 'Not a plant image' and confidence to 0.
- If healthy, set severity to 'none' and medicines to [].
- Confidence is an integer 0-100.
"""

SYSTEM_PROMPT_VI = """Bạn là chuyên gia bệnh học thực vật và kỹ sư nông nghiệp hàng đầu. Hãy phân tích kỹ lưỡng (các) hình ảnh cây trồng/lá cây/thân cây và chẩn đoán bệnh chính xác.

BƯỚC 1 — NHẬN DIỆN CÂY TRỒNG:
- Khi có NHIỀU ẢNH (ví dụ: Ảnh 1 cận cảnh vết bệnh, Ảnh 2 toàn cảnh cành lá/toàn cây): BẮT BUỘC kết hợp cả hai. Dùng ảnh toàn cảnh để xác định chính xác loại cây trồng (dáng lá, gân, cuống, cành), dùng ảnh cận cảnh để soi chi tiết bào tử, quầng vàng, vết hoại tử.
- Quan sát kỹ hình thái cây phổ biến tại Việt Nam: Cam, Bưởi, Chanh, Lúa, Chè, Cà phê, Tiêu, Ớt, Cà chua, Sầu riêng, Chuối, Xoài, Ngô, Khoai tây, Sắn...
- Nếu người dùng cung cấp gợi ý loại cây (plant_hint): BẮT BUỘC ưu tiên chẩn đoán bệnh trên loại cây đó.
- Nếu chỉ có ảnh CẬN CẢNH vết bệnh trên phiến lá mà không thấy toàn thể chiếc lá, liệt kê TẤT CẢ các cây khả dĩ vào 'plant_candidates'.
- Nếu ảnh chỉ chụp THÂN/VỎ CÂY (xì mủ, nứt thân, loét gốc) mà không có lá hay hoa quả: Nếu không thể xác định loại cây chính xác, hãy chẩn đoán theo HỘI CHỨNG BỆNH HỌC (ví dụ: 'Hội chứng xì mủ nứt thân do nấm' hoặc 'Bệnh lở cổ rễ thối gốc').

BƯỚC 2 — ĐÁNH GIÁ CHẤT LƯỢNG VÀ NGỮ CẢNH ẢNH:
- Ghi nhận vào 'image_quality_warnings' nếu ảnh chụp quá sát chỉ thấy vết đốm, hoặc ảnh mờ, tối, che tay.

BƯỚC 3 — PHÂN TÍCH TRIỆU CHỨNG:
- Mô tả chi tiết hình dạng vết bệnh, quầng vàng, đốm hoại tử, mốc trắng/nâu/đen.

BƯỚC 4 — KẾT LUẬN & ĐIỀU TRỊ:
- Đưa ra biện pháp canh tác và danh sách hoạt chất/thuốc BVTV an toàn, phù hợp với danh mục lưu hành tại Việt Nam.

ĐỊNH DẠNG ĐẦU RA (JSON BẮT BUỘC):
Tất cả các key giữ nguyên tiếng Anh như mẫu dưới, nhưng toàn bộ giá trị văn bản PHẢI bằng TIẾNG VIỆT tự nhiên cho nông dân Việt Nam:
{
  "reasoning": "Suy luận từng bước: nhận diện cây → phân tích triệu chứng vết bệnh → kết luận",
  "plant_candidates": ["Cây 1", "Cây 2"],
  "image_quality_warnings": ["cảnh báo nếu ảnh cận cảnh thiếu cành lá hoặc bị mờ"],
  "plant": "Tên cây trồng (ví dụ: Cam, Bưởi, Lúa, Chè, Cà phê)",
  "disease": "Tên bệnh bằng tiếng Việt (ví dụ: Bệnh loét cam, Bệnh đạo ôn lá, Bệnh thán thư) hoặc 'Khỏe mạnh' hoặc 'Không phải ảnh cây trồng'",
  "confidence": 85,
  "severity": "nhẹ/trung bình/nặng/không",
  "description": "mô tả chi tiết triệu chứng quan sát được bằng tiếng Việt",
  "treatment": "khuyến nghị kỹ thuật xử lý và biện pháp phòng trừ bằng tiếng Việt",
  "medicines": ["tên hoạt chất hoặc thuốc BVTV khuyến nghị 1", "thuốc 2"]
}

Quy tắc:
- Key JSON bằng tiếng Anh, Value bằng tiếng Việt.
- Nếu không phải ảnh thực vật: disease = 'Không phải ảnh cây trồng', confidence = 0, severity = 'không', medicines = [].
- Nếu khỏe mạnh: disease = 'Khỏe mạnh', severity = 'không', medicines = [].
- Confidence là số nguyên từ 0 đến 100.
"""

PLANT_ICONS = [
    ("cam", "🍊"), ("bưởi", "🍈"), ("chanh", "🍋"), ("quýt", "🍊"), ("citrus", "🍊"),
    ("lúa", "🌾"), ("gạo", "🌾"), ("rice", "🌾"),
    ("chè", "🍵"), ("trà", "🍵"), ("tea", "🍵"),
    ("cà phê", "☕"), ("coffee", "☕"),
    ("sầu riêng", "🍈"), ("durian", "🍈"),
    ("tiêu", "🌿"), ("pepper", "🌿"),
    ("ớt", "🌶️"), ("chili", "🌶️"),
    ("cà chua", "🍅"), ("tomato", "🍅"),
    ("khoai tây", "🥔"), ("potato", "🥔"),
    ("ngô", "🌽"), ("bắp", "🌽"), ("corn", "🌽"),
    ("chuối", "🍌"), ("banana", "🍌"),
    ("xoài", "🥭"), ("mango", "🥭"),
    ("nho", "🍇"), ("grape", "🍇"),
    ("dưa", "🍈"), ("bí", "🎃"),
    ("sắn", "🌿"), ("khoai mì", "🌿"),
    ("táo", "🍎"), ("thân", "🪵"), ("gỗ", "🪵")
]


def _get_plant_icon(name: str) -> str:
    n = name.lower()
    for key, icon in PLANT_ICONS:
        if key in n:
            return icon
    return "🌿"


def _build_candidate_plants(candidates: list[str]) -> list[dict]:
    res = []
    seen = set()
    for c in candidates:
        c_clean = str(c).strip()
        if not c_clean or c_clean.lower() in seen:
            continue
        seen.add(c_clean.lower())
        icon = _get_plant_icon(c_clean)
        res.append({"id": c_clean.lower().replace(" ", "_"), "name": c_clean, "icon": icon})

    if not res:
        res = [
            {"id": "citrus", "name": "Cây có múi (Cam, Bưởi, Chanh)", "icon": "🍊"},
            {"id": "rice", "name": "Lúa", "icon": "🌾"},
            {"id": "tea", "name": "Chè", "icon": "🍵"},
            {"id": "coffee", "name": "Cà phê", "icon": "☕"},
        ]
    res.append({"id": "other", "name": "Cây khác / Không có trong danh sách", "icon": "🌿"})
    return res


def _encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64 JPEG string with EXIF auto-orientation and downscaling."""
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    img_rgb = image.convert("RGB")
    max_dim = 1024
    if max(img_rgb.width, img_rgb.height) > max_dim:
        img_rgb.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _extract_json(content: str) -> dict:
    """Safely extract and parse JSON from model response even if formatted with markdown or commentary."""
    content = content.strip()

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

    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = content[first_brace : last_brace + 1]
        try:
            return json.loads(json_str)
        except Exception:
            pass

    return json.loads(content)


def _call_vlm_once(
    b64_list: list[str],
    lang: str,
    temperature: float = 0,
    seed: int = 42,
    db = None,
    plant_hint: Optional[str] = None
) -> Optional[dict]:
    """Make a single VLM API call with 1 or more images and optional plant hint."""
    provider = "cliproxy"
    api_url = "http://152.67.112.145:8317/v1/chat/completions"
    api_key = "ai-teaching-assistant-prod"
    model_name = "gpt-5.5"

    if db is not None:
        p_setting = db.query(Setting).filter(Setting.key == "llm_provider").first()
        if p_setting and p_setting.value:
            provider = p_setting.value

        url_setting = db.query(Setting).filter(Setting.key == "llm_api_url").first()
        if url_setting and url_setting.value:
            api_url = url_setting.value

        key_setting = db.query(Setting).filter(Setting.key == "llm_api_key").first()
        if key_setting and key_setting.value:
            api_key = key_setting.value

        model_setting = db.query(Setting).filter(Setting.key == "llm_model_name").first()
        if model_setting and model_setting.value:
            model_name = model_setting.value

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
        user_content = []
        if len(b64_list) == 1:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_list[0]}"}})
            instruction = "Phân tích bệnh cây trong ảnh này. Trả về JSON." if lang == "vi" else "Identify the plant disease in this image. Respond with JSON."
            if plant_hint:
                instruction += f" [LƯU Ý: Người dùng chỉ định đây là cây {plant_hint}. Hãy tập trung chẩn đoán bệnh trên cây {plant_hint}]."
            user_content.append({"type": "text", "text": instruction})
        else:
            labels_vi = ["Ảnh 1 (Cận cảnh vết bệnh)", "Ảnh 2 (Toàn cảnh cành lá/toàn cây)", "Ảnh 3 (Bộ phận khác)"]
            labels_en = ["Image 1 (Close-up of lesion)", "Image 2 (Overview of plant/branch)", "Image 3 (Other view)"]
            for idx, b64 in enumerate(b64_list):
                lbl = labels_vi[idx] if lang == "vi" else labels_en[idx] if idx < len(labels_vi) else f"Ảnh {idx + 1}"
                user_content.append({"type": "text", "text": f"[{lbl}]:"})
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

            instruction = (
                "Phân tích kết hợp các ảnh trên (Ảnh 1 cận cảnh vết bệnh + Ảnh 2 tổng thể cành lá/cây) để chẩn đoán chính xác loại cây và bệnh. Trả về JSON."
                if lang == "vi"
                else "Analyze and synthesize the images above (Image 1 close-up + Image 2 plant overview) to accurately identify the plant and disease. Respond with JSON."
            )
            if plant_hint:
                instruction += f" [LƯU Ý: Người dùng chỉ định đây là cây {plant_hint}. Hãy tập trung chẩn đoán bệnh trên cây {plant_hint}]."
            user_content.append({"type": "text", "text": instruction})

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        parts = []
        for b64 in b64_list:
            parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})

        instruction = "Phân tích bệnh cây trong các ảnh này. Trả về JSON." if lang == "vi" else "Identify the plant disease in these images. Respond with JSON."
        if plant_hint:
            instruction += f" Người dùng chỉ định đây là cây: {plant_hint}."
        parts.append({"text": instruction})

        payload = {
            "contents": [{"parts": parts}],
            "systemInstruction": {"parts": [{"text": prompt}]},
            "generationConfig": {"responseMimeType": "application/json", "temperature": temperature},
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
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

    winners = [r for r in results if (str(r.get("plant") or "").strip(), str(r.get("disease") or "").strip()) == most_common]

    def _safe_conf(r):
        try:
            return int(float(str(r.get("confidence", 0)).replace('%', '').strip()))
        except Exception:
            return 0

    best = max(winners, key=_safe_conf)
    avg_conf = round(sum(_safe_conf(r) for r in winners) / len(winners))
    best["confidence"] = avg_conf
    return best


def _format_result(
    result: dict,
    lang: str,
    voting_used: bool = False,
    status: str = "success",
    candidate_plants: list = None,
    clarification_message: str = None,
    session_token: str = None,
) -> dict:
    """Format parsed VLM result into prediction response schema."""
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
    medicine_match = match_medicines(medicines) if medicines else {"matched_products": [], "banned_warning": []}

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
        "status": status,
        "candidate_plants": candidate_plants or [],
        "clarification_message": clarification_message,
        "preliminary_symptoms": str(result.get("description") or "") if status == "needs_clarification" else None,
        "session_token": session_token,
    }


def _get_images_hash(images: list[Image.Image]) -> str:
    """Compute combined perceptual hash for a list of images."""
    hashes = []
    for img in images[:2]:
        hashes.append(str(imagehash.phash(img.convert("RGB").resize((224, 224)))))
    return "_".join(hashes)


def _find_cached(cache_key: str) -> Optional[dict]:
    """Find exact cached prediction."""
    if cache_key in _prediction_cache:
        logger.info("Cache exact hit: key=%s", cache_key)
        return _prediction_cache[cache_key]
    return None


def _store_cache(cache_key: str, result: dict):
    """Store prediction result in cache."""
    _prediction_cache[cache_key] = result
    logger.info("Cached prediction: key=%s, entries=%d/%d", cache_key, len(_prediction_cache), _prediction_cache.maxsize)


def predict_vlm(
    images: Union[Image.Image, List[Image.Image]],
    lang: str = "vi",
    db = None,
    plant_hint: Optional[str] = None
) -> Optional[dict]:
    """Use GPT-5.5 vision to identify plant disease with multi-image support, hint filtering, and interactive clarification."""
    if isinstance(images, (list, tuple)):
        img_list = list(images)
    else:
        img_list = [images]

    if not img_list:
        return None

    # Step 1: Check pHash cache
    img_hash_str = _get_images_hash(img_list)
    cache_key = f"{img_hash_str}_{lang}_{plant_hint or ''}"
    cached = _find_cached(cache_key)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cached"] = True
        return cached_copy

    # Step 2: Encode images to base64
    b64_list = [_encode_image(img) for img in img_list]

    try:
        # Round 1: deterministic inference
        result = _call_vlm_once(b64_list, lang, temperature=0, seed=42, db=db, plant_hint=plant_hint)
        if not result or not isinstance(result, dict):
            raise ValueError(f"Invalid result from VLM round 1: {result}")

        try:
            confidence = int(float(str(result.get("confidence", 0)).replace('%', '').strip()))
        except Exception:
            confidence = 0

        # Step 3: Interactive Clarification Trigger
        # If user did NOT specify plant, provided only 1 image, and confidence is low or multiple plant candidates exist:
        candidates = result.get("plant_candidates", [])
        warnings = [str(w).lower() for w in result.get("image_quality_warnings", [])]
        is_closeup_or_ambiguous = any("single detached leaf" in w or "cận cảnh" in w or "chưa rõ" in w or "thiếu" in w for w in warnings)

        should_clarify = (
            plant_hint is None
            and len(img_list) == 1
            and (
                confidence < 70
                or (len(candidates) >= 2 and confidence < 78 and is_closeup_or_ambiguous)
            )
        )

        if should_clarify:
            session_token = uuid.uuid4().hex
            _clarification_sessions[session_token] = {
                "b64_list": b64_list,
                "initial_result": result,
                "lang": lang,
            }
            cand_plants = _build_candidate_plants(candidates)
            msg = (
                "Ảnh chụp rất cận cảnh vết bệnh nên chưa thấy rõ hình thái cành lá. Để kết quả chính xác 100%, bạn đang trồng loại cây nào dưới đây?"
                if lang == "vi"
                else "The image shows a close-up lesion without clear leaf morphology. Please confirm which crop you are growing for an exact diagnosis:"
            )
            formatted = _format_result(
                result,
                lang,
                voting_used=False,
                status="needs_clarification",
                candidate_plants=cand_plants,
                clarification_message=msg,
                session_token=session_token,
            )
            return formatted

        # Step 4: High confidence → return directly
        if confidence >= VOTING_CONFIDENCE_THRESHOLD:
            logger.info("VLM prediction: %s (confidence=%d%%, no voting needed)", result.get("disease"), confidence)
            formatted = _format_result(result, lang, voting_used=False, status="success")
            _store_cache(cache_key, formatted)
            return formatted

        # Step 5: Low confidence → self-consistency voting
        logger.info("VLM confidence=%d%% < %d%%, triggering voting (%d rounds total)",
                     confidence, VOTING_CONFIDENCE_THRESHOLD, VOTING_ROUNDS)
        all_results = [result]

        for i in range(1, VOTING_ROUNDS):
            try:
                extra = _call_vlm_once(b64_list, lang, temperature=0.3, seed=42 + i * 17, db=db, plant_hint=plant_hint)
                if extra and isinstance(extra, dict):
                    all_results.append(extra)
                    logger.info("Voting round %d: %s (confidence=%s)", i + 1, extra.get("disease"), extra.get("confidence", 0))
            except Exception as e:
                logger.warning("Voting round %d failed: %s", i + 1, e)

        if len(all_results) > 1:
            final = _majority_vote(all_results)
            if "image_quality_warnings" not in final or not final["image_quality_warnings"]:
                for r in all_results:
                    if r.get("image_quality_warnings"):
                        final["image_quality_warnings"] = r["image_quality_warnings"]
                        break
            logger.info("Voting result: %s (averaged confidence=%s)", final.get("disease"), final.get("confidence", 0))
            formatted = _format_result(final, lang, voting_used=True, status="success")
        else:
            formatted = _format_result(result, lang, voting_used=False, status="success")

        _store_cache(cache_key, formatted)
        return formatted

    except Exception as e:
        import traceback
        logger.error("VLM prediction failed: %s\n%s", e, traceback.format_exc())
        return None


def clarify_vlm(session_token: str, selected_plant: str, lang: str = "vi", db = None) -> Optional[dict]:
    """Resolve a pending clarification session by passing the user selected plant."""
    session = _clarification_sessions.get(session_token)
    if not session:
        logger.warning("Clarification session expired or not found: %s", session_token)
        return None

    b64_list = session["b64_list"]
    initial_res = session["initial_result"]

    try:
        result = _call_vlm_once(b64_list, lang, temperature=0, seed=42, db=db, plant_hint=selected_plant)
        if not result or not isinstance(result, dict):
            result = dict(initial_res)
            result["plant"] = selected_plant
            result["confidence"] = max(80, int(result.get("confidence", 75)))
    except Exception as e:
        logger.error("Clarify VLM call failed: %s, falling back to initial with plant override", e)
        result = dict(initial_res)
        result["plant"] = selected_plant
        result["confidence"] = max(80, int(result.get("confidence", 75)))

    formatted = _format_result(result, lang, voting_used=False, status="success")
    # Invalidate session
    _clarification_sessions.pop(session_token, None)
    return formatted
