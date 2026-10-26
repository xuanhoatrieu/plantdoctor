"""Download and optimize all 50 CABI Plantwise Vietnam reference images locally onto the server.

Stores verified JPEG thumbnails (max 600x600, quality=82) in:
    backend/app/data/kb_images/<slug>.jpg

Updates `backend/app/data/vn_diseases.json` so every record's `image_url` points to
the self-hosted local route:
    /api/v1/kb_images/<slug>.jpg
with zero runtime dependency on external websites (iNaturalist / Wikimedia).
"""

import io
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from PIL import Image

HEADERS = {
    "User-Agent": "PlantDoctorTUAF/2.7 (https://benhcay.tuaf.edu.vn; mailto:trieuxuanhoa@tuaf.edu.vn)"
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_JSON_PATH = os.path.join(BASE_DIR, "app", "data", "vn_diseases.json")
KB_IMG_DIR = os.path.join(BASE_DIR, "app", "data", "kb_images")


def slugify(text: str) -> str:
    s = (text or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.lower()).strip("_")
    return s[:64] or "disease"


def fetch_inat_photo(query: str) -> str:
    q = urllib.parse.quote(query.strip())
    url = f"https://api.inaturalist.org/v1/taxa?q={q}&per_page=3"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        for r in data.get("results", []):
            dp = r.get("default_photo") or {}
            img = dp.get("medium_url") or dp.get("url")
            if img:
                return img
    return ""


def download_and_optimize(url: str, dest_path: str) -> bool:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    img = Image.open(io.BytesIO(raw))
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    img.thumbnail((600, 600), Image.Resampling.LANCZOS)
    img.save(dest_path, format="JPEG", quality=82, optimize=True)
    # Verify saved file opens cleanly
    with Image.open(dest_path) as check_img:
        check_img.verify()
    return os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024


def main():
    os.makedirs(KB_IMG_DIR, exist_ok=True)
    with open(KB_JSON_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    ok_count = 0
    for idx, item in enumerate(entries):
        crop_slug = slugify(item.get("crop", ""))
        name_slug = slugify(item.get("name_en") or item.get("name_vi", ""))
        filename = f"{idx + 1:02d}_{crop_slug}_{name_slug}.jpg"
        dest_path = os.path.join(KB_IMG_DIR, filename)
        local_url = f"/api/v1/kb_images/{filename}"

        # Keep track of original source URL if it was remote
        src_url = item.get("source_image_url") or (
            item.get("image_url") if str(item.get("image_url", "")).startswith("http") else ""
        )
        if not src_url:
            # Resolve fallback for Durian psyllid (Carsidaridae / Psylloidea) or any missing item
            for fallback_q in [item.get("scientific_name", ""), "Carsidaridae", "Psylloidea", item.get("name_en", "")]:
                if not fallback_q:
                    continue
                try:
                    src_url = fetch_inat_photo(fallback_q)
                    if src_url:
                        break
                except Exception:
                    pass

        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
            item["image_url"] = local_url
            if src_url:
                item["source_image_url"] = src_url
            ok_count += 1
            print(f"[{idx + 1:02d}/50] EXISTS {filename} ({os.path.getsize(dest_path) // 1024} KB)")
            continue

        if not src_url:
            print(f"[{idx + 1:02d}/50] ERROR: No source URL for {item['name_vi']}")
            continue

        try:
            if download_and_optimize(src_url, dest_path):
                item["source_image_url"] = src_url
                item["image_url"] = local_url
                ok_count += 1
                print(f"[{idx + 1:02d}/50] DOWNLOADED {filename} ({os.path.getsize(dest_path) // 1024} KB) <- {src_url}")
            else:
                print(f"[{idx + 1:02d}/50] FAILED validation for {filename}")
        except Exception as e:
            print(f"[{idx + 1:02d}/50] EXCEPTION downloading {src_url}: {e}")
        time.sleep(0.15)

    with open(KB_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"\nCompleted: {ok_count}/{len(entries)} local reference images verified in {KB_IMG_DIR}")


if __name__ == "__main__":
    main()
