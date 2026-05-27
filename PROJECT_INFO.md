# PlantDoctor 🌿 - Chẩn đoán bệnh cây trồng bằng AI

## Thông tin dự án
- **Tên:** PlantDoctor
- **Tác giả:** Triệu Xuân Hòa
- **Đơn vị:** Trường Đại học Nông Lâm Thái Nguyên
- **Mô tả:** Ứng dụng chẩn đoán bệnh cây trồng từ ảnh lá cây sử dụng AI (GPT-5.5 Vision)

## Tech Stack

### Web (đã hoàn thành)
- **Backend:** FastAPI + GPT-5.5 Vision API (qua proxy 152.67.112.145:8317)
- **Frontend:** React + Vite + TailwindCSS
- **AI:** GPT-5.5 Vision (primary), ResNet50 + MobileNetV2 + SigLIP2 (offline backup)
- **Deploy:** VPS (sẽ production)

### Mobile (đang phát triển)
- **Framework:** React Native + Expo
- **Platforms:** iOS + Android
- **Mode:** Online only (cần kết nối mạng)
- **Backend:** Cùng API với web (VPS có domain + HTTPS)

## Tính năng
1. 📷 Chụp/upload ảnh lá cây → AI chẩn đoán bệnh
2. 📋 Kết quả: tên bệnh, mức độ, triệu chứng, cách điều trị, thuốc đề xuất
3. 📜 Lịch sử chẩn đoán
4. 📚 Thư viện bệnh (chi tiết, hình ảnh, phòng trị)
5. 🧪 Danh mục thuốc BVTV (4712 sản phẩm, tìm kiếm/lọc)
6. ⛅ Thời tiết nông nghiệp
7. 🌐 Đa ngôn ngữ (Việt/Anh)

## API
- **Proxy:** 152.67.112.145:8317
- **API Key:** ai-teaching-assistant-prod
- **Model:** gpt-5.5
- **Endpoint:** POST /api/v1/predict (multipart: file, model_id=gpt55_vision, lang)

## Cấu trúc
```
leaf/
├── backend/           # FastAPI server
├── frontend/          # React web (đã xong)
├── mobile/            # React Native Expo app
├── restart.sh         # Script restart services
└── PROJECT_INFO.md    # File này
```

## Accounts
- Apple Developer: ✅ có
- Google Play Console: ✅ có
