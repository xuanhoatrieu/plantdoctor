"""Benchmark script checks — run with:  cd backend && venv/bin/python tests/test_benchmark.py

Verifies the honesty rules of scripts/eval_benchmark.py without calling the real AI.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="bench_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/t.db"
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from PIL import Image  # noqa: E402

import eval_benchmark as eb  # noqa: E402
from app.models import vlm  # noqa: E402

PASSED, FAILED = 0, []


def check(name, cond, detail=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


print("\n[1] helpers")
check("alias match", eb.match_text("Bệnh loét cam (Xanthomonas)", ["loét cam"]))
check("empty never matches", not eb.match_text("", ["cam"]))
check("active overlap VN/EN", eb.active_overlap(["Copper Hydroxide 77%"], ["Đồng Hydroxide"]))
check("active overlap exact", eb.active_overlap(["Tricyclazole"], ["Tricyclazole", "Isoprothiolane"]))
check("no overlap", not eb.active_overlap(["Mancozeb"], ["Tricyclazole"]))
lo, hi = eb.wilson(5, 5)
check("wilson 5/5 is not 100-100", hi == 100.0 and lo < 60, (lo, hi))

print("\n[2] dry-run is labelled and never written to docs/")
out = _tmp / "reports"
gt_real = BACKEND / "benchmark_data" / "ground_truth.json"
md = eb.run_benchmark(gt_real, out, dry_run=True, auto_clarify=True)
text = md.read_text(encoding="utf-8")
check("dry-run file name marked", "MO_PHONG" in md.name, md.name)
check("dry-run banner present", "MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THẬT" in text)
check("dry-run written to output dir, not docs/", md.parent == out)

print("\n[3] real mode with missing images skips (no simulation)")
calls = []
vlm._call_vlm_once = lambda *a, **k: calls.append(1) or {}
md = eb.run_benchmark(gt_real, out, dry_run=False, auto_clarify=True)
text = md.read_text(encoding="utf-8")
data = json.loads(md.with_suffix(".json").read_text(encoding="utf-8"))
check("no rows evaluated when images missing", data["rows"] == [], len(data["rows"]))
check("all cases listed as skipped", len(data["skipped"]) == 5, len(data["skipped"]))
check("report says nothing evaluated", "Chưa có ca nào được đánh giá" in text)
check("no AI call made", calls == [])
check("real report has no MÔ PHỎNG banner", "KHÔNG PHẢI KẾT QUẢ THẬT" not in text)

print("\n[4] real mode scoring with a fake AI")
samples = _tmp / "samples"
samples.mkdir()
import random  # noqa: E402
from PIL import ImageDraw  # noqa: E402

for i, name in enumerate(["a.jpg", "b.jpg", "c.jpg"]):
    rnd = random.Random(i * 31 + 7)
    im = Image.new("RGB", (640, 480), (40, 120, 50))
    d = ImageDraw.Draw(im)
    for _ in range(12):
        x, y = rnd.randint(0, 600), rnd.randint(0, 440)
        d.ellipse([x, y, x + rnd.randint(40, 200), y + rnd.randint(30, 150)], fill=(rnd.randint(0, 255), rnd.randint(60, 200), rnd.randint(0, 120)))
    im.save(samples / name)
gt = [
    {"id": "ok_case", "image_path": str(samples / "a.jpg"), "group": "leaf", "expected_plant": "Cam",
     "expected_plant_aliases": ["cam"], "expected_disease": "Loét cam", "expected_disease_aliases": ["loét cam"],
     "is_healthy": False, "recommended_actives": ["Đồng Hydroxide"]},
    {"id": "clarify_case", "image_path": str(samples / "b.jpg"), "group": "closeup", "expected_plant": "Bưởi",
     "expected_plant_aliases": ["bưởi"], "expected_disease": "Ghẻ", "expected_disease_aliases": ["ghẻ"],
     "is_healthy": False, "recommended_actives": ["Mancozeb"]},
    {"id": "banned_case", "image_paths": [str(samples / "c.jpg"), str(samples / "a.jpg")], "group": "leaf",
     "expected_plant": "Lúa", "expected_plant_aliases": ["lúa"], "expected_disease": "Đạo ôn",
     "expected_disease_aliases": ["đạo ôn"], "is_healthy": False, "recommended_actives": ["Tricyclazole"]},
    {"id": "missing_case", "image_path": "benchmark_data/samples/does_not_exist.jpg", "expected_plant": "Chè",
     "expected_disease": "x", "is_healthy": False},
]
gt_file = _tmp / "gt.json"
gt_file.write_text(json.dumps(gt, ensure_ascii=False), encoding="utf-8")

# Make case_image_paths accept absolute paths (BASE_DIR / abs == abs)
answers = {
    1: {"plant": "Cam", "disease": "Loét cam", "confidence": 90, "medicines": ["Copper Hydroxide"], "plant_candidates": []},
    "clarify_first": {"plant": "Cam", "disease": "Ghẻ", "confidence": 55, "medicines": ["Mancozeb"], "plant_candidates": ["Cam", "Bưởi"]},
    "clarify_second": {"plant": "Bưởi", "disease": "Ghẻ nhám", "confidence": 85, "medicines": ["Mancozeb"], "plant_candidates": []},
    "banned": {"plant": "Lúa", "disease": "Đạo ôn lá", "confidence": 92, "medicines": ["Tricyclazole", "Carbofuran"], "plant_candidates": []},
}
seq = []


def fake(b64_list, lang, temperature=0, seed=42, db=None, plant_hint=None):
    seq.append((len(b64_list), plant_hint))
    if len(b64_list) == 2:
        return dict(answers["banned"])
    if plant_hint == "Bưởi":
        return dict(answers["clarify_second"])
    if len(seq) == 1:
        return dict(answers[1])
    return dict(answers["clarify_first"])


vlm._call_vlm_once = fake
md = eb.run_benchmark(gt_file, out, dry_run=False, auto_clarify=True)
data = json.loads(md.with_suffix(".json").read_text(encoding="utf-8"))
rows = {r["case"]["id"]: r for r in data["rows"]}
check("3 evaluated, 1 skipped", len(rows) == 3 and len(data["skipped"]) == 1, (list(rows), data["skipped"]))
check("ok_case all correct", rows["ok_case"]["eval"]["plant_ok"] and rows["ok_case"]["eval"]["disease_ok"] and rows["ok_case"]["eval"]["rx_ok"])
cl = rows["clarify_case"]
check("clarification was asked and resolved with expected plant", cl["actual"]["asked_clarification"] and cl["actual"]["clarified"], cl["actual"])
check("clarified case scored on final answer", cl["eval"]["plant_ok"] and cl["eval"]["disease_ok"])
check("clarify re-ran AI with expected plant", (1, "Bưởi") in seq, seq)
bn = rows["banned_case"]
check("2-image case sent 2 images", (2, None) in seq, seq)
check("banned active detected -> rx fails", bn["eval"]["banned_free"] is False and bn["eval"]["rx_ok"] is False, bn["eval"])
text = md.read_text(encoding="utf-8")
check("small-sample warning shown", "Mẫu nhỏ" in text)
check("Wilson CI column present", "KTC 95%" in text)
check("no Top-3 claim", "Top-3" not in text and "top-3" not in text.lower())

print("\n[5] --no-clarify keeps the first-pass answer")
seq.clear()
vlm._prediction_cache.clear()
md = eb.run_benchmark(gt_file, out, dry_run=False, auto_clarify=False, limit=2)
data = json.loads(md.with_suffix(".json").read_text(encoding="utf-8"))
cl = {r["case"]["id"]: r for r in data["rows"]}["clarify_case"]
check("asked but not clarified", cl["actual"]["asked_clarification"] and not cl["actual"]["clarified"])
check("first-pass wrong plant is counted wrong", cl["eval"]["plant_ok"] is False)

print(f"\nRESULT: {PASSED} passed, {len(FAILED)} failed")
if FAILED:
    print("FAILED:", FAILED)
    sys.exit(1)
