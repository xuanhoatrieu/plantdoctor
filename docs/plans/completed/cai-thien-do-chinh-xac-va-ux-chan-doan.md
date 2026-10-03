# Kế hoạch chi tiết: Cải thiện độ chính xác và Trải nghiệm chẩn đoán (PlantDoctor)

## Mục tiêu
Nâng cao độ chính xác chẩn đoán bệnh cây từ ảnh thực tế, khắc phục triệt để tình trạng ảnh thiếu ngữ cảnh (ảnh cận cảnh vết bệnh, ảnh thân cây, ảnh thiếu cành lá), đồng thời tạo ra trải nghiệm người dùng (UX) thông minh, tương tác hai chiều và quy trình đo lường định lượng chuẩn hóa cho Trường ĐH Nông Lâm Thái Nguyên.

## Phạm vi triển khai
- **Bao gồm:**
  - **Phase 1:** API & UI hỗ trợ tải 2 ảnh (cận cảnh + toàn cảnh), bộ lọc chọn nhanh loại cây trồng.
  - **Phase 2 (Trọng tâm):** Khung ngắm Camera thông minh (Smart Viewfinder) và luồng tương tác hỏi lại làm rõ hai chiều (Interactive Clarification Flow) khi ảnh thiếu thông tin.
  - **Phase 3:** Bộ dữ liệu kiểm thử Benchmark chuẩn hóa, script đo lường tự động và cơ chế phản hồi thực tế (Feedback Loop).
- **Không bao gồm:**
  - Can thiệp vào các module tài khoản, đăng nhập, thanh toán hoặc cơ sở dữ liệu thuốc BVTV đã ổn định.

---

## Danh sách công việc theo dõi tiến trình (Checklist)

### 📌 Giai đoạn 1: Nền tảng Đa ảnh & Thu hẹp không gian tìm kiếm (Multi-photo & Crop Filter)
- [x] **1.1. Backend API:** Cập nhật endpoint `/api/v1/predict` hỗ trợ nhận nhiều ảnh (`files: List[UploadFile]`) và tham số tùy chọn `plant_hint: Optional[str]`.
- [x] **1.2. Backend VLM Model:** Cập nhật `backend/app/models/vlm.py`:
  - [x] Nạp đồng thời mảng nhiều ảnh (`image_url`) trong 1 request gửi tới VLM (Ảnh 1: Cận cảnh vết bệnh, Ảnh 2: Toàn cảnh cành lá/toàn cây).
  - [x] Tích hợp `plant_hint` vào system prompt để thu hẹp không gian tìm kiếm bệnh cây khi người dùng đã chỉ định loại cây.
  - [x] Cập nhật cache pHash tương thích với nhiều ảnh hoặc kết hợp hint.
- [x] **1.3. UI Mobile & Web - Bộ chọn nhanh loại cây:**
  - [x] Thiết kế thanh cuộn ngang chứa danh mục cây chủ lực: `[Tất cả] [🍊 Cam/Bưởi] [🌾 Lúa] [🍵 Chè] [☕ Cà phê] [🌶️ Ớt/Cà chua] [🍈 Sầu riêng] [Cây khác...]`.
  - [x] Lưu lựa chọn gần nhất vào bộ nhớ máy (`AsyncStorage` / `localStorage`).
- [x] **1.4. UI Mobile & Web - Hỗ trợ chụp/tải 2 ảnh:**
  - [x] Khung chọn ảnh kép: Slot 1 (Bắt buộc): Vết bệnh cận cảnh; Slot 2 (Tùy chọn): Toàn cảnh cành lá.
  - [x] Xem trước 2 ảnh và nút xóa/chụp lại từng ảnh linh hoạt.

---

### 📌 Giai đoạn 2: Trải nghiệm Chụp ảnh Thông minh & Tương tác Làm rõ (TRỌNG TÂM CHI TIẾT)
> *Giai đoạn này tập trung xử lý triệt để bài toán: người dùng đưa ảnh chỉ chụp một phần lá hoặc thân cây khiến AI không đủ căn cứ kết luận.*

