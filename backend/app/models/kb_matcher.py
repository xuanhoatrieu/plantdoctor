"""Multi-signal Knowledge Base Matcher (Image -> VLM Visual Features -> CABI Plantwise KB).

Matches the AI's visual diagnosis (plant, disease, visual description/reasoning)
against the curated CABI Plantwise Vietnam Knowledge Base in the `diseases` table,
returning the verified disease profile, self-hosted reference image URL, IPM prevention guide,
and standard active ingredients.
"""
import re
from typing import Optional
from ..database.models import Disease

_COMMON_STOP_WORDS = {
    "bệnh", "hại", "trên", "dưới", "của", "và", "hoặc", "do", "bởi", "cây",
    "in", "on", "of", "the", "and", "or", "by", "disease",
}

# Plant organs and crop names stripped ONLY when comparing disease names, so
# generic words like "lá", "cành", "sầu riêng" never cause two unrelated diseases
# on the same crop (e.g. "Bệnh nấm hồng trên cành" vs "Bệnh đốm rong hại lá và cành") to match.
_NAME_ONLY_STOP_WORDS = _COMMON_STOP_WORDS | {
    # Plant organs
    "lá", "cành", "thân", "rễ", "gốc", "ngọn", "quả", "trái", "búp", "bông",
    "hoa", "cổ", "hạt", "vỏ", "chồi", "bẹ", "củ", "nấm", "vi", "khuẩn",
    "leaf", "leaves", "stem", "root", "foot", "fruit", "berry", "branch", "twig",
    "sheath", "blight", "spot", "rot", "wilt",
    # Crop tokens
    "chè", "trà", "cam", "bưởi", "chanh", "quýt", "có", "múi", "lúa", "nếp",
    "mạ", "ngô", "bắp", "cà", "phê", "hồ", "tiêu", "ớt", "sầu", "riêng",
    "chua", "khoai", "tây", "chuối", "nhãn", "vải", "xoài", "thanh", "long",
    "rau", "màu", "cải", "súp", "lơ", "họ", "thập", "tự", "xanh", "lạc",
    "đậu", "phộng", "tương", "nành",
    "tea", "citrus", "rice", "corn", "maize", "coffee", "pepper", "chili",
    "durian", "tomato", "potato", "banana", "longan", "lychee", "mango",
    "dragon", "cabbage", "crucifer", "crucifers", "peanut", "soybean", "black",
}

_CROP_GROUPS = [
    {"chè", "trà", "camellia", "tea"},
    {"cam", "bưởi", "chanh", "quýt", "có múi", "citrus", "cam/bưởi"},
    {"lúa", "nếp", "mạ", "rice", "oryza"},
    {"ngô", "bắp", "corn", "maize", "zea"},
    {"cà phê", "coffee", "coffea"},
    {"hồ tiêu", "tiêu", "ớt", "hồ tiêu/ớt", "pepper", "chili"},
    {"sầu riêng", "durian"},
    {"cà chua", "tomato"},
    {"khoai tây", "potato"},
    {"chuối", "banana"},
    {"nhãn", "vải", "nhãn/vải", "longan", "lychee"},
    {"xoài", "mango"},
    {"thanh long", "dragon fruit"},
    {"bắp cải", "cải", "súp lơ", "rau", "rau màu/bắp cải", "cabbage", "crucifer"},
    {"lạc", "đậu phộng", "đậu tương", "đậu nành", "lạc/đậu tương", "peanut", "soybean"},
]


def _normalize_synonyms(text: str) -> str:
    low = (text or "").lower()
    # Normalize regional Vietnamese plant pathology synonyms
    low = low.replace("rỉ sắt", "gỉ sắt")
    low = low.replace("sương mai khoai tây", "mốc sương khoai tây")
    low = low.replace("sương mai cà chua", "mốc sương cà chua")
    low = low.replace("vàng lá greening", "vàng lá gân xanh greening")
    return low


def _tokenize(text: str, stop_words: set[str] = _COMMON_STOP_WORDS) -> set[str]:
    normed = _normalize_synonyms(text)
    clean = re.sub(
        r"[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]",
        " ",
        normed,
    )
    return {w for w in clean.split() if len(w) > 1 and w not in stop_words}


def _crop_group_index(crop_text: str) -> Optional[int]:
    low = (crop_text or "").lower().strip()
    if not low:
        return None
    # Sort all (alias, group_idx) pairs by alias length descending so specific multi-word
    # crop names like "bắp cải" (cabbage) always match before single words like "bắp" (corn).
    candidates = [
        (alias, idx)
        for idx, grp in enumerate(_CROP_GROUPS)
        for alias in grp
    ]
    candidates.sort(key=lambda item: len(item[0]), reverse=True)
    for alias, idx in candidates:
        if re.search(rf"(?<![a-zà-ỹ]){re.escape(alias)}(?![a-zà-ỹ])", low):
            return idx
    return None


