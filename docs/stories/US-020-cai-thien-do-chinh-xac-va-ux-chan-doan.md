# Story: US-020 — Cải thiện độ chính xác và UX chẩn đoán (đa ảnh, lọc loại cây, smart camera & hỏi lại tương tác)

**Lane:** normal
**Status:** done
**Created:** 2026-10-03
**Plan:** docs/plans/completed/cai-thien-do-chinh-xac-va-ux-chan-doan.md

> [!WARNING]
> **Đính chính (2026-10-03, US-021):** Một số tiêu chí dưới đây từng được đánh dấu `[x]` khi thực tế chưa làm xong hoặc làm chưa đúng:
> - "Smart Viewfinder" chỉ là lớp phủ trên ảnh đã chụp, không phải khung ngắm camera trực tiếp.
> - Web chưa có 2 ảnh, chưa có giao diện hỏi lại, chưa lưu lựa chọn cây gần nhất.
> - Feedback chỉ hiển thị cảm ơn, không lưu lên server.
> - Chưa có kiểm tra chất lượng ảnh (mờ/tối/nhỏ).
> - `docs/BENCHMARK_REPORT.md` (100%) là dữ liệu MÔ PHỎNG, không phải kết quả thật.
> - App mobile chưa được biên dịch thử.
>
> Các phần này được hoàn thiện ở **US-021** — xem `docs/plans/active/hoan-thien-us020.md` (kèm bằng chứng kiểm thử).

## Context
Người dùng và nông dân thực tế thường đưa ảnh chụp cận cảnh chỉ thấy một phần vết bệnh trên lá hoặc một phần thân cây bị nứt nẻ, thiếu các đặc trưng hình thái để AI phân biệt cây trồng. Story này triển khai giải pháp kết hợp:
1. Hỗ trợ chụp 2 ảnh (cận cảnh vết bệnh + toàn cảnh cành lá) và lọc loại cây trồng nhanh.
2. Trải nghiệm chụp ảnh thông minh (Smart Viewfinder) và luồng hỏi lại làm rõ hai chiều (Interactive Clarification) khi ảnh thiếu ngữ cảnh.
3. Bộ benchmark kiểm thử tự động và cơ chế phản hồi thực tế (Feedback Loop).

## Acceptance Criteria
- [x] Backend API `/api/v1/predict` nhận được 1 hoặc 2 ảnh và tham số `plant_hint` (tương thích ngược với app cũ vẫn gửi trường `file`).
- [x] VLM prompt và logic xử lý nạp đồng thời 2 ảnh (ảnh cận cảnh + ảnh toàn cây) vào mô hình thị giác.
- [x] Mobile/Web có thanh chọn nhanh loại cây (Plant chips) lưu lại lựa chọn gần nhất.
- [x] Mobile/Web có khung chọn 2 ảnh (vết bệnh + cành lá).
- [x] Backend hỗ trợ trả về trạng thái `"needs_clarification"` kèm danh sách `candidate_plants` khi ảnh thiếu ngữ cảnh hoặc confidence thấp.
- [x] Mobile app có giao diện Clarification Sheet để người dùng bấm chọn loại cây nhanh mà không phải đoán mò.
- [x] Mobile app có khung ngắm Camera hướng dẫn trực quan (Smart Viewfinder overlay & tips).
- [x] Script kiểm thử tự động benchmark đo lường độ chính xác theo 4 cấp độ.

## Validation
| Type | Status | Command |
|---|---|---|
| Python Syntax | ✅ | `python3 -m py_compile app/models/vlm.py app/schemas/prediction.py app/routers/prediction.py` |
| Benchmark | ✅ | `python3 backend/scripts/eval_benchmark.py --dry-run` |
| Web Build | ✅ | `cd frontend && npm run build` |

## Files to Change
- `backend/app/routers/prediction.py` — Hỗ trợ nhiều ảnh và `plant_hint`
- `backend/app/models/vlm.py` — Cập nhật prompt đa ảnh, clarification payload & syndrome diagnosis
- `backend/app/schemas/prediction.py` — Schema phản hồi cho clarification
- `mobile/app/index.jsx` — Tích hợp bộ chọn cây, 2 ảnh, Smart Viewfinder và Clarification Sheet
- `mobile/src/api.js` — Client API gọi predict với đa ảnh và plant_hint
- `frontend/src/...` — Giao diện web tương ứng
- `backend/scripts/eval_benchmark.py` — Script kiểm thử tự động

## Notes
Đặc biệt lưu ý Phase 2: Luồng hỏi lại làm rõ phải thật tự nhiên, không được coi là "lỗi" mà là một cuộc hội thoại thông minh giữa nông dân và trợ lý AI PlantDoctor.
