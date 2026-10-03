# Bộ dữ liệu Benchmark chuẩn hóa — PlantDoctor 🌿

Tài liệu hướng dẫn cán bộ, giảng viên và sinh viên Trường Đại học Nông Lâm Thái Nguyên thu thập, thẩm định và chuẩn hóa dữ liệu ảnh phục vụ đo lường độ chính xác AI.

---

## 1. Cấu trúc thư mục
```
benchmark_data/
├── ground_truth.json      # File nhãn chuẩn do chuyên gia thẩm định
├── samples/               # Thư mục chứa các tệp ảnh kiểm thử (.jpg, .png)
└── README.md              # File hướng dẫn này
```

## 2. Tiêu chí phân nhóm ảnh (3 nhóm)
1. **`standard_leaf` (Ảnh chuẩn phòng thí nghiệm/vườn cây):**
   - Chụp 1 chiếc lá rõ ràng, ánh sáng thuận, thấy rõ phiến lá, gân lá và mép lá.
2. **`field_condition` (Ảnh thực tế đồng ruộng):**
   - Chụp cả cành lá hoặc chùm lá ngoài đồng ruộng thực tế (có bóng râm, ánh nắng, hậu cảnh tự nhiên).
3. **`trunk_syndrome` hoặc `closeup_lesion` (Ảnh cận cảnh/Hội chứng thân cây):**
   - Ảnh chụp zoom sát vào vết bệnh cục bộ hoặc vết nứt vỏ thân cây (dùng để kiểm thử tính năng Tương tác làm rõ - Interactive Clarification và Chẩn đoán hội chứng).

## 3. Quy cách dán nhãn (`ground_truth.json`)
Mỗi mẫu ảnh bao gồm:
- `id`: Mã định danh duy nhất (ví dụ: `citrus_canker_001`).
- `image_path`: Đường dẫn tương đối tới file ảnh trong `samples/`.
- `expected_plant`: Tên cây trồng chính xác theo tiếng Việt.
- `expected_plant_aliases`: Các tên gọi đồng nghĩa hoặc nhóm cây liên quan.
- `expected_disease`: Tên bệnh chính xác.
- `expected_disease_aliases`: Các tên gọi khác, tên tiếng Anh hoặc tên khoa học tác nhân gây bệnh.
- `recommended_actives`: Danh sách hoạt chất khuyến nghị theo tài liệu của Cục BVTV Việt Nam.

## 4. Chạy script đánh giá tự động
Chạy lệnh từ thư mục `backend/`:
```bash
python3 scripts/eval_benchmark.py
```
Báo cáo đo lường độ chính xác sẽ tự động xuất ra file `docs/BENCHMARK_REPORT.md`.