def match_kb_disease(
    db,
    plant: str,
    disease: str,
    description: str = "",
    reasoning: str = "",
) -> Optional[dict]:
    """Match a VLM diagnosis against the CABI Plantwise Vietnam Knowledge Base."""
    if db is None or not disease:
        return None

    d_low = _normalize_synonyms(disease).strip()
    if d_low in ("healthy", "khỏe mạnh", "unknown", "không phải ảnh cây trồng", "not a plant"):
        return None

    try:
        rows = db.query(Disease).all()
    except Exception:
        return None
    if not rows:
        return None

    plant_grp = _crop_group_index(plant)
    disease_crop_grp = _crop_group_index(disease)
    disease_name_tokens = _tokenize(disease, _NAME_ONLY_STOP_WORDS)
    if not disease_name_tokens:
        disease_name_tokens = _tokenize(disease, _COMMON_STOP_WORDS)

    context_text = _normalize_synonyms(f"{disease} {description} {reasoning}")
    context_tokens = _tokenize(context_text, _COMMON_STOP_WORDS)

    _PEST_HEAD_TOKENS = {
        "nhện", "rầy", "sâu", "bọ", "ruồi", "mọt", "rệp",
        "mite", "mites", "leafhopper", "planthopper", "borer", "moth",
        "armyworm", "caterpillar", "aphid", "aphids", "psyllid", "leafminer", "bug",
    }

    best_row = None
    best_score = 0.0

    for row in rows:
        row_grp = _crop_group_index(row.crop or "")
        # Strict cross-crop filter: never attach a disease from a different crop group
        if plant_grp is not None and row_grp is not None and plant_grp != row_grp:
            continue
        if disease_crop_grp is not None and row_grp is not None and disease_crop_grp != row_grp:
            continue

        crop_score = 0.25 if (plant_grp is not None and plant_grp == row_grp) else 0.0

        # 1. Pathology-specific name similarity (Vietnamese + English)
        row_name_vi = _normalize_synonyms(row.name_vi or "")
        row_name_en = _normalize_synonyms(row.name_en or "")
        row_name_tokens = _tokenize(f"{row_name_vi} {row_name_en}", _NAME_ONLY_STOP_WORDS)
        if not row_name_tokens:
            row_name_tokens = _tokenize(f"{row_name_vi} {row_name_en}", _COMMON_STOP_WORDS)
        if not row_name_tokens:
            continue

        common_name_tokens = disease_name_tokens & row_name_tokens
        overlap_name = len(common_name_tokens) / max(1, min(len(disease_name_tokens), len(row_name_tokens)))

        # Core phrase bonus when >=2 pathology tokens match or full core phrase matches
        core_vi = re.sub(r"\([^)]*\)", "", row_name_vi).replace("bệnh", "").strip()
        core_d = re.sub(r"\([^)]*\)", "", d_low).replace("bệnh", "").strip()
        exact_bonus = 0.25 if (
            (core_vi and (core_vi in core_d or core_d in core_vi))
            or len(common_name_tokens) >= 2
        ) else 0.0
        name_score = min(0.75, overlap_name * 0.55 + exact_bonus)

        # 2. Scientific name match in disease/description/reasoning
        sci_tokens = [
            t for t in _tokenize(row.scientific_name or "", _COMMON_STOP_WORDS)
            if len(t) >= 5 and t not in ("physiological", "disorder", "subsp", "virus", "toxicity")
        ]
        sci_score = 0.35 if (sci_tokens and any(st in context_text for st in sci_tokens)) else 0.0

        # If the KB entry is an insect/mite pest, require pest head token match or scientific name match
        # so color words alone ("nâu", "đỏ", "vàng") never match a fungal leaf spot to a pest.
        row_pest_heads = row_name_tokens & _PEST_HEAD_TOKENS
        if row_pest_heads and not (disease_name_tokens & _PEST_HEAD_TOKENS) and sci_score == 0.0:
            continue

        # Guard: require a genuine pathology name match OR scientific taxon match.
        # Prevents unrelated diseases on the same crop from matching via crop_score + generic symptoms.
        if name_score < 0.25 and sci_score == 0.0:
            continue

        # 3. Visual symptom token overlap
        sym_tokens = _tokenize(row.symptoms_vi or "", _COMMON_STOP_WORDS)
        if sym_tokens and context_tokens:
            sym_overlap = len(context_tokens & sym_tokens) / max(6, min(20, len(sym_tokens)))
            sym_score = min(0.25, sym_overlap * 0.25)
        else:
            sym_score = 0.0

        total_score = crop_score + name_score + sci_score + sym_score
        if total_score > best_score:
            best_score = total_score
            best_row = row

    if best_row is None or best_score < 0.45:
        return None

    return {
        "id": best_row.id,
        "crop": best_row.crop or "",
        "name_vi": best_row.name_vi or "",
        "name_en": best_row.name_en or "",
        "scientific_name": best_row.scientific_name or "",
        "severity": best_row.severity or "medium",
        "symptoms_vi": best_row.symptoms_vi or "",
        "symptoms_en": best_row.symptoms_en or "",
        "conditions_vi": best_row.conditions_vi or "",
        "conditions_en": best_row.conditions_en or "",
        "prevention_vi": best_row.prevention_vi or "",
        "prevention_en": best_row.prevention_en or "",
        "treatment_vi": best_row.treatment_vi or "",
        "treatment_en": best_row.treatment_en or "",
        "image_url": best_row.image_url or "",
        "match_score": round(min(1.0, best_score), 2),
    }
