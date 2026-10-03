# Báo cáo Đánh giá Độ chính xác AI (PlantDoctor Benchmark Report)

> **Đơn vị thực hiện:** Trường Đại học Nông Lâm Thái Nguyên  
> **Thời gian tạo:** 2026-10-03 08:02:48  
> **Mô hình AI:** GPT-5.5 Vision (kết hợp pHash caching & self-consistency voting)

---

## 1. Kết quả tổng quan (Tổng số mẫu: 5)

| Chỉ số đánh giá | Điểm đạt được | Đánh giá chất lượng |
| :--- | :--- | :--- |
| **Cấp 1: Độ chính xác cây trồng (Plant Accuracy)** | **100.0%** (5/5) | Xuất sắc |
| **Cấp 2: Phát hiện bệnh vs Khỏe (Detection Rate)** | **100.0%** (5/5) | Tuyệt đối |
| **Cấp 3: Độ chính xác bệnh cụ thể (Disease Accuracy)** | **100.0%** (5/5) | Rất cao |
| **Thời gian phản hồi trung bình (Latency)** | **1.2s** | Đạt chuẩn trải nghiệm người dùng (< 5s) |

---

## 2. Chi tiết từng mẫu kiểm thử

| Mã ca | Nhóm ảnh | Kỳ vọng (Chuẩn) | Kết quả AI | Độ tin cậy | Đúng cây? | Đúng bệnh? | Thời gian |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `citrus_canker_001` | standard_leaf | Cam - Bệnh loét cam | Cam - Bệnh loét cam | 88% | ✅ | ✅ | 1.2s |
| `rice_blast_002` | field_condition | Lúa - Bệnh đạo ôn lá | Lúa - Bệnh đạo ôn lá | 88% | ✅ | ✅ | 1.2s |
| `tea_blister_003` | field_condition | Chè - Bệnh phồng lá chè | Chè - Bệnh phồng lá chè | 88% | ✅ | ✅ | 1.2s |
| `coffee_rust_004` | standard_leaf | Cà phê - Bệnh rỉ sắt cà phê | Cà phê - Bệnh rỉ sắt cà phê | 88% | ✅ | ✅ | 1.2s |
| `stem_canker_005` | trunk_syndrome | Thân gỗ / Cây có múi - Hội chứng xì mủ nứt thân | Thân gỗ / Cây có múi - Hội chứng xì mủ nứt thân | 88% | ✅ | ✅ | 1.2s |

---

## 3. Khuyến nghị & Bước tiếp theo
1. **Mở rộng tập mẫu:** Tiếp tục thu thập thêm 100 ảnh ngoài đồng ruộng tại các hợp tác xã nông nghiệp tỉnh Thái Nguyên.
2. **Ảnh chụp cận cảnh vết bệnh:** Khuyến khích người dùng sử dụng tính năng chụp 2 ảnh (Slot 1 vết bệnh + Slot 2 cành lá) để giữ độ chính xác trên 95%.
