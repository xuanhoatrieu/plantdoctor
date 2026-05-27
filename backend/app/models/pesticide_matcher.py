import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BANNED_SUBSTANCES = [
    'aldrin', 'bhc', 'lindane', 'cadmium', 'carbofuran', 'chlordane', 'chlordimeform',
    'ddt', 'dieldrin', 'endosulfan', 'endrin', 'heptachlor', 'isobenzan', 'isodrin',
    'lead', 'methamidophos', 'methyl parathion', 'monocrotophos', 'parathion ethyl',
    'sodium pentachlorophenate', 'pentachlorophenol', 'phosphamidon', 'polychlorocamphene',
    'trichlorfon', 'chlorophos', 'arsenic', 'captan', 'captafol', 'hexachlorobenzene',
    'mercury', 'selenium', 'talium', '2,4,5-t',
]

_pesticides_data = None


def _load_pesticides():
    global _pesticides_data
    if _pesticides_data is not None:
        return _pesticides_data
    path = Path(__file__).parent.parent.parent.parent / "frontend" / "public" / "pesticides.json"
    if not path.exists():
        logger.warning("pesticides.json not found at %s", path)
        _pesticides_data = []
        return _pesticides_data
    with open(path, "r", encoding="utf-8") as f:
        _pesticides_data = json.load(f)
    logger.info("Loaded %d pesticides for matching", len(_pesticides_data))
    return _pesticides_data


def match_medicines(medicines: list[str]) -> dict:
    """Match medicine names (active ingredients) against pesticide database.
    
    Returns:
        {
            "matched_products": [{"active": "...", "products": [...], "banned": False}],
            "banned_warning": ["substance1", ...]
        }
    """
    pesticides = _load_pesticides()
    matched_products = []
    banned_warning = []

    for med in medicines:
        med_lower = med.lower().strip()
        
        # Check if banned
        is_banned = any(b in med_lower for b in BANNED_SUBSTANCES)
        if is_banned:
            banned_warning.append(med)
            matched_products.append({"active": med, "products": [], "banned": True})
            continue

        # Search in pesticides database by active ingredient
        products = []
        for p in pesticides:
            if med_lower in p.get("a", "").lower():
                products.append({"name": p["n"], "company": p.get("c", ""), "target": p.get("t", "")})
                if len(products) >= 5:  # Limit to 5 products per active ingredient
                    break

        matched_products.append({"active": med, "products": products, "banned": False})

    return {"matched_products": matched_products, "banned_warning": banned_warning}
