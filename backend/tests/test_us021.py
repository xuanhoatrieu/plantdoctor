"""US-021 backend checks — run with:  cd backend && venv/bin/python tests/test_us021.py

No pytest needed. Uses a throw-away SQLite DB and monkeypatches the VLM network call,
so it never spends AI credits and never touches the real database.
"""
import io
import os
import sys
import tempfile
import time
import random

_tmpdir = tempfile.mkdtemp(prefix="us021_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-us021-only")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime as dt  # noqa: E402
import jwt  # noqa: E402
from PIL import Image, ImageEnhance, ImageFilter  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import auth  # noqa: E402
from app.database import models as dbm  # noqa: E402
from app.models import vlm  # noqa: E402
from app.routers import feedback as fb_router  # noqa: E402
from app.main import app  # noqa: E402

PASSED = 0
FAILED = []


def check(name, cond, detail=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


# ---------------------------------------------------------------- image helpers
def textured(w=800, h=600, seed=1, scale=1.0, offset=0):
    """Synthetic 'leaf-like' textured image: random blocks + noise = plenty of edges (sharp)."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), (60, 140, 60))
    px = img.load()
    for y in range(h):
        for x in range(w):
            g = 100 + ((x // 8 + y // 8) % 2) * 80 + rnd.randint(-25, 25)
            v = int(max(0, min(255, g * scale + offset)))
            px[x, y] = (v // 3, v, v // 3)
    return img


def to_bytes(img, fmt="JPEG"):
    buf = io.BytesIO()
    img.save(buf, fmt, quality=92)
    return buf.getvalue()


def leaf_scene(seed=1, w=900, h=700):
    """Smooth, photo-like scene (gradient + leaf-shaped ellipses + spots) for perceptual-hash tests."""
    from PIL import ImageDraw
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=(30 + y * 60 // h, 70 + y * 50 // h, 30))
    for _ in range(6):
        cx, cy = rnd.randint(100, w - 100), rnd.randint(100, h - 100)
        rw, rh = rnd.randint(120, 260), rnd.randint(50, 110)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(40, rnd.randint(120, 190), 50))
        for _ in range(5):
            sx, sy = cx + rnd.randint(-rw // 2, rw // 2), cy + rnd.randint(-rh // 2, rh // 2)
            d.ellipse([sx - 12, sy - 12, sx + 12, sy + 12], fill=(120, 90, 40))
    return img.filter(ImageFilter.GaussianBlur(1))


SHARP = textured()
SMALL = textured(200, 180, seed=2)
DARK = textured(seed=3, scale=0.15)
BRIGHT = Image.new("RGB", (800, 600), (250, 252, 250))
BLURRY = SHARP.filter(ImageFilter.GaussianBlur(10))
OTHER = textured(seed=99).transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
SCENE = leaf_scene(1)
# Same photo re-sent: slightly brighter, re-compressed, downscaled 90%
SCENE_DUP = ImageEnhance.Brightness(SCENE).enhance(1.04).resize((810, 630))
SCENE_OTHER = leaf_scene(7)

# ---------------------------------------------------------------- fake VLM
CALLS = []
NEXT = {"result": None, "raise": False}


def fake_call(b64_list, lang, temperature=0, seed=42, db=None, plant_hint=None):
    CALLS.append({"n": len(b64_list), "hint": plant_hint, "temp": temperature})
    if NEXT["raise"]:
        raise RuntimeError("simulated upstream failure")
    return dict(NEXT["result"])


GOOD_RESULT = {
    "plant": "Cam", "disease": "Loét cam", "confidence": 90, "description": "Vết loét sần",
    "treatment": "Cắt bỏ lá bệnh", "medicines": [], "severity": "trung bình",
    "plant_candidates": [], "image_quality_warnings": [],
}
LOW_RESULT = dict(GOOD_RESULT, confidence=60, plant_candidates=["Cam", "Bưởi", "Chanh"])

vlm._call_vlm_once = fake_call


def reset_vlm(result=GOOD_RESULT, raise_=False):
    CALLS.clear()
    NEXT["result"] = result
    NEXT["raise"] = raise_
    vlm._prediction_cache.clear()
    vlm._clarification_sessions.clear()


# ================================================================ 1. quality function
print("\n[1] assess_image_quality")
q = vlm.assess_image_quality(SHARP)
check("sharp textured image has no issues", q["issues"] == [], q)
q = vlm.assess_image_quality(SMALL)
check("200x180 -> low_resolution", "low_resolution" in q["issues"], q)
check("low_resolution message has size", "200x180" in q["messages"][0], q["messages"])
q = vlm.assess_image_quality(DARK)
check("dark -> too_dark (and blur not judged)", q["issues"] == ["too_dark"], q)
q = vlm.assess_image_quality(BRIGHT)
check("near-white -> overexposed", q["issues"] == ["overexposed"], q)
q = vlm.assess_image_quality(BLURRY)
check("gaussian blur r10 -> blurry", q["issues"] == ["blurry"], q)
q_en = vlm.assess_image_quality(BLURRY, "en")
check("english message", q_en["messages"][0].startswith("Image is blurry"), q_en["messages"])
citrus = os.environ.get("US021_REAL_IMAGE")
if citrus and os.path.exists(citrus):
    real = Image.open(citrus).convert("RGB")
    q = vlm.assess_image_quality(real)
    check("real citrus photo passes", q["issues"] == [], q)
    q = vlm.assess_image_quality(real.filter(ImageFilter.GaussianBlur(8)))
    check("real citrus photo blurred r8 -> blurry", "blurry" in q["issues"], q)

# ================================================================ 2. predict endpoint
client = TestClient(app)
client.__enter__()  # run lifespan -> init_db on the temp SQLite DB

print("\n[2] /predict quality gate + backward compatibility")
reset_vlm()
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SMALL), "image/jpeg")}, data={"lang": "vi"})
check("old client (single 'file', no gate) still gets a diagnosis", r.status_code == 200 and r.json()["status"] == "success", r.text[:200])
check("old client: VLM was called", len(CALLS) == 1)

reset_vlm()
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SMALL), "image/jpeg")}, data={"quality_gate": "true"})
j = r.json()
check("gate on + small image -> low_quality", r.status_code == 200 and j["status"] == "low_quality", r.text[:200])
check("low_quality has issue codes", j.get("quality_issues") == ["low_resolution"], j.get("quality_issues"))
check("low_quality has empty predictions", j["predictions"] == [])
check("low_quality did NOT call the VLM (no cost)", len(CALLS) == 0, CALLS)

reset_vlm()
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(BLURRY), "image/jpeg")}, data={"quality_gate": "true"})
check("gate on + blurry -> low_quality/blurry", r.json().get("quality_issues") == ["blurry"], r.text[:200])
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(BLURRY), "image/jpeg")}, data={"quality_gate": "false"})
check("override (gate off) diagnoses the same blurry photo", r.json()["status"] == "success" and len(CALLS) == 1, r.text[:200])

reset_vlm()
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SHARP), "image/jpeg")}, data={"quality_gate": "true"})
check("gate on + good image -> success", r.json()["status"] == "success" and len(CALLS) == 1, r.text[:200])

print("\n[3] multiple images")
reset_vlm()
r = client.post(
    "/api/v1/predict",
    files=[("files", ("1.jpg", to_bytes(SHARP), "image/jpeg")), ("files", ("2.jpg", to_bytes(DARK), "image/jpeg"))],
    data={"quality_gate": "true"},
)
j = r.json()
check("2 images, 2nd dark -> low_quality", j["status"] == "low_quality" and j["quality_issues"] == ["too_dark"], r.text[:200])
check("message says which image", any(m.startswith("Ảnh 2:") for m in j["image_quality_warnings"]), j["image_quality_warnings"])
reset_vlm()
r = client.post(
    "/api/v1/predict",
    files=[("files", ("1.jpg", to_bytes(SHARP), "image/jpeg")), ("files", ("2.jpg", to_bytes(OTHER), "image/jpeg"))],
    data={"quality_gate": "true"},
)
check("2 good images -> one VLM call with 2 images", r.json()["status"] == "success" and CALLS and CALLS[0]["n"] == 2, CALLS)
r = client.post("/api/v1/predict", files={"file": ("x.txt", b"not an image", "text/plain")})
check("invalid file -> 400", r.status_code == 400)

print("\n[4] near-duplicate cache")
reset_vlm()
client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SCENE), "image/jpeg")})
r = client.post("/api/v1/predict", files={"file": ("b.jpg", to_bytes(SCENE_DUP), "image/jpeg")})
check("re-sent photo (brighter, resized) -> cached, no 2nd VLM call", r.json().get("cached") is True and len(CALLS) == 1, (r.json().get("cached"), CALLS))
r = client.post("/api/v1/predict", files={"file": ("c.jpg", to_bytes(SCENE_OTHER), "image/jpeg")})
check("different image -> not cached", r.json().get("cached") is False and len(CALLS) == 2, (r.json().get("cached"), CALLS))
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SCENE), "image/jpeg")}, data={"plant_hint": "Bưởi"})
check("same image but different plant hint -> not cached", r.json().get("cached") is False and len(CALLS) == 3)
r = client.post(
    "/api/v1/predict",
    files=[("files", ("1.jpg", to_bytes(SCENE), "image/jpeg")), ("files", ("2.jpg", to_bytes(SCENE_OTHER), "image/jpeg"))],
)
check("2-image set with same first image -> not cached", r.json().get("cached") is False and len(CALLS) == 4)

print("\n[5] clarification flow")
reset_vlm(LOW_RESULT)
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SHARP), "image/jpeg")})
j = r.json()
check("low confidence single image -> needs_clarification", j["status"] == "needs_clarification", r.text[:300])
names = [c["name"] for c in j["candidate_plants"]]
check("candidates returned (+ 'other' escape option)", names[:3] == ["Cam", "Bưởi", "Chanh"] and len(names) == 4, j["candidate_plants"])
check("no '100%' promise in message", "100%" not in (j.get("clarification_message") or ""))
token = j["session_token"]
NEXT["result"] = dict(GOOD_RESULT, plant="Bưởi", confidence=88)
r = client.post("/api/v1/predict/clarify", json={"session_token": token, "selected_plant": "Bưởi", "lang": "vi"})
check("clarify -> success", r.status_code == 200 and r.json()["status"] == "success", r.text[:200])
check("clarify re-ran VLM with chosen plant", CALLS[-1]["hint"] == "Bưởi", CALLS)
r = client.post("/api/v1/predict/clarify", json={"session_token": token, "selected_plant": "Bưởi"})
check("session is single-use -> 404", r.status_code == 404)
r = client.post("/api/v1/predict/clarify", json={"session_token": "x", "selected_plant": "Bưởi"})
check("too-short token -> 422", r.status_code == 422)
r = client.post("/api/v1/predict/clarify", json={"session_token": "a" * 32, "selected_plant": "B" * 101})
check("too-long plant -> 422", r.status_code == 422)

reset_vlm(LOW_RESULT)
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SHARP), "image/jpeg")})
token = r.json()["session_token"]
NEXT["raise"] = True
r = client.post("/api/v1/predict/clarify", json={"session_token": token, "selected_plant": "Bưởi"})
j = r.json()
check("clarify fallback keeps original confidence (no inflation)", j["predictions"][0]["confidence"] == 60, j["predictions"][0]["confidence"])
check("clarify fallback warns it is preliminary", any("sơ bộ" in w for w in j["image_quality_warnings"]), j["image_quality_warnings"])

reset_vlm(LOW_RESULT)
r = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SHARP), "image/jpeg")}, data={"plant_hint": "Cam"})
check("plant hint given -> no clarification", r.json()["status"] == "success", r.text[:200])

# ================================================================ 3. feedback
print("\n[6] feedback API")
db = dbm.SessionLocal()
normal = dbm.User(phone="0911222333", name="Nông dân A", role="user", password_hash="x")
admin = dbm.User(phone="0999888777", name="Chuyên gia", role="admin", password_hash="x")
db.add_all([normal, admin])
db.commit()
db.refresh(normal)
db.refresh(admin)
user_tok = auth.create_token(normal.id, "user")
admin_tok = auth.create_token(admin.id, "admin")
expired_tok = jwt.encode(
    {"user_id": normal.id, "role": "user", "exp": dt.datetime.utcnow() - dt.timedelta(days=1)},
    auth.SECRET_KEY, algorithm="HS256",
)
fb_router._rate_counter.clear()

base = {"is_correct": True, "platform": "web", "predicted_name": "Cam - Loét cam", "predicted_label": "Loét cam", "predicted_confidence": 87.5}
r = client.post("/api/v1/feedback", json=base)
check("guest thumbs-up -> 200", r.status_code == 200 and r.json()["ok"], r.text)
bad = dict(base, is_correct=False, reason="hack'; DROP TABLE")
check("unknown reason -> 422", client.post("/api/v1/feedback", json=bad).status_code == 422)
check("comment > 1000 chars -> 422", client.post("/api/v1/feedback", json=dict(base, comment="x" * 1001)).status_code == 422)
check("confidence > 100 -> 422", client.post("/api/v1/feedback", json=dict(base, predicted_confidence=150)).status_code == 422)
check("bad platform -> 422", client.post("/api/v1/feedback", json=dict(base, platform="windows")).status_code == 422)
neg = dict(base, is_correct=False, reason="wrong_disease", correct_disease="Ghẻ cam", comment="Vết sần nhỏ hơn", platform="android")
r = client.post("/api/v1/feedback", json=neg, headers={"Authorization": f"Bearer {expired_tok}"})
check("expired token -> still accepted as guest", r.status_code == 200, r.text)
r = client.post("/api/v1/feedback", json=dict(neg, platform="ios"), headers={"Authorization": f"Bearer {user_tok}"})
check("logged-in user feedback -> 200", r.status_code == 200, r.text)
row = db.query(dbm.DiagnosisFeedback).filter(dbm.DiagnosisFeedback.id == r.json()["id"]).first()
check("feedback linked to user", row.user_id == normal.id)
pos_row = db.query(dbm.DiagnosisFeedback).order_by(dbm.DiagnosisFeedback.id).first()
check("confidence stored as rounded int", pos_row.predicted_confidence == 88, pos_row.predicted_confidence)
exp_row = db.query(dbm.DiagnosisFeedback).filter(dbm.DiagnosisFeedback.platform == "android").first()
check("expired-token row stored without user", exp_row.user_id is None)
r = client.post("/api/v1/feedback", json=dict(base, reason="wrong_plant", correct_plant="Bưởi"))
row = db.query(dbm.DiagnosisFeedback).filter(dbm.DiagnosisFeedback.id == r.json()["id"]).first()
check("thumbs-up drops correction fields", row.reason == "" and row.correct_plant == "")

fb_router._rate_counter.clear()
hdr = {"X-Forwarded-For": "203.0.113.7"}
codes = [client.post("/api/v1/feedback", json=base, headers=hdr).status_code for _ in range(fb_router.FEEDBACK_RATE_LIMIT)]
check("first 20 from one IP -> 200", all(c == 200 for c in codes), codes)
check("21st from same IP -> 429", client.post("/api/v1/feedback", json=base, headers=hdr).status_code == 429)
check("other IP unaffected", client.post("/api/v1/feedback", json=base, headers={"X-Forwarded-For": "203.0.113.8"}).status_code == 200)
check("spoofed left-most XFF does not bypass", client.post("/api/v1/feedback", json=base, headers={"X-Forwarded-For": "1.2.3.4, 203.0.113.7"}).status_code == 429)
fb_router._rate_counter.clear()

print("\n[7] admin feedback API")
check("no token -> 401", client.get("/api/v1/admin/feedback").status_code == 401)
check("normal user -> 403", client.get("/api/v1/admin/feedback", headers={"Authorization": f"Bearer {user_tok}"}).status_code == 403)
check("normal user stats -> 403", client.get("/api/v1/admin/feedback/stats", headers={"Authorization": f"Bearer {user_tok}"}).status_code == 403)
check("normal user review -> 403", client.put("/api/v1/admin/feedback/1", json={"reviewed": True}, headers={"Authorization": f"Bearer {user_tok}"}).status_code == 403)
AH = {"Authorization": f"Bearer {admin_tok}"}
r = client.get("/api/v1/admin/feedback", params={"verdict": "incorrect"}, headers=AH)
j = r.json()
check("admin list incorrect -> 2 rows", r.status_code == 200 and j["total"] == 2, r.text[:300])
users = [it["user"] for it in j["items"] if it["user"]]
check("phone is masked", users and users[0]["phone"] == "09******33", users)
check("no password hash leaked", "password" not in r.text)
r = client.get("/api/v1/admin/feedback", params={"page_size": 5, "page": 2}, headers=AH)
check("pagination works", r.status_code == 200 and len(r.json()["items"]) == 5, r.text[:200])
check("page_size > 100 -> 422", client.get("/api/v1/admin/feedback", params={"page_size": 101}, headers=AH).status_code == 422)
check("bad verdict -> 422", client.get("/api/v1/admin/feedback", params={"verdict": "x"}, headers=AH).status_code == 422)
s = client.get("/api/v1/admin/feedback/stats", headers=AH).json()
check("stats totals consistent", s["total"] == s["correct"] + s["incorrect"] and s["incorrect"] == 2, s)
check("stats by_reason", s["by_reason"].get("wrong_disease") == 2, s["by_reason"])
check("stats unreviewed_incorrect = 2", s["unreviewed_incorrect"] == 2, s)
target = client.get("/api/v1/admin/feedback", params={"verdict": "incorrect"}, headers=AH).json()["items"][0]["id"]
r = client.put(f"/api/v1/admin/feedback/{target}", json={"reviewed": True, "expert_note": "Đúng là ghẻ cam"}, headers=AH)
check("review -> reviewed + note", r.status_code == 200 and r.json()["reviewed"] and r.json()["expert_note"] == "Đúng là ghẻ cam", r.text[:200])
s = client.get("/api/v1/admin/feedback/stats", headers=AH).json()
check("unreviewed_incorrect drops to 1", s["unreviewed_incorrect"] == 1, s)
r = client.get("/api/v1/admin/feedback", params={"reviewed": "yes"}, headers=AH)
check("filter reviewed=yes -> 1", r.json()["total"] == 1)
check("review missing id -> 404", client.put("/api/v1/admin/feedback/99999", json={"reviewed": True}, headers=AH).status_code == 404)
check("expert note > 2000 -> 422", client.put(f"/api/v1/admin/feedback/{target}", json={"expert_note": "x" * 2001}, headers=AH).status_code == 422)

print("\n[8] US-025 cache isolation, majority vote normalization & hallucination guard")
check("clean_disease_label strips 'Nghi ' prefix", vlm._clean_disease_label("Nghi nhện đỏ hại chè") == "Nhện đỏ hại chè")
check("clean_disease_label strips ', nghi ngờ cao' suffix", vlm._clean_disease_label("Bệnh phồng lá chè, nghi ngờ cao") == "Bệnh phồng lá chè")

voted = vlm._majority_vote([
    {"plant": "Cây chè", "disease": "Nghi bệnh phồng lá chè", "confidence": 75},
    {"plant": "Chè (Camellia sinensis)", "disease": "Bệnh phồng lá chè do nấm Exobasidium vexans", "confidence": 85},
    {"plant": "Cây chè", "disease": "Bệnh thối búp chè", "confidence": 65},
])
check("majority vote merges normalized disease variants", voted["disease"].startswith("Bệnh phồng lá chè") and voted["confidence"] == 80, voted)

reset_vlm(GOOD_RESULT)
r1 = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SCENE), "image/jpeg")})
check("initial predict calls VLM once", r1.json().get("cached") is False and len(CALLS) == 1)
r2 = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SCENE), "image/jpeg")})
check("second predict with same model hits cache", r2.json().get("cached") is True and len(CALLS) == 1)

r_set = client.put("/api/v1/admin/settings", json={"llm_model_name": "gemini-2.5-pro"}, headers=AH)
check("admin settings update succeeds", r_set.status_code == 200, r_set.text)
r3 = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SCENE), "image/jpeg")})
check("after model change, cache is invalidated and VLM is called again", r3.json().get("cached") is False and len(CALLS) == 2, (r3.json().get("cached"), CALLS))

reset_vlm({
    "plant": "Cây óc chó (Juglans regia)",
    "disease": "Bệnh đốm lá vi khuẩn",
    "confidence": 82,
    "description": "Đốm nâu trên lá",
    "treatment": "Phun thuốc gốc đồng",
    "medicines": [],
    "severity": "trung bình",
    "plant_candidates": [],
    "image_quality_warnings": [],
})
r_walnut = client.post("/api/v1/predict", files={"file": ("a.jpg", to_bytes(SHARP), "image/jpeg")})
j_walnut = r_walnut.json()
check("temperate tree hallucination (óc chó) triggers clarification instead of false high-confidence result", j_walnut["status"] == "needs_clarification", j_walnut)

print("\n[9] US-026 lesion ROI auto-crop, Vietnamese knowledge base RAG & expert feedback grounding")
roi = vlm._extract_lesion_crop(SCENE)
check("lesion ROI auto-crop extracts square high-res patch from 900x700 scene", roi is not None and roi.size[0] == roi.size[1] and roi.size[0] >= 256, getattr(roi, "size", None))
check("small image (<480px) skips ROI crop", vlm._extract_lesion_crop(SMALL) is None)

r_kb = client.get("/api/v1/diseases")
check("public /api/v1/diseases returns seeded Vietnamese disease knowledge base (>=30 entries)", r_kb.status_code == 200 and len(r_kb.json()) >= 30, len(r_kb.json()))
r_tea = client.get("/api/v1/diseases", params={"crop": "Chè"})
check("filtering /api/v1/diseases?crop=Chè returns tea diseases", r_tea.status_code == 200 and len(r_tea.json()) >= 5, len(r_tea.json()))

ctx_tea = vlm._load_db_disease_context(db, plant_hint="Chè", lang="vi")
check("RAG context for 'Chè' includes Exobasidium vexans & Pestalotiopsis theae", "Exobasidium vexans" in ctx_tea and "Pestalotiopsis theae" in ctx_tea, ctx_tea[:200])
check("RAG context includes expert feedback corrections from DiagnosisFeedback", "Đúng là ghẻ cam" in ctx_tea, ctx_tea[-300:])

r_seed = client.post("/api/v1/admin/diseases/seed?overwrite=true", headers=AH)
check("admin /diseases/seed endpoint succeeds", r_seed.status_code == 200 and r_seed.json().get("total", 0) >= 30, r_seed.text)

db.close()
client.__exit__(None, None, None)
print(f"\nRESULT: {PASSED} passed, {len(FAILED)} failed")
if FAILED:
    print("FAILED:", FAILED)
    sys.exit(1)
