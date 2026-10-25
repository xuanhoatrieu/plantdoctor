# Báo cáo Đánh giá Độ chính xác AI — PlantDoctor

> **Trạng thái (cập nhật 2026-10-03, US-021): CHƯA CÓ KẾT QUẢ ĐO THẬT.**

## Vì sao file này không còn số liệu?

Phiên bản trước của file này hiển thị 100% / 100% / 100% và độ trễ 1.2s cho 5 mẫu.
Đó là **dữ liệu mô phỏng** do script `eval_benchmark.py` cũ tự sinh khi
không tìm thấy ảnh mẫu (thư mục `backend/benchmark_data/samples/` trống) —
**không phải** kết quả AI chẩn đoán trên ảnh thật. Số liệu đó đã bị gỡ bỏ để tránh hiểu nhầm.

## Cách đo độ chính xác thật

1. Thu thập ảnh thực địa, đặt vào `backend/benchmark_data/samples/`.
2. Chuyên gia BVTV gán nhãn trong `backend/benchmark_data/ground_truth.json`
   (xem hướng dẫn ở `backend/benchmark_data/README.md`).
3. Chạy (từ thư mục `backend/`, backend AI phải truy cập được):

   ```bash
   venv/bin/python scripts/eval_benchmark.py
   ```

4. Báo cáo được ghi vào `backend/benchmark_data/reports/benchmark_<thời-gian>.md` và `.json`.

Script mới:
- **Bỏ qua** (và liệt kê) các ca thiếu ảnh — không bao giờ tự bịa kết quả.
- Báo cáo 4 cấp: đúng cây, phát hiện bệnh/khỏe, đúng bệnh, an toàn thuốc
  (không chứa hoạt chất cấm + trùng với hoạt chất khuyến nghị).
- Kèm khoảng tin cậy Wilson 95%, độ trễ p50/p90, cảnh báo khi mẫu nhỏ.
- Chế độ `--dry-run` chỉ để kiểm tra pipeline; báo cáo sinh ra có hậu tố
  `_MO_PHONG` và banner "MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THẬT".

> [!IMPORTANT]
> Với dưới ~30 ảnh mỗi nhóm, khoảng tin cậy rất rộng — không nên công bố một con số
> "độ chính xác X%" duy nhất cho tới khi có tập mẫu đủ lớn (khuyến nghị ≥ 100 ảnh thực địa).

## Nguồn dữ liệu bổ sung

Phản hồi đúng/sai của người dùng (tab **💬 Phản hồi chẩn đoán** trong Admin) là
nguồn ước lượng thực tế, nhưng có thiên lệch tự chọn (người gặp kết quả sai dễ phản hồi hơn).
Các ca được chuyên gia xác nhận nên được đưa vào `ground_truth.json`.
