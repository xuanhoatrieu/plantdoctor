# LeafDoctor 🌿 - Phát hiện bệnh cây trồng bằng AI

## Tổng quan dự án

Ứng dụng phát hiện bệnh cây trồng từ ảnh lá cây sử dụng AI deep learning. User chụp/upload ảnh lá cây → server chạy model AI → trả kết quả bệnh + cách chữa + thuốc đề xuất.

**Định hướng:** Web app trước, sau đó build mobile app (Flutter) làm giao diện gọi API về server.

## Kiến trúc

```
┌─────────────┐       ┌─────────────────────┐       ┌──────────────┐
│  Mobile App │──────▶│   Backend API        │──────▶│  AI Models   │
│  (Flutter)  │◀──────│   (FastAPI + Python) │◀──────│  (PyTorch)   │
└─────────────┘       └─────────────────────┘       └──────────────┘
       │                       │                           │
       │              ┌────────▼────────┐                  │
       │              │   PostgreSQL    │                  │
       │              └─────────────────┘                  │
       │                                                   │
       └── Web UI (React) ─────────────────────────────────┘
```

## Tech Stack

| Thành phần | Công nghệ | Phiên bản |
|---|---|---|
| Backend API | FastAPI (Python) | 0.115.6 |
| AI Inference | PyTorch + CUDA | 2.5.1 |
| Model Hub | HuggingFace Transformers | 4.47.1 |
| Database | PostgreSQL | 16 |
| Frontend Web | React + Vite + TailwindCSS | React 18, Vite 6 |
| Mobile | Flutter (phase sau) | - |
| Deploy | Docker Compose + NVIDIA GPU | - |
| Server | Ubuntu + GPU RTX 2070 Super | - |

## AI Models

### 1. ResNet50 (`mesabo/agri-plant-disease-resnet50`)
- **Source:** HuggingFace
- **Architecture:** ResNet50 (23.6M params, 91MB)
- **Dataset:** PlantVillage (54,305 images)
- **Accuracy:** 95%+
- **Input:** 224x224 RGB
- **Inference:** < 100ms (CPU), nhanh hơn trên GPU
- **License:** Apache 2.0

### 2. MobileNetV2 (`Daksh159/plant-disease-mobilenetv2`)
- **Source:** HuggingFace
- **Architecture:** MobileNetV2 (lightweight)
- **Dataset:** PlantVillage augmented (~87,000 images)
- **Accuracy:** 95%
- **Input:** 224x224 RGB
- **Đặc điểm:** Nhẹ, phù hợp inference nhanh
- **License:** Apache 2.0

### Cây trồng & bệnh hỗ trợ (14 loại cây, 38 classes)

| Cây | Số bệnh | Chi tiết |
|---|---|---|
| Tomato (Cà chua) | 10 | Bacterial spot, Early/Late blight, Leaf Mold, Septoria, Spider mites, Target Spot, YLCV, Mosaic virus, Healthy |
| Apple (Táo) | 4 | Scab, Black rot, Cedar rust, Healthy |
| Corn (Ngô) | 4 | Gray leaf spot, Common rust, Northern Leaf Blight, Healthy |
| Grape (Nho) | 4 | Black rot, Esca, Leaf blight, Healthy |
| Potato (Khoai tây) | 3 | Early blight, Late blight, Healthy |
| Pepper (Ớt chuông) | 2 | Bacterial spot, Healthy |
| Cherry | 2 | Powdery mildew, Healthy |
| Peach (Đào) | 2 | Bacterial spot, Healthy |
| Strawberry (Dâu tây) | 2 | Leaf scorch, Healthy |
| Orange (Cam) | 1 | Huanglongbing (Citrus greening) |
| Squash (Bí) | 1 | Powdery mildew |
| Blueberry (Việt quất) | 1 | Healthy only |
| Raspberry (Mâm xôi) | 1 | Healthy only |
| Soybean (Đậu nành) | 1 | Healthy only |

## Tính năng

