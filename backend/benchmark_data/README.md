# Bộ dữ liệu Benchmark chuẩn hóa — PlantDoctor 🌿

Tài liệu hướng dẫn cán bộ, giảng viên và sinh viên Trường Đại học Nông Lâm Thái Nguyên thu thập, thẩm định và chuẩn hóa dữ liệu ảnh phục vụ đo lường độ chính xác AI.

---

## 1. Cấu trúc thư mục
```
benchmark_data/
├── ground_truth.json      # File nhãn chuẩn do chuyên gia thẩm định
├── samples/               # Thư mục chứa các tệp ảnh kiểm thử (.jpg, .png)
├── reports/               # Báo cáo do eval_benchmark.py sinh ra (.md + .json)
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
- `image_paths` *(tuỳ chọn)*: Danh sách tối đa 2 ảnh cho cùng một ca (ảnh 1 cận vết bệnh, ảnh 2 toàn cành/cây). Nếu có, trường này được ưu tiên hơn `image_path`.
- `expected_plant`: Tên cây trồng chính xác theo tiếng Việt.
- `expected_plant_aliases`: Các tên gọi đồng nghĩa hoặc nhóm cây liên quan.
- `expected_disease`: Tên bệnh chính xác.
- `expected_disease_aliases`: Các tên gọi khác, tên tiếng Anh hoặc tên khoa học tác nhân gây bệnh.
- `recommended_actives`: Danh sách hoạt chất khuyến nghị theo tài liệu của Cục BVTV Việt Nam.

## 4. Chạy script đánh giá tự động
Chạy lệnh từ thư mục `backend/` (cần truy cập được dịch vụ AI):
```bash
venv/bin/python scripts/eval_benchmark.py                 # chạy thật toàn bộ
venv/bin/python scripts/eval_benchmark.py --limit 5       # chỉ 5 ca đầu
venv/bin/python scripts/eval_benchmark.py --no-clarify    # không tự trả lời câu hỏi làm rõ loại cây
venv/bin/python scripts/eval_benchmark.py --dry-run       # MÔ PHỎNG, không gọi AI
```
Báo cáo được ghi vào `benchmark_data/reports/benchmark_<thời-gian>.md` và `.json`
(đổi thư mục bằng `--output-dir`, đổi file nhãn bằng `--ground-truth`).

Lưu ý quan trọng:
- Ca **thiếu ảnh sẽ bị bỏ qua và liệt kê** trong báo cáo — script không bao giờ tự sinh kết quả.
- `--dry-run` chỉ để kiểm tra pipeline; file báo cáo có hậu tố `_MO_PHONG` và banner
  "MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THẬT". Không dùng số liệu này để công bố.
- Khi AI hỏi làm rõ loại cây, script mặc định tự trả lời bằng `expected_plant` (mô phỏng người dùng
  chọn đúng cây) và đánh dấu ca đó là "có làm rõ".
- Báo cáo kèm khoảng tin cậy Wilson 95% — với mẫu nhỏ (< 30 ca), khoảng này rất rộng.
