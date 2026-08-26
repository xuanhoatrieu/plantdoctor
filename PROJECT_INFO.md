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


2. Lệnh Build file để CÀI ĐẶT TEST (Preview)
Chạy trong thư mục mobile/:

bash
cd /mnt/nvme/leaf/mobile
A. Cho Android (Xuất file .apk cài trực tiếp vào điện thoại):
bash
eas build -p android --profile preview
TIP

Lệnh này sẽ tạo trực tiếp file .apk (không cần đưa lên CH Play). Bạn chỉ cần quét mã QR hoặc tải file về máy điện thoại Android để cài và test ngay tính năng chẩn đoán bệnh.

B. Cho iOS (Internal distribution / TestFlight):
bash
eas build -p ios --profile preview
3. Lệnh Build & SUBMIT lên App Store & Google Play (CH Play)
A. Build bản phát hành (Production):
Android (Xuất file .aab chuẩn của Google Play):
bash
eas build -p android --profile production
iOS (Xuất file .ipa chuẩn của Apple App Store):
bash
eas build -p ios --profile production
Hoặc Build cả 2 nền tảng cùng lúc:
bash
eas build --platform all --profile production
B. Lệnh Submit tự động lên Store:
Sau khi build xong trên Expo Cloud (hoặc chọn bản build có sẵn):

Submit lên iOS App Store / TestFlight:

bash
eas submit -p ios --profile production
Submit lên Google Play Console (CH Play):

bash
eas submit -p android --profile production
(Tùy chọn) Build và Tự động Submit luôn khi xong:

bash
# Cho iOS
eas build -p ios --profile production --auto-submit
# Cho Android
eas build -p android --profile production --auto-submit
