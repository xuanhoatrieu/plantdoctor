# LeafDoctor 🌿 - Phát hiện bệnh cây trồng bằng AI

## Mô tả
Ứng dụng web/mobile phát hiện bệnh cây trồng từ ảnh lá cây sử dụng AI. Hỗ trợ nhiều model, đa ngôn ngữ (Việt/Anh).

## Tech Stack
- **Backend:** FastAPI + PyTorch (GPU inference)
- **Frontend:** React + Vite + TailwindCSS
- **Database:** PostgreSQL
- **Models:** ResNet50, MobileNetV2 (pretrained on PlantVillage)
- **Deploy:** Docker Compose with NVIDIA GPU support

## Cây trồng hỗ trợ (14 loại, 38 bệnh)
Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato

## Chạy nhanh (Development)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (Production)
```bash
docker compose up --build
```

## API Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/models` - List available models
- `POST /api/v1/predict` - Predict disease (multipart form: file, model_id, lang)

## Cấu trúc
```
leaf/
├── backend/          # FastAPI server
│   ├── app/
│   │   ├── main.py          # App entry point
│   │   ├── config.py        # Settings
│   │   ├── models/          # AI model inference
│   │   ├── routers/         # API routes
│   │   ├── schemas/         # Pydantic schemas
│   │   └── data/            # Disease info (JSON)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React web UI
├── mobile/           # Flutter (coming soon)
└── docker-compose.yml
```