#### 2.1. Khung ngắm Camera Thông minh (Smart Viewfinder & Real-time Capture Guides)
- [x] **2.1.1. Giao diện khung ngắm chuẩn (Camera Overlay):**
  - [x] Thiết kế khung viền định vị (Target Box) và đường viền lá mờ (Leaf Silhouette) để hướng dẫn người dùng canh góc chụp.
  - [x] Hiển thị mẹo chụp trực quan (Tips Carousel):
    - *Tip 1: Chụp trọn vẹn cả phiến lá và cuống lá để nhận diện cây chính xác nhất.*
    - *Tip 2: Tránh để ngón tay che khuất bề mặt lá.*
    - *Tip 3: Đảm bảo đủ ánh sáng, tránh bóng râm đổ trực tiếp lên vết bệnh.*
- [x] **2.1.2. Chuyển đổi chế độ chụp nhanh (Capture Mode Switcher):**
  - [x] Tab chọn chế độ: `[Lá cây toàn thể]` | `[Vết bệnh cận cảnh]` | `[Thân / Cành / Quả]`.
  - [x] Khi chuyển sang `[Vết bệnh cận cảnh]`: Tự động hiện gợi ý nhỏ: *"💡 Khuyên dùng: Chụp thêm ảnh cành lá để AI không bị nhầm lẫn loại cây."*
- [x] **2.1.3. Kiểm tra chất lượng ảnh sơ bộ (Client-side Check):**
  - [x] Kiểm tra kích thước ảnh hợp lệ (tránh ảnh bị vỡ hoặc độ phân giải quá thấp < 300px).
  - [x] Cảnh báo nếu ảnh có độ sáng quá tối trước khi gửi lên máy chủ.

#### 2.2. Cơ chế Tương tác Làm rõ Hai chiều (Interactive Clarification / Multi-turn Flow)
- [x] **2.2.1. Giao thức Backend (Clarification Response Protocol):**
  - [x] Khi VLM phát hiện ảnh thiếu ngữ cảnh hoặc confidence < 70% hoặc có nhiều ứng viên `plant_candidates`:
    - Trả về status: `"needs_clarification"` thay vì trả kết quả đoán mò.
    - Trả về danh sách gợi ý: `candidate_plants: [{"id": "citrus", "name": "Cam / Bưởi"}, {"id": "coffee", "name": "Cà phê"}, ...]`.
    - Trả về mô tả triệu chứng sơ bộ: `preliminary_symptoms: "Vết đốm nâu hoại tử viền vàng"`.
- [x] **2.2.2. Endpoint xác nhận làm rõ (`/api/v1/predict/clarify`):**
  - [x] Cho phép client gửi lựa chọn loại cây từ danh sách gợi ý (hoặc tải thêm ảnh thứ 2) để nhận ngay kết quả chẩn đoán chính thức mà không cần phân tích lại từ đầu.
- [x] **2.2.3. Giao diện Mobile & Web (Clarification Sheet / Modal):**
  - [x] Thiết kế hộp thoại thân thiện dạng trợ lý ảo:
    - 🤖 *"Tôi thấy rõ vết bệnh (đốm hoại tử viền vàng), nhưng do ảnh chụp cận cảnh nên chưa thấy dáng lá. Bạn đang trồng cây nào trong các cây dưới đây?"*
    - Các nút bấm chọn nhanh trực quan với icon sinh động.
    - Tùy chọn `[📸 Chụp thêm ảnh cành lá]` để bổ sung ngữ cảnh.
