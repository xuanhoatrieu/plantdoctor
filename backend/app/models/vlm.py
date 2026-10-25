import base64
import io
import json
import logging
import os
import re
import urllib.request
import uuid
from collections import Counter
from typing import Optional, Union, List

import imagehash
from cachetools import TTLCache
from PIL import Image, ImageFilter, ImageOps, ImageStat
from .pesticide_matcher import match_medicines
from ..database.models import Setting, Disease, DiagnosisFeedback  # noqa: F401  (kept for backwards-compatible imports)
from ..llm_config import resolve_llm_config

logger = logging.getLogger(__name__)

# LLM endpoint, key and model come from Admin Settings / environment (see app/llm_config.py).

# Confidence threshold: below this triggers self-consistency voting
VOTING_CONFIDENCE_THRESHOLD = 75
VOTING_ROUNDS = 3  # Total calls including the first one

# pHash caching: same image(s) + same model → same result (100% consistency)
_prediction_cache: TTLCache = TTLCache(maxsize=500, ttl=86400)
HASH_SIMILARITY_THRESHOLD = 4  # Tight Hamming distance < 4 = re-compressed/resized copy of the exact same photo

# Clarification sessions cache (stores pending sessions for interactive clarification)
# Max 300 sessions, expire after 30 minutes
_clarification_sessions: TTLCache = TTLCache(maxsize=300, ttl=1800)

# Temperate trees commonly hallucinated by PlantVillage-biased models on Vietnamese leaf photos
_TEMPERATE_HALLUCINATIONS = (
    "óc chó", "walnut", "juglans",
    "cây phong", "lá phong", "maple",
    "cây sồi", "oak",
    "việt quất", "blueberry",
    "anh đào", "cherry",
    "dẻ gai", "beech",
    "hạnh nhân", "almond",
)


def clear_prediction_cache() -> None:
    """Clear in-memory prediction and clarification caches (e.g. when Admin updates LLM settings)."""
    n_pred = len(_prediction_cache)
    n_clar = len(_clarification_sessions)
    _prediction_cache.clear()
    _clarification_sessions.clear()
    logger.info("Cleared prediction cache (%d entries) and clarification sessions (%d entries)", n_pred, n_clar)

# Image quality gate thresholds (evaluated BEFORE calling the VLM, so rejected images cost nothing).
# Brightness = mean grayscale (0-255). Sharpness = variance of a Laplacian-filtered, 512px-downscaled image.
QUALITY_MIN_SIDE_PX = 300
QUALITY_DARK_THRESHOLD = 45
QUALITY_BRIGHT_THRESHOLD = 235
# Calibrated on a synthetic Gaussian-blur series of a 1200px leaf photo: sharp ≈ 850, radius 3 ≈ 90,
# radius 5 ≈ 44, radius 8 ≈ 29 (close-up crops score lower: sharp ≈ 410, radius 5 ≈ 30).
# This is a soft gate (user can override), but re-tune it once real field photos are collected.
QUALITY_BLUR_THRESHOLD = 50.0
_LAPLACIAN_KERNEL = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)

_QUALITY_MESSAGES = {
    "vi": {
        "low_resolution": "Ảnh có độ phân giải quá thấp ({w}x{h}px). Hãy chụp gần hơn hoặc dùng ảnh gốc từ camera.",
        "too_dark": "Ảnh quá tối, AI khó nhìn rõ màu sắc vết bệnh. Hãy chụp ở nơi đủ sáng hoặc bật đèn flash.",
        "overexposed": "Ảnh bị cháy sáng (quá chói). Hãy tránh nắng chiếu thẳng hoặc chụp ở chỗ có bóng râm nhẹ.",
        "blurry": "Ảnh bị mờ/nhòe. Hãy giữ chắc tay và chạm vào màn hình để lấy nét trước khi chụp.",
    },
    "en": {
        "low_resolution": "Image resolution is too low ({w}x{h}px). Move closer or use the original camera photo.",
        "too_dark": "Image is too dark for the AI to see lesion colors. Use better lighting or the flash.",
        "overexposed": "Image is overexposed. Avoid direct sunlight or shoot in light shade.",
        "blurry": "Image is blurry. Hold steady and tap to focus before shooting.",
    },
}


