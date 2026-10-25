#!/usr/bin/env python3
"""
PlantDoctor benchmark — đo độ chính xác THẬT trên bộ ảnh có nhãn chuẩn.
Trường Đại học Nông Lâm Thái Nguyên

4 cấp độ:
  Cấp 1  Nhận đúng loại cây (plant accuracy)
  Cấp 2  Phân biệt bệnh / khỏe mạnh (detection accuracy)
  Cấp 3  Đúng tên bệnh (disease accuracy)
  Cấp 4  Đơn thuốc an toàn: không chứa hoạt chất cấm + có ít nhất 1 hoạt chất nằm trong
         danh sách khuyến cáo của chuyên gia (recommended_actives) — chỉ tính cho ca bị bệnh.
Kèm: thời gian phản hồi (trung bình, p50, p90), tỷ lệ AI phải hỏi lại loại cây, số lỗi AI.

Quy tắc trung thực:
  * Chế độ thật KHÔNG BAO GIỜ mô phỏng. Ca thiếu ảnh bị BỎ QUA và liệt kê trong báo cáo.
  * --dry-run chỉ để kiểm tra pipeline; báo cáo ghi rõ "MÔ PHỎNG" và được lưu riêng,
    không bao giờ ghi đè docs/.
  * Với n nhỏ, mỗi tỷ lệ kèm khoảng tin cậy 95% (Wilson) để không diễn giải quá mức.

Sử dụng (từ thư mục backend/):
  python3 scripts/eval_benchmark.py                 # chạy thật, tốn lượt gọi AI
  python3 scripts/eval_benchmark.py --limit 3       # chạy thật 3 ca đầu
  python3 scripts/eval_benchmark.py --dry-run       # mô phỏng, không gọi AI
  python3 scripts/eval_benchmark.py --no-clarify    # không tự trả lời câu hỏi làm rõ loại cây

Định dạng ground_truth.json (mỗi ca):
  id, image_path (hoặc image_paths: [ảnh cận cảnh, ảnh toàn cảnh]), group,
  expected_plant, expected_plant_aliases, expected_disease, expected_disease_aliases,
  is_healthy, recommended_actives, plant_hint (tùy chọn: mô phỏng người dùng đã chọn cây)
"""

import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DEFAULT_GT = BASE_DIR / "benchmark_data" / "ground_truth.json"
DEFAULT_OUT = BASE_DIR / "benchmark_data" / "reports"

# Vietnamese/English names for the same active ingredient (lower-case)
ACTIVE_SYNONYMS = {
    "đồng": "copper",
    "copper": "copper",
    "oxychloride": "oxychloride",
    "hydroxide": "hydroxide",
}


def norm(s) -> str:
    return " ".join(str(s or "").lower().replace("-", " ").split())


def match_text(candidate: str, targets: list) -> bool:
    """Case-insensitive substring match in either direction. Empty strings never match."""
    c = norm(candidate)
    if not c:
        return False
    for t in targets:
        t = norm(t)
        if t and (t in c or c in t):
            return True
    return False


def _active_tokens(name: str) -> set:
    tokens = set()
    for w in norm(name).split():
        tokens.add(ACTIVE_SYNONYMS.get(w, w))
    return tokens


def active_overlap(medicines: list, recommended: list) -> bool:
    """True if any suggested active ingredient matches a recommended one.

    Match = substring in either direction, or every significant token of the recommended name
    appears in the suggestion (handles 'Đồng Hydroxide' vs 'Copper Hydroxide 77%').
    """
    for med in medicines or []:
        m = norm(med)
        mt = _active_tokens(med)
        for rec in recommended or []:
            r = norm(rec)
            if not r:
                continue
            if r in m or (m and m in r):
                return True
            rt = {t for t in _active_tokens(rec) if len(t) > 2}
            if rt and rt.issubset(mt):
                return True
    return False


