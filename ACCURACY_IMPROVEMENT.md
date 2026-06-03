# Nâng cao độ chính xác & tính nhất quán của LLM trong chẩn đoán bệnh cây

> Tài liệu thảo luận nội bộ — LeafDoctor Project  
> Ngày: 29/05/2026

---

## 1. Vấn đề hiện tại

- Sử dụng GPT-5.5 Vision API với prompt đơn giản, temperature=0
- Mỗi lần gọi API cho cùng 1 ảnh có thể cho kết quả khác nhau (tên bệnh, confidence, mô tả)
- Không có cơ chế kiểm chứng hoặc ràng buộc output

---

## 2. Nâng cao độ chính xác dự đoán

### 2.1. Cải thiện Prompt Engineering

**Chain-of-Thought (CoT):**
- Yêu cầu model suy luận từng bước: quan sát màu sắc lá → hình dạng vết bệnh → vị trí tổn thương → kết luận
- Giảm hallucination vì model phải "giải thích" trước khi kết luận

**Few-shot examples:**
- Đưa 2-3 ví dụ mẫu (mô tả triệu chứng + output JSON mong muốn) vào prompt
- "Neo" model vào format và mức độ chi tiết cần thiết

**Constrained output space:**
- Cung cấp danh sách bệnh cụ thể mà model được phép chọn (thay vì để tự nghĩ ra tên)
- Ví dụ: "Chỉ chọn từ danh sách: [Apple Scab, Black Rot, Powdery Mildew, ...]"
- Nghiên cứu (arxiv 2605.09768) cho thấy VLM gặp khó khăn với fine-grained disease identification khi thiếu structured crop-specific knowledge

**Yêu cầu visual evidence trước kết luận:**
- Bắt model liệt kê triệu chứng nhìn thấy (vết nâu, viền vàng, nấm trắng...) rồi mới map sang bệnh
- Giảm "đoán mò", tăng traceability

### 2.2. Hybrid approach: LLM + CNN

Nghiên cứu (arxiv 2504.20419) cho thấy kết hợp GPT-4o fine-tuned với ResNet-50 đạt **98.12% accuracy** trên apple leaf images.

Cách tiếp cận đề xuất:
1. Dùng CNN (ResNet50/MobileNetV2) cho classification → ra top-3 candidates
2. Dùng VLM để verify và mô tả chi tiết dựa trên candidates từ CNN
3. CNN cho confidence score ổn định, VLM cho mô tả/treatment chất lượng

**Ưu điểm:** Accuracy cao nhất, confidence ổn định  
**Nhược điểm:** Cần GPU, tăng complexity

### 2.3. RAG (Retrieval-Augmented Generation)

Thay vì để LLM tự nhớ kiến thức bệnh cây:
- Xây database triệu chứng bệnh (đã có `diseases.json`)
- Sau khi LLM nhận diện sơ bộ → retrieve thông tin chi tiết từ DB → đưa vào prompt để LLM xác nhận/điều chỉnh
- Giảm hallucination vì model có "ground truth" để đối chiếu

### 2.4. Image preprocessing

- Crop vùng lá bị bệnh (focus vào lesion thay vì toàn bộ ảnh)
- Chuẩn hóa ánh sáng, loại bỏ background
- Resize về kích thước tối ưu (không quá nhỏ mất chi tiết, không quá lớn tốn token)

---

## 3. Giảm thiểu sự không nhất quán giữa các lần gọi

### 3.1. Bản chất vấn đề

Đây là vấn đề **inherent** của LLM:
- Ngay cả temperature=0 + seed cố định vẫn không đảm bảo 100% deterministic
- OpenAI thừa nhận: model update (system_fingerprint thay đổi) có thể thay đổi output
- Với long-form output, variability có thể lên tới 50% giữa các lần gọi

### 3.2. Tham số inference

| Tham số | Hiện tại | Khuyến nghị | Ghi chú |
|---------|----------|-------------|---------|
| `temperature` | 0 | 0 (giữ nguyên) | Đã tối ưu |
| `top_p` | mặc định | Không set (redundant khi temp=0) | |
| `seed` | **không set** | **Thêm seed cố định (vd: 42)** | Giảm variance ngắn hạn |
| `max_tokens` | 500 | 500 (giữ nguyên) | |

### 3.3. Self-Consistency Decoding (Majority Voting)

Kỹ thuật mạnh nhất để giảm variance:

```
Gọi LLM 3 lần (temperature=0.3) cho cùng 1 ảnh
    ↓
Majority vote trên tên bệnh
    ↓
Trung bình confidence
    ↓
Chọn description/treatment từ lần có confidence cao nhất
```

- Nghiên cứu cho thấy self-consistency giảm error rate theo hàm mũ khi tăng số samples
- 3 lần gọi là sweet spot giữa chi phí và độ ổn định
- Có thể chạy parallel để giảm latency

**Trade-off:** Tốn 3x API cost, tăng latency ~2-3s nếu chạy parallel

### 3.4. Constrained Output Format

Giảm output space = giảm variance:
- Cung cấp enum cố định các bệnh (không cho model tự đặt tên)
- Confidence phải là bội số 5 (80, 85, 90...)
- Severity chỉ 4 giá trị: nhẹ/trung bình/nặng/không

### 3.5. Caching

- **Perceptual hash** ảnh (pHash) → nếu ảnh giống/gần giống → trả kết quả cached
- Đảm bảo cùng ảnh = cùng kết quả 100%
- Giảm chi phí API

### 3.6. Post-processing normalization

Sau khi nhận output từ LLM:
- Fuzzy match tên bệnh vào danh sách chuẩn
- Clamp confidence vào các mức cố định
- Map severity về đúng 4 giá trị cho phép

---

## 4. Đề xuất ưu tiên triển khai

| # | Giải pháp | Effort | Impact (Accuracy) | Impact (Consistency) |
|---|-----------|--------|-------------------|---------------------|
| 1 | Thêm `seed` parameter | Cực thấp | — | ⭐⭐⭐ |
| 2 | Danh sách bệnh cố định trong prompt | Thấp | ⭐⭐⭐ | ⭐⭐⭐ |
| 3 | CoT reasoning trong prompt | Thấp | ⭐⭐⭐ | ⭐⭐ |
| 4 | Image hash caching | Trung bình | — | ⭐⭐⭐⭐⭐ |
| 5 | Self-consistency (3x voting) | Trung bình | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 6 | Hybrid CNN + VLM | Cao | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### Lộ trình đề xuất

**Phase 1 (ngay lập tức):** Giải pháp 1 + 2 + 3 — chỉ cần sửa prompt và thêm seed  
**Phase 2 (1-2 tuần):** Giải pháp 4 + 5 — caching + majority voting  
**Phase 3 (dài hạn):** Giải pháp 6 — hybrid CNN nếu có GPU server

---

## 5. Tham khảo

- [Plant Disease Detection through Multimodal LLMs and CNNs](https://arxiv.org/abs/2504.20419) — GPT-4o + ResNet50 đạt 98.12%
- [Scalable Agentic Grounded Evaluation for Crop Disease Diagnosis](https://arxiv.org/html/2605.09768v1) — VLM cần structured knowledge
- [Self-Consistency Decoding](https://www.emergentmind.com/topics/self-consistency-sc-decoding) — Majority voting giảm variance
- [OpenAI Community: Deterministic Outputs](https://community.openai.com/t/ensuring-consistent-output-with-gpt-4o-2024-08-06-temperature-set-to-0/1006897) — Giới hạn của temp=0
- [Test-Time Consistency in VLMs](https://arxiv.org/html/2506.22395v1) — Cross-Entropy Agreement Loss