- [x] **2.2.4. Chẩn đoán Hội chứng Thân cây (Syndrome-level Diagnosis):**
  - [x] Khi người dùng chỉ chụp vỏ thân nứt / xì mủ / thối thân mà không rõ loại cây:
    - Định dạng kết quả theo **Hội chứng bệnh học** (ví dụ: *"Hội chứng xì mủ nứt thân do nấm"*).
    - Cung cấp biện pháp xử lý cơ học và thuốc trừ nấm phổ rộng an toàn, kèm khuyến cáo chụp thêm ảnh lá khi có thể.

---

### 📌 Giai đoạn 3: Đo lường Chuẩn hóa & Vòng lặp Phản hồi Thực tế (Benchmark & Feedback Loop)
- [x] **3.1. Bộ dữ liệu Benchmark chuẩn (Gold Standard Dataset):**
  - [x] Chuẩn bị cấu trúc thư mục `benchmark_data/` gồm các ảnh thực tế đã được giảng viên/chuyên gia ĐH Nông Lâm Thái Nguyên dán nhãn chuẩn (`ground_truth.json`).
  - [x] Phân loại theo 3 nhóm: Ảnh chuẩn, Ảnh đồng ruộng thực tế, Ảnh cận cảnh/thiếu ngữ cảnh.
- [x] **3.2. Script kiểm thử tự động (`backend/scripts/eval_benchmark.py`):**
  - [x] Chạy tự động toàn bộ ảnh qua pipeline AI.
  - [x] Đo lường các chỉ số:
    - Cấp 1: Độ chính xác nhận diện cây (Plant Accuracy %).
    - Cấp 2: Tỷ lệ phát hiện bệnh đúng (Recall/Sensitivity %).
    - Cấp 3: Độ chính xác chủng bệnh cụ thể (Top-1 & Top-3 Accuracy %).
    - Cấp 4: Đánh giá thời gian phản hồi (Latency) và tỷ lệ thuốc BVTV hợp lệ.
  - [x] Xuất báo cáo tổng kết tự động dạng Markdown/HTML.
- [x] **3.3. Vòng lặp phản hồi người dùng thực tế (User Feedback Loop):**
  - [x] Thêm nút đánh giá 👍 / 👎 ở màn hình kết quả chẩn đoán.
  - [x] Cho phép người dùng phản ánh nếu kết quả chưa đúng (ví dụ: *"Sai cây"*, *"Sai bệnh"*, *"Cây của tôi là..."*).

---

## Trình tự triển khai chi tiết từng bước (Execution Roadmap)

```text
[BƯỚC 1] Triển khai Backend đa ảnh + plant_hint (Phase 1.1 + 1.2)
   ↓
[BƯỚC 2] Triển khai UI Bộ chọn loại cây & Upload 2 ảnh trên Web + Mobile (Phase 1.3 + 1.4)
   ↓
[BƯỚC 3] Xây dựng Backend Clarification Protocol & Syndrome diagnosis (Phase 2.2.1 + 2.2.2 + 2.2.4)
   ↓
[BƯỚC 4] Xây dựng Giao diện Clarification Sheet & Smart Viewfinder trên Mobile (Phase 2.1 + 2.2.3)
   ↓
[BƯỚC 5] Viết script Benchmark kiểm thử tự động & Tích hợp Feedback Loop (Phase 3.1 + 3.2 + 3.3)
```

## Tiêu chí hoàn thành (Definition of Done)
1. Backend xử lý tốt cả 1 ảnh lẫn 2 ảnh (cận cảnh + toàn thể), phản hồi đúng khi có `plant_hint`.
2. Khi người dùng đưa ảnh cận cảnh thiếu thông tin lá:
   - Hệ thống không đoán bừa.
   - Hiện hộp thoại hỏi lại thân thiện với các ứng viên cây trồng phù hợp.
   - Nhận diện chính xác ngay sau khi người dùng xác nhận loại cây hoặc bổ sung ảnh.
3. Mobile app có khung ngắm hỗ trợ chụp ảnh chuẩn, trải nghiệm mượt mà, không giật lag.
4. Có script kiểm thử benchmark đánh giá định lượng được điểm độ chính xác.
