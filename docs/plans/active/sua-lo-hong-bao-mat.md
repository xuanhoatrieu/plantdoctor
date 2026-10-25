# Kế hoạch: Sửa các lỗ hổng bảo mật backend (Story US-022)

**Lane:** high-risk (đụng tới đăng nhập, mật khẩu, cấu hình production)

## Bối cảnh
Trong lúc làm US-021 phát hiện 7 vấn đề bảo mật/độ chính xác có sẵn từ trước. Kế hoạch này sửa toàn bộ,
**không thêm thư viện mới** và **không làm người dùng hiện tại mất khả năng đăng nhập**.

## Quyết định thiết kế
- **Băm mật khẩu:** `hashlib.scrypt` có sẵn trong Python (memory-hard, OWASP khuyến nghị; tham số
  N=2^14, r=8, p=5 ≈ 16 MiB). `bcrypt` có trong venv dev nhưng KHÔNG có trong `requirements.txt`/Docker → không dùng.
- **Chuyển đổi dần:** hash sha256 cũ vẫn đăng nhập được; khi đăng nhập thành công sẽ tự băm lại bằng scrypt.
  Hash cũ được thử với: `SECRET_KEY` hiện tại, `LEGACY_SECRET_KEY` (nếu có), chuỗi mặc định cũ và chuỗi rỗng
  (docker-compose truyền `${SECRET_KEY}` rỗng nếu server chưa đặt biến).
- **SECRET_KEY:** thiếu / rỗng / trùng chuỗi mặc định công khai → **từ chối khởi động** (fail closed).
  Chỉ môi trường test/dev được phép dùng khoá ngẫu nhiên tạm thời qua `ALLOW_EPHEMERAL_SECRET=1`.
- **Admin:** không bao giờ ghi đè mật khẩu khi khởi động. Chỉ tạo admin khi đặt `ADMIN_PHONE` + `ADMIN_PASSWORD`.
  Cảnh báo CRITICAL nếu admin vẫn dùng mật khẩu mặc định cũ.
- **LLM key:** bỏ khỏi code. Thứ tự lấy cấu hình: Admin Settings (DB) → biến môi trường `LLM_*`.
  DB production đã có sẵn key (được seed từ trước) → không gián đoạn.
- **CORS:** chỉ cho phép tên miền TUAF + localhost (dev) + `CORS_ORIGINS`; tắt `allow_credentials`
  (web/mobile dùng header Bearer, không dùng cookie).
- **Rate limit `/predict` + `/predict/clarify`:** cửa sổ trượt trong bộ nhớ; theo tài khoản nếu đăng nhập,
  theo IP nếu là khách; ngưỡng chỉnh bằng biến môi trường. Trả 429 + `Retry-After`.
- **`lead`:** so khớp theo ranh giới từ thay vì chuỗi con.

## Checklist
- [x] S1. Mật khẩu admin không bị reset khi khởi động; `make_admin.py` không còn mật khẩu mặc định
  — test: init_db 3 lần không đổi hash; không tự tạo/tự cấp quyền 0944550007; ADMIN_PASSWORD < 8 → không tạo
- [x] S2. `SECRET_KEY` fail-closed; JWT bắt buộc `exp`, chỉ HS256
  — test + chạy thật: thiếu/rỗng/mặc định → exit 1; token ký bằng khoá mặc định, `alg=none`, thiếu exp, HS512 → 401
- [x] S3. Bỏ LLM URL/key khỏi code (vlm.py, admin.py, models.py, AdminView.jsx, tài liệu); Gemini key qua header
  — test quét mã nguồn backend/web/mobile: 0 chỗ; bundle web build: 0 chỗ; DB > env; key Gemini không nằm trong URL
- [x] S4. scrypt + tự nâng cấp hash cũ khi đăng nhập
  — test + chạy thật: hash cũ (salt mặc định/rỗng/hiện tại) đăng nhập 200 → hash thành `scrypt$`
- [x] S5. CORS chặt + header bảo mật cơ bản cho API
  — test: origin lạ / look-alike / preflight lạ không nhận ACAO; không có Allow-Credentials; nosniff, DENY, no-store
- [x] S6. Rate limit `/predict` và `/predict/clarify`
  — test: khách 3→429 + Retry-After, AI không bị gọi; IP khác riêng; XFF giả mạo bên trái không lách được;
    tài khoản bị giới hạn kể cả đổi IP; token hỏng = khách; clarify dùng chung ngưỡng
- [x] S7. So khớp thuốc cấm theo ranh giới từ — test 7 ca bị cấm + 6 ca hợp lệ
- [x] V1. `tests/test_security.py` **90/90**
- [x] V2. `test_us021.py` **70/70** (ảnh thật), `test_benchmark.py` **26/26**, `npm run build` OK
- [x] V3. Chạy uvicorn thật (127.0.0.1, DB tạm): khởi động OK, cảnh báo CRITICAL mật khẩu cũ, đăng nhập hash cũ 200
- [x] V4. `docs/SECURITY_DEPLOY_US022.md`

## Phát hiện thêm — CHƯA sửa (cần quyết định)
- **Đăng nhập Apple không xác minh chữ ký token** (`auth_router.py`, đã gắn `TODO(security)`): ai cũng có thể giả token
  để đăng nhập vào tài khoản Apple của người khác. Sửa cần thư viện `cryptography` (RS256) → thêm dependency.
- Chính sách mật khẩu tối thiểu 6 ký tự (đồng bộ với app) — nên nâng lên 8 cùng lúc với app mobile/web.
- `DATABASE_URL` lỗi kết nối thì backend lặng lẽ chuyển sang SQLite (`database/models.py`) — nên báo lỗi thay vì chuyển.

## Bảo mật (Verification)
- Negative: token ký bằng khoá rỗng/mặc định/`alg=none`/thiếu `exp` → 401.
- Negative: origin lạ không nhận header CORS; không có `Access-Control-Allow-Credentials`.
- Negative: vượt ngưỡng `/predict` → 429, AI không bị gọi.
- Negative: khởi động lại không đổi mật khẩu admin; `ADMIN_PHONE` không tự cấp quyền khi không được đặt.
- Không log mật khẩu, token hay API key.

## Rollback
- Hash scrypt mới không đọc được bởi code cũ → nếu rollback image, người đã đăng nhập sau khi nâng cấp
  sẽ phải được admin đặt lại mật khẩu. (Ghi rõ trong hướng dẫn deploy.)
