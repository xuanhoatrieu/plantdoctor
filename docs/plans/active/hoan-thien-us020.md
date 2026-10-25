# Kế hoạch: Hoàn thiện các phần còn thiếu của US-020 (Story US-021)

## Bối cảnh
Sau khi rà soát lại v2.5.8, các hạng mục sau đã bị đánh dấu "xong" nhưng thực tế chưa làm hoặc làm chưa đủ.
Kế hoạch này làm nốt và **chỉ đánh dấu [x] khi đã có bằng chứng kiểm chứng**.

## Quyết định thiết kế
- **Kiểm tra độ sáng/độ nét trên mobile:** React Native không đọc được điểm ảnh nếu không thêm thư viện native mới.
  → Kiểm tra độ phân giải ngay trên máy (từ kích thước ảnh), còn độ sáng/độ nét kiểm tra nhanh ở server
  **trước khi gọi AI** (không tốn chi phí AI). Web kiểm tra được cả độ sáng ngay trên trình duyệt (canvas).
- **Tương thích ngược:** cổng chặn ảnh kém (`quality_gate`) chỉ bật khi client mới gửi lên,
  để app cũ trên store (chưa biết trạng thái `low_quality`) không bị lỗi.
- **Phản hồi người dùng:** lưu vào bảng mới `diagnosis_feedback` (tạo bằng `create_all`, không sửa bảng cũ).
  Không lưu ảnh (tránh vấn đề dung lượng/quyền riêng tư) — chỉ lưu kết quả chẩn đoán và ý kiến.
- **Không thêm thư viện mới** cho cả backend, web và mobile.

## Checklist

### A. Backend
- [x] A1. Hàm đánh giá chất lượng ảnh (độ phân giải, độ sáng, độ nét) bằng Pillow
  — `assess_image_quality` trong `vlm.py`; test nhỏ/tối/cháy/mờ/ảnh thật OK trong `tests/test_us021.py`
- [x] A2. `/predict` nhận `quality_gate`; ảnh kém → trả `status: "low_quality"` mà không gọi AI
  — test xác nhận AI không bị gọi; tắt gate (app cũ) → hành vi cũ
- [x] A3. Khôi phục cache "ảnh gần giống" (Hamming distance) đã bị mất ở v2.5.8
  — test ảnh nén lại JPEG vẫn trúng cache, ảnh khác không trúng
- [x] A4. Sửa lỗi ưu tiên toán tử khi gắn nhãn ảnh (Ảnh 1/2/3) — `vlm.py` dòng ~341–349
- [x] A5. Bảng `diagnosis_feedback` + `POST /api/v1/feedback` (kiểm tra dữ liệu, giới hạn tần suất)
  — test: khách/đăng nhập/token hết hạn, lý do ngoài allow-list → 422, quá 20 lần/10 phút → 429
- [x] A6. API admin: danh sách phản hồi (lọc, phân trang), thống kê, đánh dấu đã rà soát + ghi chú chuyên gia
  — test: user thường → 403, SĐT bị che, id không tồn tại → 404, ghi chú > 2000 ký tự → 422

### B. Web (frontend)
- [x] B1. Tải 2 ảnh (vết bệnh + toàn cảnh) — E2E Playwright gửi đủ 2 file
- [x] B2. Lưu lựa chọn loại cây vào `localStorage` — E2E reload vẫn giữ; giá trị lạ bị bỏ qua
- [x] B3. Kiểm tra độ phân giải + độ sáng ngay trên trình duyệt trước khi gửi — E2E ảnh nhỏ/tối hiện cảnh báo
- [x] B4. Thẻ hỏi lại loại cây (clarification) — E2E chọn ứng viên + "Cây khác" nhập tay
- [x] B5. Thẻ cảnh báo ảnh kém (low_quality) với lựa chọn "Vẫn chẩn đoán" / "Chọn ảnh khác" — E2E cả 2 nút
- [x] B6. Nút 👍/👎 + hộp thoại lý do, gửi về server — E2E kiểm tra bản ghi trong DB, không có dialog
- [x] B7. Tab Admin "Phản hồi chẩn đoán" — E2E lọc + rà soát + ghi chú

### C. Mobile
- [x] C1. Camera trong app có khung ngắm (khung định vị + đường viền lá / vòng tròn / thân cây theo chế độ)
  — `SmartCamera.jsx` (expo-camera `CameraView`). ⚠️ Chỉ kiểm bằng bundle, **chưa chạy trên máy thật**
- [x] C2. Kiểm tra độ phân giải sau khi chụp/chọn ảnh — `acceptAsset` (< 300px → hỏi chọn lại)
- [x] C3. Xử lý `low_quality` (chụp lại / vẫn chẩn đoán) — `diagnose(true)` gửi `quality_gate=false`
- [x] C4. Hộp thoại phản hồi (thay `Alert.prompt` chỉ chạy trên iOS), gửi về server — `DiagnosisModals.jsx`
- [x] C5. Biên dịch thử bundle mobile thành công — `expo export -p android` và `-p ios` EXIT 0

### D. Benchmark
- [x] D1. Chế độ thật không bao giờ tự giả lập; ảnh thiếu → bỏ qua và báo rõ — `tests/test_benchmark.py`
- [x] D2. Chế độ thử (dry-run) ghi rõ "MÔ PHỎNG" và không ghi vào `docs/` — ghi vào `benchmark_data/reports/*_MO_PHONG.*`
- [x] D3. Cấp 4: tỷ lệ không đề xuất thuốc cấm + tỷ lệ trùng hoạt chất khuyến nghị — có test
- [x] D4. Đo cả luồng hỏi lại (tự trả lời bằng loại cây chuẩn) — có test, tắt bằng `--no-clarify`
- [x] D5. Thay báo cáo giả lập đã commit bằng ghi chú trung thực — `docs/BENCHMARK_REPORT.md`,
  kèm sửa `PROJECT.md`, `benchmark_data/README.md`, đính chính story/plan US-020

### E. Kiểm chứng
- [x] E1. Test tự động backend: `tests/test_us021.py` **70/70** (kèm ảnh thật), `tests/test_benchmark.py` **26/26**
- [x] E2. `npm run build` web — thành công
- [x] E3. Kiểm tra giao diện web trên trình duyệt — Playwright **40/40** (desktop + mobile viewport, không lỗi console)
- [x] E4. Bundle mobile (`expo export`) — Android + iOS EXIT 0

## Giới hạn còn lại (trung thực)
- UI mobile (camera, modal) **chưa được thử trên máy thật/giả lập** — cần test tay trước khi lên store.
- Ngưỡng độ mờ (< 50) mới hiệu chỉnh trên ảnh làm mờ nhân tạo — cần tinh chỉnh bằng ảnh thực địa.
- Benchmark chưa có ảnh thật → chưa có số đo độ chính xác.

## Bảo mật (Verification)
- Endpoint phản hồi công khai: kiểm tra kiểu/độ dài bằng Pydantic, danh sách lý do cố định (allow-list),
  giới hạn tần suất theo IP, ORM (không ghép chuỗi SQL).
- API admin dùng `require_admin` (kiểm tra quyền phía server).
- Dữ liệu người dùng hiển thị qua React/RN (tự escape), không dùng `dangerouslySetInnerHTML`.
- Web không dùng `alert()/prompt()` cho luồng mới.

## Rollback
- Bảng mới độc lập, có thể bỏ qua nếu cần. Tất cả trường mới trong API đều có giá trị mặc định.
