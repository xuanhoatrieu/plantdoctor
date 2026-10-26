# Lộ trình Mở rộng Kho Tri thức & Hình ảnh Bệnh cây (PlantDoctor Knowledge Base Roadmap)

Tài liệu này lưu trữ danh sách các nguồn dữ liệu bệnh học thực vật uy tín quốc tế và Việt Nam đã được khảo sát để tích hợp theo từng giai đoạn vào hệ thống **PlantDoctor (`benhcay.tuaf.edu.vn`)**.

---

## Giai đoạn 1 (Đang triển khai): CABI PlantwisePlus Vietnam + VAAS/PPRI + Ảnh thực địa chuẩn
- **Nguồn chính**:
  - **CABI PlantwisePlus Knowledge Bank Vietnam** (`https://plantwiseplusknowledgebank.org`): Các tài liệu *Pest Management Decision Guides (PMDG)* và *Factsheets for Farmers (FFF)* biên soạn riêng cho Việt Nam (phối hợp cùng Cục BVTV, PPRI, SOFRI, Chi cục BVTV các tỉnh).
  - **Danh mục thuốc BVTV hợp pháp tại Việt Nam** (`pesticides.json` — Thông tư 75/2025/TT-BNNPTNT).
  - **iNaturalist Research-Grade Taxa API (`https://api.inaturalist.org/v1/taxa`) & Wikimedia Commons**: Truy xuất ảnh chụp thực địa đã được xác thực sinh học theo tên khoa học (`scientific_name`) của từng tác nhân gây hại.
- **Đặc điểm cấu trúc**:
  - Bao phủ các nhóm cây trồng chủ lực Việt Nam: Chè, Cam/Bưởi/Chanh/Quýt, Lúa, Ngô, Cà phê, Hồ tiêu, Ớt, Sầu riêng, Cà chua, Khoai tây, Chuối, Nhãn/Vải, Xoài, Thanh long, Bắp cải/Rau họ thập tự, Lạc/Đậu tương, Sắn.
  - Áp dụng nguyên tắc **IPM Đèn giao thông của CABI**:
    - **Phòng ngừa & Kiểm soát Xanh (Green Control)**: Canh tác, cắt tỉa, giống kháng, thiên địch, chế phẩm sinh học (*Trichoderma*, *Bacillus subtilis*, *Beauveria*, dầu khoáng...).
    - **Kiểm soát Vàng (Yellow Control)**: Hoạt chất hóa học đặc hiệu được phép sử dụng tại Việt Nam, đối chiếu tự động sang sản phẩm thương phẩm.

---

## Giai đoạn 2 (Đã lưu bộ nhớ để triển khai tiếp theo)

### 1. PlantPAD (`https://plantpad.samlab.cn`)
- **Quy mô**: 421.314 ảnh, 63 loài cây trồng, 310 bệnh cây, 121 thuộc tính hình thái vết bệnh (*Nucleic Acids Research / Nature*, 2024).
- **Mục tiêu tích hợp**: Lấy bảng ma trận **121 thuộc tính hình thái** (màu sắc đốm, hình dạng viền, cấu trúc bề mặt, vị trí phân bố trên lá/thân/quả) để nâng cấp bộ chấm điểm `kb_matcher` theo thuộc tính thị giác.

### 2. `enalis/LeafNet` & `LeafBench` (`https://huggingface.co/datasets/enalis/LeafNet`)
- **Quy mô**: 186.000 ảnh lá bệnh trên 22 cây trồng, 97 lớp bệnh chi tiết kèm mô tả triệu chứng bệnh học chuẩn và bộ câu hỏi VQA (`LeafBench`).
- **Mục tiêu tích hợp**: Trích xuất bộ ảnh mẫu đại diện (3–5 ảnh/bệnh) để làm **Visual Few-Shot RAG** (so sánh vector ảnh bằng BioCLIP / DINOv2).

### 3. EPPO Global Database (`https://gd.eppo.int` & `https://data.eppo.int`)
- **Quy mô**: 97.800+ loài dịch hại và cây ký chủ, có REST API miễn phí theo mã chuẩn quốc tế **EPPO Code** (6 ký tự, ví dụ `EXOBVE`, `XANTCI`, `PYRIOR`).
- **Mục tiêu tích hợp**: Chuẩn hóa mã định danh quốc tế EPPO Code cho từng bệnh trong bảng `diseases` và tự động đồng bộ danh sách cây ký chủ + ảnh kiểm dịch thực vật.

### 4. Bugwood / IPM Images (`https://www.ipmimages.org`)
- **Quy mô**: 320.000+ ảnh bệnh cây và côn trùng của Đại học Georgia & USDA (Creative Commons).
- **Mục tiêu tích hợp**: Bổ sung bộ sưu tập ảnh theo từng giai đoạn bệnh (sớm / trung bình / nặng) và bộ phận bị hại.

### 5. IRRI Rice Knowledge Bank (`http://www.knowledgebank.irri.org`)
- **Quy mô**: Ngân hàng kiến thức chuyên sâu về cây lúa tại Đông Nam Á.
- **Mục tiêu tích hợp**: Bổ sung đầy đủ bộ chẩn đoán **Thiếu hụt dinh dưỡng & Ngộ độc sinh lý trên lúa** (Thiếu Đạm, Lân, Kali, Kẽm, Silic, Ngộ độc phèn, Ngộ độc hữu cơ/nghẹt rễ).

### 6. `FieldPlant` & `IP102` (Hugging Face / Kaggle)
- **Quy mô**: 5.170 ảnh bệnh cây nhiệt đới ngoài đồng (`FieldPlant`) + 75.000 ảnh của 102 loài sâu hại nông nghiệp (`IP102`).
- **Mục tiêu tích hợp**: Tăng cường kho ảnh mẫu nhận diện sâu hại (rầy, bọ xít, sâu đục quả, sâu keo, bọ trĩ, nhện).