### Đã triển khai (v1.0)
- [x] Upload/drag-drop ảnh lá cây
- [x] Chọn model AI để dự đoán
- [x] Kết quả: tên bệnh, độ tin cậy (%), top 5 predictions
- [x] Thông tin bệnh: mô tả, cách điều trị, thuốc đề xuất
- [x] Song ngữ Việt/Anh (mặc định Việt)
- [x] GPU inference (RTX 2070S)
- [x] REST API cho mobile app
- [x] Docker Compose deployment

### Roadmap (phát triển tiếp)
- [ ] Lịch sử dự đoán (lưu DB)
- [ ] User authentication
- [ ] Flutter mobile app
- [ ] Thêm model cho cây trồng Việt Nam (lúa, sắn, cà phê...)
- [ ] Fine-tune model trên dữ liệu thực tế
- [ ] Grad-CAM heatmap (giải thích vùng bệnh trên ảnh)
- [ ] Export ONNX/TensorRT cho inference nhanh hơn
- [ ] Chatbot tư vấn nông nghiệp

## Cấu trúc thư mục

```
/mnt/nvme/leaf/
├── README.md                    # Hướng dẫn nhanh
├── PROJECT.md                   # File này - thông tin đầy đủ
├── docker-compose.yml           # Deploy production
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variables mẫu
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app + lifespan (load models)
│       ├── config.py            # Pydantic settings
│       ├── models/
│       │   ├── __init__.py
│       │   └── inference.py     # ModelRegistry - load & predict
│       ├── routers/
│       │   ├── __init__.py
│       │   └── prediction.py    # API endpoints (/predict, /models)
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── prediction.py    # Pydantic response models
│       ├── database/
│       │   └── __init__.py      # (sẽ thêm ORM models)
│       └── data/
│           └── diseases.json    # 38 bệnh, song ngữ, thuốc đề xuất
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf               # Reverse proxy to backend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── index.css
│       ├── App.jsx              # Main UI component
│       └── i18n.js              # Translations vi/en
└── mobile/                      # Flutter (chưa triển khai)
```

## API Endpoints

| Method | Endpoint | Mô tả | Params |
|---|---|---|---|
| GET | `/api/v1/health` | Health check | - |
| GET | `/api/v1/models` | Danh sách models | - |
| POST | `/api/v1/predict` | Dự đoán bệnh | `file` (image), `model_id` (resnet50/mobilenetv2), `lang` (vi/en) |

### Ví dụ response `/api/v1/predict`:
```json
{
  "model_id": "resnet50",
  "model_name": "ResNet50 - Plant Disease",
  "predictions": [
    {
      "label": "Tomato___Late_blight",
      "confidence": 94.5,
      "name": "Bệnh mốc sương muộn cà chua",
      "description": "Bệnh do nấm Phytophthora infestans...",
      "treatment": "Phun thuốc ngay khi phát hiện...",
      "medicines": ["Metalaxyl + Mancozeb", "Cymoxanil", "Dimethomorph"]
    }
  ]
}
```

## Hướng dẫn chạy

### Development (không Docker)

**Backend:**
```bash
cd /mnt/nvme/leaf/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd /mnt/nvme/leaf/frontend
npm install
npm run dev
```

Truy cập: http://localhost:3000

### Production (Docker Compose)
```bash
cd /mnt/nvme/leaf
docker compose up --build -d
```

Truy cập: http://server-ip:3000

### Yêu cầu hệ thống
- Python 3.11+
- Node.js 20+
- NVIDIA GPU + CUDA drivers (khuyến nghị)
- Docker + Docker Compose (cho production)
- RAM: tối thiểu 4GB (models ~500MB khi load)
- Disk: ~2GB (models + dependencies)

## Ghi chú kỹ thuật

- Models được download tự động từ HuggingFace lần đầu chạy
- Inference trên GPU 2070S: ~10-30ms/ảnh
- Frontend proxy `/api/*` về backend qua Vite (dev) hoặc Nginx (prod)
- CORS cho phép tất cả origins (sẽ restrict khi deploy production)
- Phiên bản này chưa train/finetune model, dùng pretrained as-is
