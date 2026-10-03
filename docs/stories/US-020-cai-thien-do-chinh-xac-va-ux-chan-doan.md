# Story: US-020 — Cải thiện độ chính xác và UX chẩn đoán (đa ảnh, lọc loại cây, smart camera & hỏi lại tương tác)

**Lane:** normal
**Status:** done
**Created:** 2026-10-03
**Plan:** docs/plans/active/cai-thien-do-chinh-xac-va-ux-chan-doan.md

## Context
Người dùng và nông dân thực tế thường đưa ảnh chụp cận cảnh chỉ thấy một phần vết bệnh trên lá hoặc một phần thân cây bị nứt nẻ, thiếu các đặc trưng hình thái để AI phân biệt cây trồng. Story này triển khai giải pháp kết hợp:
1. Hỗ trợ chụp 2 ảnh (cận cảnh vết bệnh + toàn cảnh cành lá) và lọc loại cây trồng nhanh.
2. Trải nghiệm chụp ảnh thông minh (Smart Viewfinder) và luồng hỏi lại làm rõ hai chiều (Interactive Clarification) khi ảnh thiếu ngữ cảnh.
3. Bộ benchmark kiểm thử tự động và cơ chế phản hồi thực tế (Feedback Loop).

## Acceptance Criteria
- [x] Backend API `/api/v1/predict` nhận được 1 hoặc 2 ảnh và tham số `plant_hint` (tương thích ngược 100%).
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