def assess_image_quality(image: Image.Image, lang: str = "vi") -> dict:
    """Cheap, local image quality check (no network). Returns metrics, issue codes and user-facing messages."""
    try:
        img = ImageOps.exif_transpose(image)
    except Exception:
        img = image
    width, height = img.size

    gray = img.convert("L")
    full = gray.copy()
    full.thumbnail((512, 512))
    brightness = ImageStat.Stat(full).mean[0]

    # Sharpness: take the max of the whole frame and the central 50% region (analysed at up to 1024px).
    # The subject is usually centred, while a defocused (bokeh) background should not count as "blurry".
    detail = gray.copy()
    detail.thumbnail((1024, 1024))
    dw, dh = detail.size
    center = detail.crop((dw // 4, dh // 4, dw - dw // 4, dh - dh // 4))
    sharpness = max(
        ImageStat.Stat(full.filter(_LAPLACIAN_KERNEL)).var[0],
        ImageStat.Stat(center.filter(_LAPLACIAN_KERNEL)).var[0],
    )

    issues = []
    if min(width, height) < QUALITY_MIN_SIDE_PX:
        issues.append("low_resolution")
    if brightness < QUALITY_DARK_THRESHOLD:
        issues.append("too_dark")
    elif brightness > QUALITY_BRIGHT_THRESHOLD:
        issues.append("overexposed")
    # Blur is meaningless on a nearly black/white frame, so only judge it when exposure is acceptable
    if "too_dark" not in issues and "overexposed" not in issues and sharpness < QUALITY_BLUR_THRESHOLD:
        issues.append("blurry")

    msgs = _QUALITY_MESSAGES.get(lang, _QUALITY_MESSAGES["vi"])
    messages = [msgs[code].format(w=width, h=height) for code in issues]
    return {
        "width": width,
        "height": height,
        "brightness": round(brightness, 1),
        "sharpness": round(sharpness, 1),
        "issues": issues,
        "messages": messages,
    }

SYSTEM_PROMPT = """You are an expert plant pathologist and agronomist specializing in tropical and subtropical crops in Vietnam. Analyze the provided plant/leaf/stem image(s) and diagnose any disease or pest damage.

STEP 1 — IDENTIFY THE PLANT:
- If multiple images are provided: Synthesize both. Use the overview image (plant/branch/whole leaves) to identify plant species and morphology, and use the close-up image to inspect fine lesion details.
- Carefully observe morphology: leaf shape, margins (serrated/smooth), venation, petiole, trunk/stem traits.
- Prioritize crops actually grown in Vietnam: Tea (Camellia sinensis), Citrus (Orange, Pomelo, Lime, Mandarin), Rice, Corn/Maize, Coffee, Black Pepper, Durian, Banana, Mango, Longan, Lychee, Guava, Tomato, Chili/Bell Pepper, Potato, Cassava, Soybean, Peanut, Cucurbits, Crucifers.
- NEVER hallucinate rare temperate forest trees (such as Walnut/Juglans, Maple, Oak, Birch, Cherry, Blueberry) on a single detached leaf. If leaf morphology is ambiguous on a single detached leaf, list 2-4 plausible Vietnamese crops in 'plant_candidates' and set 'confidence' <= 68 so the user is asked to confirm the crop.
- If the image depicts ONLY a tree trunk, bark, or stem lesion (e.g. gummosis, canker, stem rot) without leaves: If the plant cannot be reliably identified, diagnose at the PATHOLOGICAL SYNDROME level (e.g. 'Stem Canker and Gummosis Syndrome' or 'Root Collar Rot').

STEP 2 — ASSESS IMAGE QUALITY & CONTEXT:
Evaluate the input:
- Is only a close-up lesion or detached leaf visible without wider context?
- Is the image blurry, poorly lit, or occluded?
Report any warnings in 'image_quality_warnings'.

STEP 3 — DIFFERENTIAL DIAGNOSIS OF SYMPTOMS:
Carefully distinguish look-alike diseases before concluding:
- Tea (Camellia sinensis):
  * Blister blight (Exobasidium vexans): ONLY on young tender leaves/shoots; translucent yellow/pink spot that becomes CONCAVE on the upper surface and CONVEX/BLISTER-LIKE with a dense white-grey velvety spore layer on the lower surface. Do NOT diagnose Blister blight on flat, dry brown necrotic lesions of mature leaves!
  * Grey blight (Pestalotiopsis theae): Mature/maintenance leaves; large grey-brown to whitish-grey lesions starting at leaf tips/margins with distinct CONCENTRIC RINGS and tiny black dot-like acervuli/pycnidia.
  * Brown blight / Anthracnose (Colletotrichum camelliae): Dark reddish-brown necrotic patches from margins/tips, sharp boundary, lacking concentric grey rings or convex blisters.
  * Tea mosquito bug (Helopeltis theivora): Cluster of small angular/circular dark brown/black feeding punctures (1-3mm) on young shoots/leaves, causing curled, deformed, blackened shoots.
  * Tea green leafhopper (Empoasca onukii): Yellowing and reddish-brown marginal scorching (hopperburn) along young leaf edges.
  * Red spider mite (Oligonychus coffeae): Upper leaf surface turns dull bronze/rusty-reddish brown (especially along midrib) with fine whitish蜕/dust.
- Citrus (Orange, Pomelo, Lime):
  * Citrus canker (Xanthomonas citri): Raised corky/erumpent lesions on BOTH leaf surfaces with a cracked center and a distinct bright YELLOW HALO.
  * Citrus scab (Elsinoë fawcettii): Wart-like conical projections on ONE surface (hollowed on the opposite side) causing severe leaf distortion/wrinkling, buff/pinkish-grey, lacking a uniform yellow halo.
  * Citrus greening (HLB): Asymmetric blotchy mottling across the midrib or yellow lamina with green veins.
  * Citrus leafminer (Phyllocnistis citrella): Silvery serpentine mines under the epidermis of young leaves.
- Rice (Oryza sativa):
  * Rice blast (Magnaporthe oryzae): Diamond/spindle/eye-shaped lesions with pointed ends, grey-white center, dark brown border.
  * Brown spot (Bipolaris oryzae): Oval/sesame-seed shaped dark brown spots with uniform rounded ends.
  * Bacterial leaf blight (Xanthomonas oryzae): Water-soaked to yellow/straw-white wavy lesions progressing from leaf tip down along the margins.
- Corn (Zea mays):
  * Common/Southern rust (Puccinia): Raised pustules (uredinia) rupturing the epidermis to release cinnamon-brown/rusty spore powder.
  * Physoderma brown spot (Physoderma maydis): Very small flat yellowish-brown flecks in bands on the blade and dark brown/black coalescing blotches on the midrib; flat, NOT raised spore pustules.
  * Northern corn leaf blight (Exserohilum turcicum): Large (5-15cm) cigar/elliptical grey-green to tan lesions.

STEP 4 — DIAGNOSIS & CONFIDENCE CALIBRATION:
- If the user provides a plant hint, strictly prioritize diseases for that plant.
- Do NOT prefix the 'disease' field with tentative words like 'Suspected' or 'Possibly'. State the canonical disease/pest name cleanly.
- Calibrate 'confidence' honestly:
  * 85-95: Both crop morphology and textbook diagnostic symptoms are unmistakably clear.
  * 70-84: Symptoms are clear, minor context limitations.
  * 45-68: Close-up of a single leaf where crop species is uncertain (>=2 candidates) or symptoms overlap between multiple diseases.

Respond ONLY with valid JSON in this exact format:
{
  "reasoning": "Step-by-step reasoning: morphology -> differential diagnosis -> conclusion",
  "plant_candidates": ["plant1", "plant2"],
  "image_quality_warnings": ["warning1"],
  "plant": "most likely plant name in English",
  "disease": "clean canonical disease name or 'Healthy'",
  "confidence": 82,
  "severity": "mild/moderate/severe/none",
  "description": "detailed symptoms observed",
  "treatment": "recommended treatment and cultural practices",
  "medicines": ["active_ingredient1", "active_ingredient2"]
}

Rules:
- If not a plant, set disease to 'Not a plant image' and confidence to 0.
- If healthy, set severity to 'none' and medicines to [].
- Confidence is an integer 0-100.
"""

SYSTEM_PROMPT_VI = """Bạn là chuyên gia bệnh học thực vật và kỹ sư bảo vệ thực vật hàng đầu tại Việt Nam (Trường Đại học Nông Lâm Thái Nguyên). Hãy phân tích kỹ lưỡng (các) hình ảnh cây trồng/lá cây/thân cây và chẩn đoán chính xác bệnh hoặc tác nhân gây hại.

BƯỚC 1 — NHẬN DIỆN CÂY TRỒNG (CHỐNG ĐOÁN MÒ CÂY NGOẠI LAI):
- Khi có NHIỀU ẢNH (Ảnh 1 cận cảnh vết bệnh, Ảnh 2 toàn cảnh cành lá/toàn cây): BẮT BUỘC kết hợp cả hai. Dùng ảnh toàn cảnh để xác định chính xác loại cây trồng (dáng lá, răng cưa mép lá, gân lá, cuống lá, cành), dùng ảnh cận cảnh để soi chi tiết bào tử, quầng vàng, vết hoại tử.
- Ưu tiên tuyệt đối hệ cây trồng thực tế tại Việt Nam: Chè (Trà), Cam, Bưởi, Chanh, Quýt, Lúa, Ngô, Cà phê, Hồ tiêu, Sầu riêng, Chuối, Xoài, Nhãn, Vải, Ổi, Cà chua, Ớt, Khoai tây, Sắn, Đậu tương, Lạc, Dưa chuột, Bầu bí, Rau họ thập tự.
- TUYỆT ĐỐI KHÔNG đoán mò các cây gỗ ôn đới ngoại lai hiếm gặp (như: cây óc chó/walnut, cây phong/maple, cây sồi/oak, việt quất/blueberry, anh đào/cherry) khi chỉ nhìn thấy 1 chiếc lá rời!
- Nếu người dùng đã cung cấp gợi ý loại cây (plant_hint): BẮT BUỘC chẩn đoán bệnh/sâu hại trên đúng loại cây đó.
- Nếu người dùng CHƯA chọn cây và ảnh chỉ chụp 1 lá rời hoặc cận cảnh vết bệnh khiến việc nhận diện loài cây chưa chắc chắn 100%: Liệt kê 2–4 cây trồng Việt Nam khả dĩ nhất vào 'plant_candidates', đồng thời BẮT BUỘC chấm 'confidence' <= 68 để hệ thống hiển thị câu hỏi xác nhận loại cây với người dùng.
- Nếu ảnh chỉ chụp THÂN/VỎ CÂY (xì mủ, nứt thân, loét gốc) mà không có lá hay hoa quả: Nếu không thể xác định loại cây chính xác, hãy chẩn đoán theo HỘI CHỨNG BỆNH HỌC (ví dụ: 'Hội chứng xì mủ nứt thân do nấm Phytophthora' hoặc 'Bệnh lở cổ rễ thối gốc').

BƯỚC 2 — ĐÁNH GIÁ CHẤT LƯỢNG VÀ NGỮ CẢNH ẢNH:
- Ghi nhận vào 'image_quality_warnings' nếu ảnh chụp quá sát chỉ thấy một phần lá/một lá rời thiếu cành quả, hoặc ảnh mờ, tối, che tay.

BƯỚC 3 — CHẨN ĐOÁN PHÂN BIỆT TRIỆU CHỨNG (TRÁNH NHẦM LẪN PHỔ BIẾN):
Hãy đối chiếu kỹ các cặp bệnh dễ nhầm lẫn dưới đây trước khi kết luận:
1. TRÊN CÂY CHÈ (Camellia sinensis):
   - Bệnh phồng lá chè (nấm Exobasidium vexans): CHỈ xuất hiện trên lá non và búp non; vết bệnh tạo vùng lõm hình lòng chảo ở mặt trên và PHỒNG LỒI LÊN như mụn rộp ở mặt dưới, bề mặt vết phồng phủ lớp phấn mịn màu trắng xám (bào tử nấm). CẤM kết luận là Bệnh phồng lá chè nếu vết bệnh phẳng, khô cứng ở lá bánh tẻ/lá già hoặc không có cấu trúc phồng lồi!
   - Bệnh đốm xám / chấm xám lá chè (nấm Pestalotiopsis theae): Thường ở lá bánh tẻ và lá già; vết bệnh lớn từ chóp lá hoặc mép lá lan vào, màu nâu xám đến xám trắng khô, có CÁC VÒNG ĐỒNG TÂM rõ rệt và các chấm đen nhỏ li ti (ổ bào tử) xếp theo vòng.
   - Bệnh thán thư / đốm nâu cháy lá chè (nấm Colletotrichum camelliae): Vết cháy màu nâu đỏ đến nâu sẫm ở mép hoặc chóp lá, ranh giới rất rõ với phần mô xanh, không có vòng đồng tâm xám trắng rõ như đốm xám và không phồng lồi.
   - Bọ xít muỗi hại chè (Helopeltis theivora): Trên búp non/lá non có NHIỀU VẾT CHÍCH HÌNH ĐA GIÁC HOẶC TRÒN NHỎ (1–3mm) màu nâu đen tập trung dày đặc, làm lá non xoăn vặn, biến dạng, đọt non cháy đen.
   - Rầy xanh hại chè (Empoasca onukii): Mép lá non chuyển vàng rồi cháy khô màu nâu đỏ dọc theo rìa lá (cháy rìa lá), phiến lá hơi cong úp xuống.
   - Nhện đỏ nâu hại chè (Oligonychus coffeae): Mặt trên lá già/lá bánh tẻ chuyển màu đồng hun / đỏ gạch xỉn (nhất là dọc theo gân chính và nửa dưới lá), có lớp bụi trắng mịn li ti, không tạo đốm hoại tử lớn riêng lẻ.
   - Sâu vẽ bùa hại chè: Đường ngoằn nghèo màu trắng xám dưới lớp biểu bì lá.
2. TRÊN CÂY CÓ MÚI (Cam, Bưởi, Chanh, Quýt):
   - Bệnh loét cây có múi (vi khuẩn Xanthomonas citri): Vết đốm tròn nhô cao, SẦN SÙI HÓA BẦN (corky) ở CẢ HAI MẶT LÁ/quả, tâm vết loét nứt nhẹ, bao quanh bởi QUẦNG VÀNG TƯƠI (yellow halo) rất rõ và tròn đều.
   - Bệnh ghẻ sẹo / ghẻ nhám (nấm Elsinoë fawcettii): Mụn sần nhô lên chỉ ở MỘT MẶT LÁ (mặt đối diện lõm xuống hình phễu), làm phiến lá non BỊ CO RÚM, VẶN VẸO BIẾN DẠNG méo mó, màu xám hồng/vàng xám, KHÔNG có quầng vàng tròn đều như bệnh loét.
   - Bệnh vàng lá gân xanh (Greening / HLB): Lá vàng lốm đốm KHÔNG ĐỐI XỨNG qua gân chính (bên vàng bên xanh) hoặc phiến lá vàng nhạt nhưng gân lá vẫn xanh, lá nhỏ mọc dựng đứng.
   - Sâu vẽ bùa (Phyllocnistis citrella): Đường hầm ngoằn nghèo màu trắng bạc óng ánh trên lá non làm lá co кру.
3. TRÊN CÂY LÚA (Oryza sativa):
   - Bệnh đạo ôn lá (nấm Magnaporthe oryzae): Vết bệnh HÌNH THOI (hình mắt én) nhọn hai đầu, tâm màu xám trắng, viền nâu đậm.
   - Bệnh đốm nâu / tiêm lửa (nấm Bipolaris oryzae): Vết đốm HÌNH BẦU DỤC TRÒN ĐỀU như hạt vừng màu nâu đậm, không nhọn hai đầu.
   - Bệnh bạc lá vi khuẩn (Xanthomonas oryzae): Vết cháy dọc từ chóp lá và hai rìa mép lá lan xuống theo đường GỢN SÓNG màu vàng cam chuyển trắng xám.
   - Bệnh khô vằn (nấm Rhizoctonia solani): Vết bệnh lớn hình đám mây / vằn da báo màu xám xanh viền nâu tím ở bẹ và lá dưới.
4. TRÊN CÂY NGÔ (Zea mays):
   - Bệnh gỉ sắt ngô (nấm Puccinia sorghi / P. polysora): Các MỤN U NHỎ (pustules) NỔI GỒ trên mặt lá, làm nứt vỡ biểu bì giải phóng bột bào tử màu nâu đỏ / nâu gỉ sắt.
   - Bệnh đốm nâu ngô (nấm Physoderma maydis): Các chấm tròn rất nhỏ (1–2mm) màu vàng nâu phẳng xếp thành dải ngang trên phiến lá và đốm nâu đen lớn ở gân chính; bề mặt phẳng, KHÔNG phải mụn bột gỉ sắt nổi gồ vỡ biểu bì.
   - Bệnh cháy lá lớn (nấm Exserohilum turcicum): Vết bệnh lớn dài 5–15cm hình thoi dài / điếu xì gà màu xám xanh chuyển nâu xám.
   - Bệnh đốm lá nhỏ (nấm Bipolaris maydis): Vết đốm nhỏ hình chữ nhật/bầu dục dài bị giới hạn bởi hai gân lá song song.
5. TRÊN CÀ CHUA, ỚT, KHOAI TÂY:
   - Bệnh mốc sương / héo muộn (Phytophthora infestans): Mảng lớn bất định ở mép/chóp lá màu xanh tái ướt như luộc chuyển nâu đen sẫm, mặt dưới có mốc trắng mờ ở rìa vết bệnh, không có vòng đồng tâm.
   - Bệnh đốm vòng / cháy sớm (Alternaria solani): Đốm tròn nâu đen có CÁC VÒNG ĐỒNG TÂM như bia bắn rõ rệt.
   - Bệnh đốm vi khuẩn (Xanthomonas): Đốm nhỏ 1–3mm màu nâu đen ướt, không có vòng đồng tâm.
   - Bệnh xoăn vàng lá virus (TYLCV): Lá non nhỏ, xoăn cong lên phía trên, vàng mép lá.
6. TRÊN CÀ PHÊ, HỒ TIÊU, SẦU RIÊNG, CÂY ĂN QUẢ:
   - Bệnh gỉ sắt cà phê (Hemileia vastatrix): Mặt dưới lá có đốm bột màu VÀNG CAM / DA CAM đặc trưng, mặt trên là đốm vàng nhạt.
   - Bệnh đốm mắt cua cà phê (Cercospora coffeicola): Đốm tròn tâm trắng xám, viền nâu đỏ và quầng vàng rõ ở mặt trên.
   - Bệnh cháy lá / thán thư (Colletotrichum / Rhizoctonia): Vết cháy nâu từ chóp hoặc mép lá, hoặc mảng cháy lớn như bỏng nước sôi.

BƯỚC 4 — KẾT LUẬN, ĐẶT TÊN BỆNH & CHẤM ĐIỂM ĐỘ TIN CẬY (CONFIDENCE):
- Trường 'disease' PHẢI là tên bệnh hoặc tác nhân gây hại chuẩn xác, ngắn gọn (ví dụ: 'Bệnh đốm xám lá chè', 'Bọ xít muỗi hại chè', 'Nhện đỏ nâu hại chè', 'Bệnh loét cây có múi', 'Bệnh gỉ sắt ngô'). TUYỆT ĐỐI KHÔNG viết các từ ngập ngừng như 'Nghi...', 'Có thể...', 'Nghi ngờ cao...' vào trong trường 'disease' (mọi lập luận phân vân hãy viết vào 'reasoning' và 'description').
- Thang điểm 'confidence' nghiêm ngặt (không tự chấm điểm cao ảo):
  * 85 – 95: Nhìn rõ cả hình thái cây trồng VÀ triệu chứng đặc trưng điển hình không thể nhầm lẫn.
  * 70 – 84: Nhìn rõ triệu chứng bệnh đặc trưng, loại cây đã rõ hoặc đã được người dùng chỉ định.
  * 45 – 68: Ảnh chỉ chụp 1 lá rời/cận cảnh chưa chắc chắn loại cây (có >= 2 ứng viên trong 'plant_candidates'), hoặc triệu chứng ở giai đoạn đầu dễ nhầm giữa các bệnh.
- Đưa ra biện pháp canh tác và danh sách hoạt chất BVTV phổ biến, hợp pháp tại Việt Nam (chỉ ghi tên hoạt chất chuẩn trong mảng 'medicines', ví dụ: ["Hexaconazole", "Mancozeb", "Đồng Oxychloride", "Abamectin"]).

ĐỊNH DẠNG ĐẦU RA (JSON BẮT BUỘC):
Tất cả các key giữ nguyên tiếng Anh như mẫu dưới, toàn bộ giá trị văn bản bằng TIẾNG VIỆT tự nhiên:
{
  "reasoning": "Suy luận từng bước: (1) Nhận diện hình thái lá/cây -> (2) Phân tích chi tiết vết bệnh (màu sắc, độ lồi/lõm, vòng đồng tâm, quầng vàng, vị trí lá non/già) -> (3) Loại trừ các bệnh dễ nhầm -> (4) Kết luận",
  "plant_candidates": ["Cây 1", "Cây 2"],
  "image_quality_warnings": ["cảnh báo nếu ảnh chỉ có 1 lá rời cận cảnh thiếu cành lá hoặc bị mờ"],
  "plant": "Tên cây trồng (ví dụ: Chè, Cam, Bưởi, Lúa, Ngô, Cà phê, Cà chua)",
  "disease": "Tên bệnh/sâu hại chuẩn bằng tiếng Việt hoặc 'Khỏe mạnh' hoặc 'Không phải ảnh cây trồng'",
  "confidence": 82,
  "severity": "nhẹ/trung bình/nặng/không",
  "description": "mô tả chi tiết triệu chứng quan sát được và đặc điểm phân biệt bằng tiếng Việt",
  "treatment": "khuyến nghị kỹ thuật xử lý canh tác và phòng trừ bằng tiếng Việt",
  "medicines": ["Tên hoạt chất 1", "Tên hoạt chất 2"]
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


def _is_temperate_hallucination(plant_name: str, disease_name: str = "") -> bool:
    """Return True if the model guessed an exotic temperate tree rarely grown in Vietnam."""
    combined = f"{plant_name} {disease_name}".lower()
    return any(term in combined for term in _TEMPERATE_HALLUCINATIONS)


def _clean_disease_label(raw: str) -> str:
    """Strip tentative prefixes/suffixes ('Nghi...', ', nghi ngờ cao') so labels are clean and canonical."""
    s = str(raw or "").strip()
    if not s:
        return "Unknown"
    # Strip leading tentative prefixes in Vietnamese/English
    s = re.sub(r"^(?:nghi\s+ngờ\s+cao|nghi\s+ngờ|nghi\s+là|nghi|có\s+thể\s+là|có\s+khả\s+năng\s+là|suspected|possibly)\s+", "", s, flags=re.IGNORECASE).strip()
    # Strip trailing tentative clauses
    s = re.sub(r"[,;–-]\s*(?:nghi\s+ngờ\s+cao|nghi\s+ngờ|chưa\s+loại\s+trừ.*|không\s+phải\s+bệnh\s+nấm\s+điển\s+hình.*)$", "", s, flags=re.IGNORECASE).strip()
    if s:
        s = s[0].upper() + s[1:]
    return s or "Unknown"


def _normalize_vote_key(text: str) -> str:
    """Normalize a plant or disease string into a canonical key for majority voting."""
    s = _clean_disease_label(text).lower()
    # Remove parenthetical scientific names and pathogen tails ('do nấm...', 'do vi khuẩn...', 'trên cây...')
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(?:do\s+nấm|do\s+vi\s+khuẩn|do\s+virus|do\s+vi\s+sinh\s+vật|trên\s+cây|trên\s+lá)\b.*$", " ", s)
    s = re.sub(r"^(?:cây|bệnh|hội\s+chứng|tác\s+nhân)\s+", "", s.strip())
    # Collapse punctuation/synonyms
    s = s.replace("rỉ sắt", "gỉ sắt").replace("chấm xám", "đốm xám")
    if "," in s:
        s = s.split(",", 1)[0]
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _build_candidate_plants(candidates: list[str]) -> list[dict]:
    res = []
    seen = set()
    for c in candidates:
        c_clean = str(c).strip()
        if not c_clean or c_clean.lower() in seen or _is_temperate_hallucination(c_clean):
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


def _encode_image(image: Image.Image, max_dim: int = 1024) -> str:
    """Convert PIL Image to base64 JPEG string with EXIF auto-orientation and downscaling."""
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    img_rgb = image.convert("RGB")
    if max(img_rgb.width, img_rgb.height) > max_dim:
        img_rgb.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _extract_lesion_crop(image: Image.Image) -> Optional[Image.Image]:
    """Lightweight model-agnostic lesion ROI auto-crop (no YOLO/GPU needed).

    Scans a 3x3 grid over the central 80% of the image, scoring each window by
    Laplacian edge energy (lesion borders/spores) + R-G color anomaly (necrosis/chlorosis/rust)
    with a gentle center prior, and returns the highest-scoring 1:1 crop.
    """
    try:
        img = ImageOps.exif_transpose(image).convert("RGB")
    except Exception:
        img = image.convert("RGB")

    w, h = img.size
    min_side = min(w, h)
    if min_side < 480:
        return None

    crop_side = max(256, min(512, int(min_side * 0.48)))
    margin_x = int(w * 0.10)
    margin_y = int(h * 0.10)
    usable_w = max(crop_side, w - 2 * margin_x)
    usable_h = max(crop_side, h - 2 * margin_y)

    best_score = -1.0
    best_box = None

    for gy in range(3):
        for gx in range(3):
            x0 = margin_x + int((usable_w - crop_side) * (gx / 2.0))
            y0 = margin_y + int((usable_h - crop_side) * (gy / 2.0))
            x0 = max(0, min(w - crop_side, x0))
            y0 = max(0, min(h - crop_side, y0))
            patch = img.crop((x0, y0, x0 + crop_side, y0 + crop_side))

            # Downsample patch to 128x128 for fast (<2ms) saliency scoring
            small = patch.resize((128, 128), Image.Resampling.BILINEAR)
            gray = small.convert("L")
            edge_var = ImageStat.Stat(gray.filter(_LAPLACIAN_KERNEL)).var[0]

            r_ch, g_ch, _ = small.split()
            # Variance in R and G channels captures brown/yellow/orange spots against green leaf
            r_std = ImageStat.Stat(r_ch).stddev[0]
            g_std = ImageStat.Stat(g_ch).stddev[0]
            color_contrast = r_std + g_std

            center_weight = 1.0 - 0.12 * (abs(gx - 1) + abs(gy - 1))
            score = (edge_var + 2.5 * color_contrast) * center_weight
            if score > best_score:
                best_score = score
                best_box = (x0, y0, x0 + crop_side, y0 + crop_side)

    if best_box is None:
        return None
    return img.crop(best_box)


def _auto_lesion_crop_b64(b64_str: str) -> Optional[str]:
    """Decode a base64 image, extract the highest-saliency lesion ROI crop, and re-encode."""
    try:
        raw = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        roi = _extract_lesion_crop(img)
        if roi is None:
            return None
        return _encode_image(roi, max_dim=512)
    except Exception:
        return None


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


_CROP_HINT_SYNONYMS = {
    "trà": "chè",
    "tea": "chè",
    "cam": "cam/bưởi",
    "bưởi": "cam/bưởi",
    "chanh": "cam/bưởi",
    "quýt": "cam/bưởi",
    "cây có múi": "cam/bưởi",
    "citrus": "cam/bưởi",
    "bắp": "ngô",
    "corn": "ngô",
    "tiêu": "hồ tiêu/ớt",
    "ớt": "hồ tiêu/ớt",
    "nhãn": "nhãn/vải",
    "vải": "nhãn/vải",
}


def _load_db_disease_context(db, plant_hint: Optional[str], lang: str) -> str:
    """Load expert-curated disease reference entries and reviewed feedback corrections from DB."""
    if db is None:
        return ""
    sections: list[str] = []
    try:
        all_rows = db.query(Disease).order_by(Disease.crop, Disease.name_vi).all()
        if all_rows:
            if plant_hint:
                raw_tokens = [t.strip().lower() for t in re.split(r"[/,;-]", plant_hint) if t.strip()]
                expanded_tokens = set(raw_tokens)
                for tok in raw_tokens:
                    if tok in _CROP_HINT_SYNONYMS:
                        expanded_tokens.add(_CROP_HINT_SYNONYMS[tok])
                matched = []
                for row in all_rows:
                    crop_low = (row.crop or "").lower()
                    if any(tok in crop_low or crop_low in tok for tok in expanded_tokens):
                        matched.append(row)
                rows = matched if matched else all_rows[:25]
            else:
                rows = all_rows[:35]

            lines = []
            for d in rows:
                if lang == "vi":
                    sym = (d.symptoms_vi or "")[:280]
                    cond = f" Điều kiện: {(d.conditions_vi or '')[:120]}." if getattr(d, "conditions_vi", "") else ""
                    trt = (d.treatment_vi or "")[:160]
                    lines.append(f"- [{d.crop}] {d.name_vi} ({d.scientific_name}): {sym}{cond} Hoạt chất/Xử lý: {trt}")
                else:
                    sym = (d.symptoms_en or d.symptoms_vi or "")[:280]
                    trt = (d.treatment_en or d.treatment_vi or "")[:160]
                    lines.append(f"- [{d.crop}] {d.name_en or d.name_vi} ({d.scientific_name}): {sym} Treatment: {trt}")

            if lang == "vi":
                if plant_hint:
                    header = (
                        f"\n\nKHO TRI THỨC BỆNH CÂY CHUẨN CHO CÂY '{plant_hint}' "
                        f"(BẮT BUỘC ưu tiên đối chiếu với danh mục này):\n"
                    )
                else:
                    header = "\n\nKHO TRI THỨC BỆNH CÂY VIỆT NAM THAM CHIẾU (ĐỐI CHIẾU TRIỆU CHỨNG):\n"
            else:
                header = "\n\nVIETNAMESE CROP DISEASE KNOWLEDGE BASE REFERENCE:\n"
            sections.append(header + "\n".join(lines))
    except Exception:
        pass

    # Active learning loop: inject expert-reviewed corrections from DiagnosisFeedback
    try:
        fb_rows = (
            db.query(DiagnosisFeedback)
            .filter(DiagnosisFeedback.is_correct.is_(False))
            .order_by(DiagnosisFeedback.reviewed.desc(), DiagnosisFeedback.id.desc())
            .limit(15)
            .all()
        )
        fb_lines = []
        for fb in fb_rows:
            if not (fb.reviewed or fb.correct_disease or fb.expert_note):
                continue
            wrong = fb.predicted_name or fb.predicted_label or "Chẩn đoán cũ"
            right_parts = [p for p in (fb.correct_plant, fb.correct_disease) if p]
            right = " - ".join(right_parts) if right_parts else ""
            note = (fb.expert_note or fb.comment or "").strip()[:180]
            if right or note:
                detail = f"Thực tế là: {right}." if right else ""
                if note:
                    detail += f" Ghi chú chuyên gia: {note}"
                fb_lines.append(f"- Tránh nhầm '{wrong}' -> {detail}".strip())
        if fb_lines:
            fb_header = (
                "\n\nLƯU Ý TỪ CÁC CA CHẨN ĐOÁN SAI ĐÃ ĐƯỢC CHUYÊN GIA HIỆU CHỈNH:\n"
                if lang == "vi"
                else "\n\nEXPERT CORRECTIONS FROM PAST MISDIAGNOSES:\n"
            )
            sections.append(fb_header + "\n".join(fb_lines[:10]))
    except Exception:
        pass

    return "".join(sections)


def _call_vlm_once(
    b64_list: list[str],
    lang: str,
    temperature: float = 0,
    seed: int = 42,
    db = None,
    plant_hint: Optional[str] = None
) -> Optional[dict]:
    """Make a single VLM API call with 1 or more images and optional plant hint."""
    cfg = resolve_llm_config(db)  # raises LLMConfigError if not configured (caught by callers)
    provider = cfg["provider"]
    api_url = cfg["api_url"]
    api_key = cfg["api_key"]
    model_name = cfg["model_name"]

    prompt = (SYSTEM_PROMPT_VI if lang == "vi" else SYSTEM_PROMPT) + _load_db_disease_context(db, plant_hint, lang)

    # Multi-scale smart crop: when only 1 photo is uploaded, automatically attach a high-res
    # 1:1 crop of the highest-saliency lesion region so ANY model sees fine lesion details.
    auto_roi_b64 = _auto_lesion_crop_b64(b64_list[0]) if len(b64_list) == 1 else None

    if provider in ("cliproxy", "openai"):
        user_content = []
        if len(b64_list) == 1:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_list[0]}"}})
            if auto_roi_b64:
                roi_label = (
                    "[Ảnh 1b - Tự động phóng đại cận cảnh vùng nghi có vết bệnh từ Ảnh 1 để soi chi tiết viền, quầng vàng, bào tử nấm/sâu hại]:"
                    if lang == "vi"
                    else "[Image 1b - Automatic high-resolution zoom crop of the suspected lesion region from Image 1]:"
                )
                user_content.append({"type": "text", "text": roi_label})
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{auto_roi_b64}"}})
            instruction = (
                "Phân tích kỹ hình thái lá/cây và đặc điểm vi mô của vết bệnh trong ảnh này theo đúng 4 bước. Trả về JSON."
                if lang == "vi"
                else "Carefully analyze the plant morphology and lesion traits in this image following the 4 steps. Respond with JSON."
            )
            if plant_hint:
                instruction += f" [LƯU Ý BẮT BUỘC: Người dùng xác nhận đây là cây {plant_hint}. Hãy đối chiếu kỹ các bệnh và sâu hại trên cây {plant_hint}]."
            user_content.append({"type": "text", "text": instruction})
        else:
            labels_vi = ["Ảnh 1 (Cận cảnh vết bệnh)", "Ảnh 2 (Toàn cảnh cành lá/toàn cây)", "Ảnh 3 (Bộ phận khác)"]
            labels_en = ["Image 1 (Close-up of lesion)", "Image 2 (Overview of plant/branch)", "Image 3 (Other view)"]
            for idx, b64 in enumerate(b64_list):
                labels = labels_vi if lang == "vi" else labels_en
                if idx < len(labels):
                    lbl = labels[idx]
                else:
                    lbl = f"Ảnh {idx + 1}" if lang == "vi" else f"Image {idx + 1}"
                user_content.append({"type": "text", "text": f"[{lbl}]:"})
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

            instruction = (
                "Phân tích kết hợp các ảnh trên (Ảnh 1 cận cảnh vết bệnh + Ảnh 2 tổng thể cành lá/cây) để chẩn đoán chính xác loại cây và bệnh. Trả về JSON."
                if lang == "vi"
                else "Analyze and synthesize the images above (Image 1 close-up + Image 2 plant overview) to accurately identify the plant and disease. Respond with JSON."
            )
            if plant_hint:
                instruction += f" [LƯU Ý BẮT BUỘC: Người dùng xác nhận đây là cây {plant_hint}. Hãy đối chiếu kỹ các bệnh và sâu hại trên cây {plant_hint}]."
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        parts = []
        for b64 in b64_list:
            parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
        if auto_roi_b64:
            parts.append({"inlineData": {"mimeType": "image/jpeg", "data": auto_roi_b64}})

        instruction = "Phân tích bệnh cây trong các ảnh này. Trả về JSON." if lang == "vi" else "Identify the plant disease in these images. Respond with JSON."
        if plant_hint:
            instruction += f" Người dùng chỉ định đây là cây: {plant_hint}."
        parts.append({"text": instruction})

        payload = {
            "contents": [{"parts": parts}],
            "systemInstruction": {"parts": [{"text": prompt}]},
            "generationConfig": {"responseMimeType": "application/json", "temperature": temperature},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return _extract_json(content)


def _majority_vote(results: list[dict]) -> dict:
    """Pick the most common normalized (plant, disease) pair and merge best fields."""
    def _key(r: dict) -> tuple[str, str]:
        return (
            _normalize_vote_key(str(r.get("plant") or "")),
            _normalize_vote_key(str(r.get("disease") or "")),
        )

    combos = [_key(r) for r in results]
    most_common = Counter(combos).most_common(1)[0][0]

    winners = [r for r in results if _key(r) == most_common]

    def _safe_conf(r):
        try:
            return int(float(str(r.get("confidence", 0)).replace('%', '').strip()))
        except Exception:
            return 0

    best = dict(max(winners, key=_safe_conf))
    avg_conf = round(sum(_safe_conf(r) for r in winners) / len(winners))
    best["confidence"] = avg_conf
    if best.get("disease"):
        best["disease"] = _clean_disease_label(str(best["disease"]))
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
    disease_str = _clean_disease_label(str(result.get("disease") or "Unknown"))
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


def _get_image_hashes(images: list[Image.Image]) -> list[imagehash.ImageHash]:
    """Compute a perceptual hash for every image (order matters: close-up first, overview second)."""
    return [imagehash.phash(img.convert("RGB").resize((224, 224))) for img in images]


def _current_model_tag(db=None) -> str:
    """Return 'provider:model_name' for cache partitioning without requiring an API key in unit tests."""
    provider = ""
    model = ""
    if db is not None:
        try:
            p_row = db.query(Setting).filter(Setting.key == "llm_provider").first()
            m_row = db.query(Setting).filter(Setting.key == "llm_model_name").first()
            provider = (p_row.value or "").strip() if p_row else ""
            model = (m_row.value or "").strip() if m_row else ""
        except Exception:
            pass
    provider = (provider or os.getenv("LLM_PROVIDER") or "cliproxy").strip().lower()
    model = (model or os.getenv("LLM_MODEL_NAME") or "gemini-3.8-flash-high").strip()
    return f"{provider}:{model}"


def _make_cache_key(
    hashes: list[imagehash.ImageHash],
    lang: str,
    plant_hint: Optional[str],
    model_tag: str = "",
) -> str:
    parts = [",".join(str(h) for h in hashes), lang, plant_hint or ""]
    if model_tag:
        parts.append(model_tag)
    return "|".join(parts)


def _find_cached(
    hashes: list[imagehash.ImageHash],
    lang: str,
    plant_hint: Optional[str],
    model_tag: str = "",
) -> Optional[dict]:
    """Find a cached prediction for the same or near-identical image set (same lang + plant hint + model)."""
    key = _make_cache_key(hashes, lang, plant_hint, model_tag)
    entry = _prediction_cache.get(key)
    if entry is not None:
        logger.info("Cache exact hit: key=%s", key)
        return entry["result"]

    # Near-match: every image in the set must be within the tight Hamming distance threshold
    for stored_key, stored in list(_prediction_cache.items()):
        if stored["lang"] != lang or stored["plant_hint"] != (plant_hint or ""):
            continue
        if stored.get("model_tag", "") != (model_tag or ""):
            continue
        stored_hashes = stored["hashes"]
        if len(stored_hashes) != len(hashes):
            continue
        distances = [h - s for h, s in zip(hashes, stored_hashes)]
        if all(d < HASH_SIMILARITY_THRESHOLD for d in distances):
            logger.info("Cache near hit: key=%s, distances=%s", stored_key, distances)
            return stored["result"]
    return None


def _store_cache(
    hashes: list[imagehash.ImageHash],
    lang: str,
    plant_hint: Optional[str],
    result: dict,
    model_tag: str = "",
):
    """Store prediction result in cache together with the data needed for near-match lookup."""
    key = _make_cache_key(hashes, lang, plant_hint, model_tag)
    _prediction_cache[key] = {
        "hashes": hashes,
        "lang": lang,
        "plant_hint": plant_hint or "",
        "model_tag": model_tag or "",
        "result": result,
    }
    logger.info("Cached prediction: key=%s, entries=%d/%d", key, len(_prediction_cache), _prediction_cache.maxsize)


def predict_vlm(
    images: Union[Image.Image, List[Image.Image]],
    lang: str = "vi",
    db = None,
    plant_hint: Optional[str] = None
) -> Optional[dict]:
    """Use VLM vision to identify plant disease with multi-image support, hint filtering, and interactive clarification."""
    if isinstance(images, (list, tuple)):
        img_list = list(images)
    else:
        img_list = [images]

    if not img_list:
        return None

    model_tag = _current_model_tag(db)

    # Step 1: Check pHash cache (exact or near-identical image set for the active model)
    img_hashes = _get_image_hashes(img_list)
    cached = _find_cached(img_hashes, lang, plant_hint, model_tag=model_tag)
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

        raw_disease = str(result.get("disease") or "").strip()
        raw_plant = str(result.get("plant") or "").strip()

        # If model used tentative phrasing ("Nghi...", "Suspected...") or hallucinated a temperate tree,
        # cap its inflated confidence so clarification / voting can intervene.
        has_tentative_word = bool(re.search(r"^(?:nghi\b|nghi\s+ngờ|có\s+thể|suspected|possibly)", raw_disease, flags=re.IGNORECASE))
        temperate_fp = _is_temperate_hallucination(raw_plant, raw_disease)
        if temperate_fp:
            confidence = min(confidence, 60)
            result["confidence"] = confidence
        elif has_tentative_word and confidence >= VOTING_CONFIDENCE_THRESHOLD:
            confidence = 72
            result["confidence"] = confidence

        # Step 3: Interactive Clarification Trigger
        # If user did NOT specify plant, provided only 1 image, and confidence is low or multiple plant candidates exist:
        candidates = result.get("plant_candidates", [])
        if not isinstance(candidates, list):
            candidates = []
        warnings = [str(w).lower() for w in (result.get("image_quality_warnings") or [])]
        is_closeup_or_ambiguous = any(
            kw in w
            for w in warnings
            for kw in ("single detached leaf", "close-up", "cận cảnh", "chưa rõ", "thiếu", "một lá", "lá rời", "khó xác định")
        )

        should_clarify = (
            plant_hint is None
            and len(img_list) == 1
            and (
                confidence < 70
                or temperate_fp
                or (len(candidates) >= 2 and confidence < 82 and is_closeup_or_ambiguous)
                or (len(candidates) >= 3 and confidence < 85)
            )
        )

        if should_clarify:
            session_token = uuid.uuid4().hex
            _clarification_sessions[session_token] = {
                "b64_list": b64_list,
                "img_hashes": img_hashes,
                "initial_result": result,
                "lang": lang,
            }
            cand_plants = _build_candidate_plants(candidates)
            logger.info(
                "VLM needs clarification: preliminary=%s - %s (confidence=%d%%, candidates=%s, model=%s)",
                raw_plant, raw_disease, confidence, [c["name"] for c in cand_plants], model_tag,
            )
            msg = (
                "Ảnh chụp rất cận cảnh vết bệnh nên chưa thấy rõ hình thái cành lá. Để chẩn đoán chính xác hơn, bạn đang trồng loại cây nào dưới đây?"
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
            logger.info("VLM prediction [%s]: %s - %s (confidence=%d%%, no voting needed)",
                        model_tag, raw_plant, raw_disease, confidence)
            formatted = _format_result(result, lang, voting_used=False, status="success")
            _store_cache(img_hashes, lang, plant_hint, formatted, model_tag=model_tag)
            return formatted

        # Step 5: Low confidence → self-consistency voting
        logger.info("VLM [%s] confidence=%d%% < %d%%, triggering voting (%d rounds total)",
                     model_tag, confidence, VOTING_CONFIDENCE_THRESHOLD, VOTING_ROUNDS)
        all_results = [result]

        for i in range(1, VOTING_ROUNDS):
            try:
                extra = _call_vlm_once(b64_list, lang, temperature=0.3, seed=42 + i * 17, db=db, plant_hint=plant_hint)
                if extra and isinstance(extra, dict):
                    all_results.append(extra)
                    logger.info("Voting round %d: %s - %s (confidence=%s)",
                                i + 1, extra.get("plant"), extra.get("disease"), extra.get("confidence", 0))
            except Exception as e:
                logger.warning("Voting round %d failed: %s", i + 1, e)

        if len(all_results) > 1:
            final = _majority_vote(all_results)
            if "image_quality_warnings" not in final or not final["image_quality_warnings"]:
                for r in all_results:
                    if r.get("image_quality_warnings"):
                        final["image_quality_warnings"] = r["image_quality_warnings"]
                        break
            logger.info("Voting result [%s]: %s - %s (averaged confidence=%s)",
                        model_tag, final.get("plant"), final.get("disease"), final.get("confidence", 0))
            formatted = _format_result(final, lang, voting_used=True, status="success")
        else:
            formatted = _format_result(result, lang, voting_used=False, status="success")

        _store_cache(img_hashes, lang, plant_hint, formatted, model_tag=model_tag)
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
    img_hashes = session.get("img_hashes")
    initial_res = session["initial_result"]
    model_tag = _current_model_tag(db)

    def _fallback() -> dict:
        # Re-analysis failed: return the first-pass result with the user's plant, but do NOT inflate
        # the confidence — the disease itself was never re-checked against the confirmed crop.
        fb = dict(initial_res)
        fb["plant"] = selected_plant
        note = (
            "Không thể phân tích lại theo cây trồng bạn chọn; kết quả dưới đây là chẩn đoán sơ bộ ban đầu."
            if lang == "vi"
            else "Could not re-analyse with the selected crop; this is the preliminary first-pass diagnosis."
        )
        fb["image_quality_warnings"] = list(fb.get("image_quality_warnings") or []) + [note]
        return fb

    used_fallback = False
    try:
        result = _call_vlm_once(b64_list, lang, temperature=0, seed=42, db=db, plant_hint=selected_plant)
        if not result or not isinstance(result, dict):
            result = _fallback()
            used_fallback = True
        else:
            logger.info("VLM clarified [%s] (plant=%s): %s (confidence=%s)",
                        model_tag, selected_plant, result.get("disease"), result.get("confidence", 0))
    except Exception as e:
        logger.error("Clarify VLM call failed: %s, falling back to initial with plant override", e)
        result = _fallback()
        used_fallback = True

    formatted = _format_result(result, lang, voting_used=False, status="success")
    if img_hashes and not used_fallback:
        _store_cache(img_hashes, lang, selected_plant, formatted, model_tag=model_tag)
    # Invalidate session
    _clarification_sessions.pop(session_token, None)
    return formatted