def wilson(k: int, n: int, z: float = 1.96):
    """95% Wilson score interval, in percent."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(max(0.0, centre - half) * 100, 1), round(min(1.0, centre + half) * 100, 1))


def pct(k: int, n: int):
    return round(k * 100 / n, 1) if n else None


def percentile(values: list, q: float):
    if not values:
        return None
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return round(s[idx], 2)


def case_image_paths(case: dict) -> list:
    paths = case.get("image_paths") or ([case["image_path"]] if case.get("image_path") else [])
    return [BASE_DIR / p for p in paths]


def _display_path(p: Path) -> str:
    try:
        return str(p.relative_to(BASE_DIR))
    except ValueError:
        return str(p)


def parse_prediction(res: dict) -> dict:
    pred = (res or {}).get("predictions") or [{}]
    pred = pred[0]
    label = pred.get("label", "")
    name = pred.get("name", "")
    parts = name.split(" - ", 1)
    return {
        "plant": parts[0] if len(parts) > 1 else "",
        "disease": label,
        "confidence": pred.get("confidence", 0),
        "healthy": ("khỏe mạnh" in label.lower()) or ("healthy" in label.lower()),
        "medicines": pred.get("medicines", []) or [],
        "banned": pred.get("banned_warning", []) or [],
    }


def simulate(case: dict) -> dict:
    """Dry-run answer: echoes the ground truth. Only proves the pipeline runs — NOT accuracy."""
    return {
        "plant": case.get("expected_plant", ""),
        "disease": case.get("expected_disease", ""),
        "confidence": 0,
        "healthy": bool(case.get("is_healthy")),
        "medicines": list(case.get("recommended_actives", []))[:1],
        "banned": [],
    }


def run_case_real(case: dict, img_paths: list, auto_clarify: bool) -> dict:
    from app.models.vlm import predict_vlm, clarify_vlm

    images = [Image.open(p).convert("RGB") for p in img_paths]
    t0 = time.time()
    res = predict_vlm(images, lang="vi", plant_hint=case.get("plant_hint"))
    out = {"error": None, "asked_clarification": False, "clarified": False}
    if res is None:
        out["error"] = "AI không trả kết quả (lỗi gọi API hoặc JSON hỏng)"
        out["duration"] = time.time() - t0
        out.update({"plant": "", "disease": "", "confidence": 0, "healthy": False, "medicines": [], "banned": []})
        return out

    first = parse_prediction(res)
    if res.get("status") == "needs_clarification":
        out["asked_clarification"] = True
        out["first_pass"] = first
        if auto_clarify and res.get("session_token"):
            # Simulate a farmer who knows their crop and picks it
            res2 = clarify_vlm(res["session_token"], case.get("expected_plant", ""), lang="vi")
            if res2 is not None:
                res = res2
                out["clarified"] = True
    out["duration"] = time.time() - t0
    out.update(parse_prediction(res))
    return out


def evaluate(case: dict, actual: dict) -> dict:
    plant_aliases = case.get("expected_plant_aliases") or [case.get("expected_plant", "")]
    disease_aliases = case.get("expected_disease_aliases") or [case.get("expected_disease", "")]
    is_healthy = bool(case.get("is_healthy"))
    plant_ok = match_text(actual["plant"], plant_aliases)
    detection_ok = is_healthy == actual["healthy"]
    disease_ok = detection_ok and (is_healthy or match_text(actual["disease"], disease_aliases))
    rx_applicable = (not is_healthy) and bool(case.get("recommended_actives"))
    banned_free = len(actual["banned"]) == 0
    overlap = active_overlap(actual["medicines"], case.get("recommended_actives", [])) if rx_applicable else None
    return {
        "plant_ok": plant_ok,
        "detection_ok": detection_ok,
        "disease_ok": disease_ok,
        "rx_applicable": rx_applicable,
        "banned_free": banned_free,
        "rx_overlap": overlap,
        "rx_ok": (banned_free and bool(overlap)) if rx_applicable else None,
    }


def build_report(meta: dict, rows: list, skipped: list) -> str:
    n = len(rows)
    ev = [r["eval"] for r in rows]

    def line(title, key, rows_subset=None):
        subset = ev if rows_subset is None else rows_subset
        m = len(subset)
        k = sum(1 for e in subset if e[key])
        if m == 0:
            return f"| {title} | — | — | 0 |"
        lo, hi = wilson(k, m)
        return f"| {title} | **{pct(k, m)}%** ({k}/{m}) | {lo}% – {hi}% | {m} |"

    rx_rows = [e for e in ev if e["rx_applicable"]]
    durations = [r["actual"]["duration"] for r in rows if r["actual"].get("duration") is not None]
    asked = sum(1 for r in rows if r["actual"].get("asked_clarification"))
    errors = sum(1 for r in rows if r["actual"].get("error"))

    out = []
    out.append("# Báo cáo Benchmark PlantDoctor")
    out.append("")
    if meta["dry_run"]:
        out.append("> [!CAUTION]")
        out.append("> **MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THẬT.** Chế độ `--dry-run` trả lời bằng chính nhãn chuẩn,")
        out.append("> chỉ để kiểm tra script chạy được. Mọi con số dưới đây KHÔNG phản ánh độ chính xác của AI.")
        out.append("")
    out.append(f"- Thời gian chạy: {meta['started']}  ")
    out.append(f"- Tệp nhãn chuẩn: `{meta['ground_truth']}`  ")
    out.append(f"- Chế độ: {'MÔ PHỎNG (dry-run)' if meta['dry_run'] else 'THẬT (gọi AI)'}; tự trả lời câu hỏi làm rõ: {'có' if meta['auto_clarify'] else 'không'}  ")
    out.append(f"- Số ca đánh giá: **{n}** / {meta['total_cases']} (bỏ qua {len(skipped)} ca thiếu ảnh)")
    out.append("")
    if n == 0:
        out.append("**Chưa có ca nào được đánh giá** — cần đặt ảnh vào `backend/benchmark_data/samples/` theo `image_path` trong ground_truth.json.")
    else:
        if n < 30:
            out.append(f"> [!WARNING]\n> Mẫu nhỏ (n={n}): khoảng tin cậy rất rộng, chưa đủ để kết luận độ chính xác. Nên có ≥ 100 ảnh thực địa, chia đều theo cây/bệnh.")
            out.append("")
        out.append("## 1. Kết quả tổng hợp")
        out.append("")
        out.append("| Chỉ số | Tỷ lệ | KTC 95% (Wilson) | n |")
        out.append("| :--- | :--- | :--- | :--- |")
        out.append(line("Cấp 1 · Đúng loại cây", "plant_ok"))
        out.append(line("Cấp 2 · Đúng bệnh/khỏe", "detection_ok"))
        out.append(line("Cấp 3 · Đúng tên bệnh", "disease_ok"))
        out.append(line("Cấp 4a · Không có hoạt chất cấm (ca bị bệnh)", "banned_free", rx_rows))
        out.append(line("Cấp 4b · Có hoạt chất trong danh sách khuyến cáo", "rx_overlap", rx_rows))
        out.append(line("Cấp 4 · Đơn thuốc đạt (4a và 4b)", "rx_ok", rx_rows))
        out.append("")
        if durations and not meta["dry_run"]:
            out.append(f"- Thời gian phản hồi: trung bình **{round(statistics.mean(durations), 2)}s**, p50 {percentile(durations, 0.5)}s, p90 {percentile(durations, 0.9)}s (đo phía server, không gồm mạng của người dùng)")
        out.append(f"- AI phải hỏi lại loại cây: {asked}/{n} ca" + (" (kết quả ở trên là sau khi đã trả lời đúng loại cây)" if meta["auto_clarify"] and asked else ""))
        out.append(f"- Lỗi AI (không trả kết quả): {errors}/{n} ca — được tính là SAI ở mọi cấp")
        out.append("")
        groups = sorted({r["case"].get("group", "standard") for r in rows})
        if len(groups) > 1:
            out.append("## 2. Theo nhóm ảnh")
            out.append("")
            out.append("| Nhóm | n | Đúng cây | Đúng bệnh |")
            out.append("| :--- | :--- | :--- | :--- |")
            for g in groups:
                sub = [r["eval"] for r in rows if r["case"].get("group", "standard") == g]
                k1 = sum(e["plant_ok"] for e in sub)
                k3 = sum(e["disease_ok"] for e in sub)
                out.append(f"| {g} | {len(sub)} | {pct(k1, len(sub))}% | {pct(k3, len(sub))}% |")
            out.append("")
        out.append("## 3. Chi tiết từng ca")
        out.append("")
        out.append("| Mã ca | Nhóm | Ảnh | Kỳ vọng | AI trả lời | Tin cậy | Cây | Bệnh | Thuốc | Hỏi lại | Thời gian |")
        out.append("| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for r in rows:
            c, a, e = r["case"], r["actual"], r["eval"]
            rx = "—" if e["rx_ok"] is None else ("✅" if e["rx_ok"] else ("🚫" if not e["banned_free"] else "❌"))
            ai = a.get("error") or f"{a['plant']} - {a['disease']}"
            out.append(
                f"| `{c.get('id')}` | {c.get('group', 'standard')} | {r['image_count']} | {c.get('expected_plant')} - {c.get('expected_disease')} | "
                f"{ai} | {a.get('confidence', 0)}% | {'✅' if e['plant_ok'] else '❌'} | {'✅' if e['disease_ok'] else '❌'} | {rx} | "
                f"{'có' if a.get('asked_clarification') else ''} | {round(a.get('duration') or 0, 2)}s |"
            )
        out.append("")
    if skipped:
        out.append("## Ca bị bỏ qua (thiếu ảnh)")
        out.append("")
        for s in skipped:
            out.append(f"- `{s['id']}`: không thấy {', '.join(s['missing'])}")
        out.append("")
    out.append("## Cách đọc")
    out.append("")
    out.append("- So khớp tên dùng danh sách alias trong ground_truth.json (không phân biệt hoa thường). Alias quá rộng sẽ làm điểm cao giả — chuyên gia cần duyệt alias.")
    out.append("- Cấp 4 chỉ kiểm tra đơn thuốc so với danh sách khuyến cáo do chuyên gia nhập, không thay thế thẩm định chuyên môn.")
    return "\n".join(out) + "\n"


def run_benchmark(gt_path: Path, out_dir: Path, dry_run: bool, auto_clarify: bool, limit: int = 0) -> Path:
    if not gt_path.exists():
        print(f"❌ Không tìm thấy {gt_path}")
        sys.exit(1)
    cases = json.loads(gt_path.read_text(encoding="utf-8"))
    if limit:
        cases = cases[:limit]
    meta = {
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ground_truth": str(gt_path.relative_to(BASE_DIR)) if gt_path.is_relative_to(BASE_DIR) else str(gt_path),
        "dry_run": dry_run,
        "auto_clarify": auto_clarify,
        "total_cases": len(cases),
    }
    print(f"📊 Benchmark PlantDoctor — {'MÔ PHỎNG' if dry_run else 'THẬT'} — {len(cases)} ca")

    if not dry_run:
        from app.models import vlm
        vlm._prediction_cache.clear()  # never score a cached answer from an earlier run

    rows, skipped = [], []
    for idx, case in enumerate(cases, 1):
        cid = case.get("id", f"case_{idx}")
        paths = case_image_paths(case)
        missing = [_display_path(p) for p in paths if not p.exists()] if paths else ["(không khai báo image_path)"]
        if dry_run:
            actual = simulate(case)
            actual["duration"] = None
        elif missing:
            print(f"[{idx}/{len(cases)}] ⏭️  {cid}: thiếu ảnh → BỎ QUA (không mô phỏng)")
            skipped.append({"id": cid, "missing": missing})
            continue
        else:
            print(f"[{idx}/{len(cases)}] 🔍 {cid} ({len(paths)} ảnh)…", flush=True)
            try:
                actual = run_case_real(case, paths, auto_clarify)
            except Exception as e:  # unreadable image etc. -> counted as an error, not hidden
                actual = {"error": f"Lỗi: {e}", "plant": "", "disease": "", "confidence": 0, "healthy": False,
                          "medicines": [], "banned": [], "duration": None}
        ev = evaluate(case, actual)
        rows.append({"case": case, "actual": actual, "eval": ev, "image_count": max(1, len(paths))})
        print(f"     cây {'✅' if ev['plant_ok'] else '❌'}  bệnh {'✅' if ev['disease_ok'] else '❌'}  → {actual.get('error') or (actual['plant'] + ' - ' + actual['disease'])}")

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_MO_PHONG" if dry_run else ""
    md_path = out_dir / f"benchmark_{stamp}{suffix}.md"
    md_path.write_text(build_report(meta, rows, skipped), encoding="utf-8")
    json_path = out_dir / f"benchmark_{stamp}{suffix}.json"
    json_path.write_text(json.dumps({"meta": meta, "rows": rows, "skipped": skipped}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n📄 Báo cáo: {md_path}\n🧾 Dữ liệu: {json_path}")
    if dry_run:
        print("⚠️  Đây là MÔ PHỎNG — không dùng các con số này để đánh giá độ chính xác.")
    return md_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Benchmark độ chính xác PlantDoctor")
    ap.add_argument("--dry-run", action="store_true", help="Mô phỏng (không gọi AI) — chỉ để kiểm tra script")
    ap.add_argument("--no-clarify", action="store_true", help="Không tự trả lời câu hỏi làm rõ loại cây")
    ap.add_argument("--ground-truth", type=Path, default=DEFAULT_GT)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0, help="Chỉ chạy N ca đầu")
    a = ap.parse_args()
    run_benchmark(a.ground_truth, a.output_dir, dry_run=a.dry_run, auto_clarify=not a.no_clarify, limit=a.limit)
