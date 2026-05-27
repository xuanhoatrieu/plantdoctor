import json
import logging
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages loading and inference for multiple plant disease models."""

    def __init__(self):
        self._models: dict = {}
        self._disease_data: dict = {}
        self._load_disease_data()

    def _load_disease_data(self):
        data_path = Path(__file__).parent.parent / "data" / "diseases.json"
        with open(data_path, "r", encoding="utf-8") as f:
            self._disease_data = json.load(f)

    @property
    def available_models(self) -> list[dict]:
        return [
            {"id": mid, "name": info["name"], "description": info["description"], "classes": info["num_classes"]}
            for mid, info in self._models.items()
        ]

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._models

    def load_resnet50(self):
        """Load ResNet50 model from HuggingFace."""
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        model_name = "mesabo/agri-plant-disease-resnet50"
        logger.info("Loading ResNet50 model: %s", model_name)

        processor = AutoImageProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)
        model.eval()

        if torch.cuda.is_available():
            model = model.cuda()

        self._models["resnet50"] = {
            "name": "ResNet50 - Plant Disease",
            "description": "ResNet50 trained on PlantVillage (38 classes, 95%+ accuracy)",
            "num_classes": 38,
            "model": model,
            "processor": processor,
            "type": "transformers",
        }
        logger.info("ResNet50 loaded successfully")

    def load_rice_disease(self):
        """Load Rice Leaf Disease model from HuggingFace (SigLIP2, 94.77% accuracy)."""
        from transformers import AutoImageProcessor, SiglipForImageClassification

        model_name = "prithivMLmods/Rice-Leaf-Disease"
        logger.info("Loading Rice Disease model: %s", model_name)

        processor = AutoImageProcessor.from_pretrained(model_name)
        model = SiglipForImageClassification.from_pretrained(model_name)
        model.eval()

        if torch.cuda.is_available():
            model = model.cuda()

        self._models["rice_disease"] = {
            "name": "Rice Leaf Disease - SigLIP2",
            "description": "SigLIP2 fine-tuned for rice diseases (5 classes, 94.77% accuracy)",
            "num_classes": 5,
            "model": model,
            "processor": processor,
            "type": "transformers",
        }
        logger.info("Rice Disease model loaded successfully")

    def load_mobilenetv2(self):
        """Load MobileNetV2 model from HuggingFace (linkanjarad, native transformers)."""
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        model_name = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
        logger.info("Loading MobileNetV2 model: %s", model_name)

        processor = AutoImageProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)
        model.eval()

        if torch.cuda.is_available():
            model = model.cuda()

        # Map linkanjarad labels -> diseases.json keys
        label_map = {
            "Apple Scab": "Apple___Apple_scab",
            "Apple with Black Rot": "Apple___Black_rot",
            "Cedar Apple Rust": "Apple___Cedar_apple_rust",
            "Healthy Apple": "Apple___healthy",
            "Healthy Blueberry Plant": "Blueberry___healthy",
            "Cherry with Powdery Mildew": "Cherry_(including_sour)___Powdery_mildew",
            "Healthy Cherry Plant": "Cherry_(including_sour)___healthy",
            "Corn (Maize) with Cercospora and Gray Leaf Spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            "Corn (Maize) with Common Rust": "Corn_(maize)___Common_rust_",
            "Corn (Maize) with Northern Leaf Blight": "Corn_(maize)___Northern_Leaf_Blight",
            "Healthy Corn (Maize) Plant": "Corn_(maize)___healthy",
            "Grape with Black Rot": "Grape___Black_rot",
            "Grape with Esca (Black Measles)": "Grape___Esca_(Black_Measles)",
            "Grape with Isariopsis Leaf Spot": "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
            "Healthy Grape Plant": "Grape___healthy",
            "Orange with Citrus Greening": "Orange___Haunglongbing_(Citrus_greening)",
            "Peach with Bacterial Spot": "Peach___Bacterial_spot",
            "Healthy Peach Plant": "Peach___healthy",
            "Bell Pepper with Bacterial Spot": "Pepper,_bell___Bacterial_spot",
            "Healthy Bell Pepper Plant": "Pepper,_bell___healthy",
            "Potato with Early Blight": "Potato___Early_blight",
            "Potato with Late Blight": "Potato___Late_blight",
            "Healthy Potato Plant": "Potato___healthy",
            "Healthy Raspberry Plant": "Raspberry___healthy",
            "Healthy Soybean Plant": "Soybean___healthy",
            "Squash with Powdery Mildew": "Squash___Powdery_mildew",
            "Strawberry with Leaf Scorch": "Strawberry___Leaf_scorch",
            "Healthy Strawberry Plant": "Strawberry___healthy",
            "Tomato with Bacterial Spot": "Tomato___Bacterial_spot",
            "Tomato with Early Blight": "Tomato___Early_blight",
            "Tomato with Late Blight": "Tomato___Late_blight",
            "Tomato with Leaf Mold": "Tomato___Leaf_Mold",
            "Tomato with Septoria Leaf Spot": "Tomato___Septoria_leaf_spot",
            "Tomato with Spider Mites or Two-spotted Spider Mite": "Tomato___Spider_mites Two-spotted_spider_mite",
            "Tomato with Target Spot": "Tomato___Target_Spot",
            "Tomato Yellow Leaf Curl Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
            "Tomato Mosaic Virus": "Tomato___Tomato_mosaic_virus",
            "Healthy Tomato Plant": "Tomato___healthy",
        }

        self._models["mobilenetv2"] = {
            "name": "MobileNetV2 - Plant Disease",
            "description": "MobileNetV2 fine-tuned on PlantVillage (38 classes)",
            "num_classes": 38,
            "model": model,
            "processor": processor,
            "label_map": label_map,
            "type": "transformers",
        }
        logger.info("MobileNetV2 loaded successfully")

    def predict(self, model_id: str, image: Image.Image, lang: str = "vi") -> Optional[dict]:
        if model_id not in self._models:
            return None

        info = self._models[model_id]
        model = info["model"]
        device = next(model.parameters()).device

        return self._predict_transformers(model_id, info, image, lang, device)

    def _predict_transformers(self, model_id: str, info: dict, image: Image.Image, lang: str, device) -> dict:
        processor = info["processor"]
        model = info["model"]
        label_map = info.get("label_map", {})

        inputs = processor(images=image.convert("RGB"), return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            num_classes = probs.shape[-1]
            top_k = min(5, num_classes)
            topk = torch.topk(probs[0], top_k)

        results = []
        for i in range(top_k):
            idx = topk.indices[i].item()
            conf = topk.values[i].item()
            label = model.config.id2label[idx]
            disease_key = label_map.get(label, label)
            disease_info = self._get_disease_info(disease_key, lang)
            results.append({"label": label, "confidence": round(conf * 100, 2), "severity": "", **disease_info})

        return {"model_id": model_id, "model_name": info["name"], "predictions": results}

    def _get_disease_info(self, label: str, lang: str) -> dict:
        info = self._disease_data.get(label, {}).get(lang)
        if info:
            return {"name": info["name"], "description": info["description"], "treatment": info["treatment"], "medicines": info["medicines"]}
        # Fallback: return raw label
        return {"name": label.replace("_", " "), "description": "", "treatment": "", "medicines": []}


# Singleton
registry = ModelRegistry()
