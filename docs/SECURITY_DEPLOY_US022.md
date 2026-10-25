# Hướng dẫn deploy bản vá bảo mật (US-022)

> [!CAUTION]
> Bản này **không khởi động được** nếu server production chưa có `SECRET_KEY` hợp lệ.
> Làm đủ **Bước 1 → 2** TRƯỚC khi kéo image mới, nếu không web sẽ ngừng chạy.
> GitHub Actions chỉ build image khi push tag, không tự deploy. Nhưng nếu server có công cụ tự kéo image
> (ví dụ watchtower), hãy làm Bước 1 **trước khi push tag**.

## Bước 1 — Kiểm tra SECRET_KEY hiện tại trên server (chỉ đọc, không in giá trị)

```bash
cd <thư mục chứa docker-compose.prod.yml>
docker exec benhcay-api sh -c 'v="$SECRET_KEY"; if [ -z "$v" ]; then echo RONG; elif [ "$v" = "plantdoctor-secret-key-change-in-production" ] || [ "$v" = "dev-secret-key" ]; then echo MAC_DINH; else echo "OK (${#v} ky tu)"; fi'
```

| Kết quả | Việc cần làm |
|---|---|
| `OK (...)` | **Giữ nguyên** SECRET_KEY, sang Bước 2. Người dùng không bị đăng xuất. |
| `RONG` hoặc `MAC_DINH` | Tạo khoá mới (bên dưới). Mọi người sẽ phải **đăng nhập lại một lần**; mật khẩu cũ vẫn dùng được. |

Tạo khoá mới và ghi vào file `.env` cạnh `docker-compose.prod.yml`:

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
chmod 600 .env
```

> [!NOTE]
> Mật khẩu cũ được băm kèm SECRET_KEY cũ. Code mới tự thử với giá trị rỗng và chuỗi mặc định cũ,
> nên trường hợp `RONG` / `MAC_DINH` không cần làm gì thêm. Chỉ khi bạn **đổi một SECRET_KEY thật
> đang dùng** sang giá trị khác thì mới phải thêm `LEGACY_SECRET_KEY=<giá trị cũ>` vào `.env`.

## Bước 2 — Kiểm tra kết nối AI (key không còn nằm trong code)

Vào web **Admin → ⚙️ Cấu hình AI Model**. Nếu ô *API URL* và *API Key* đã có giá trị (key hiển thị dạng `abcd••••wxyz`)
thì không cần làm gì: cấu hình đã lưu trong database. Nếu đang trống, điền ở đây **hoặc** thêm vào `.env`:

```
LLM_API_URL=http://<địa-chỉ-cliproxy>:8317/v1/chat/completions
LLM_API_KEY=<key>
```

## Bước 3 — Deploy

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker logs --tail 50 benhcay-api
```

Nếu thiếu SECRET_KEY, `docker compose` sẽ báo `SECRET_KEY must be set in the server .env file` và **không** dừng container cũ.

## Bước 4 — Việc bắt buộc ngay sau deploy

1. **Đổi mật khẩu admin.** Mật khẩu cũ `Hoa@123` đã nằm công khai trong lịch sử git. Nếu log có dòng
   `CRITICAL ... still uses the old public default password` thì nghĩa là chưa đổi. Đổi bằng một trong các cách:
   - Mobile: Hồ sơ → Đổi mật khẩu
   - Web: Admin → Người dùng → Đặt lại mật khẩu (cho chính tài khoản của bạn)
   - Server: `docker exec -it benhcay-api python make_admin.py 0944550007 --password` (nhập mật khẩu ẩn)
2. **Đổi API key của cliproxy.** Key cũ đã nằm trong lịch sử git nên coi như đã lộ. Tạo key mới bên cliproxy,
   rồi cập nhật trong Admin → Cấu hình AI Model.
3. **Tạo tài khoản demo riêng (không phải admin) cho Apple reviewer** và nhập trong App Store Connect.

## Bước 5 — Kiểm tra nhanh

```bash
curl -s https://benhcay.tuaf.edu.vn/api/v1/health                                   # {"status":"ok",...}
curl -s -o /dev/null -D - -H "Origin: https://evil.example" https://benhcay.tuaf.edu.vn/api/v1/health | grep -i access-control || echo "CORS chặn origin lạ: OK"
```

Sau đó thử trên app mobile: đăng nhập, chẩn đoán một ảnh, gửi phản hồi.

## Khuyến nghị hạ tầng (không bắt buộc cho bản này)

- Cổng `8317` của cliproxy đang mở ra Internet và dùng HTTP. Nên đưa cliproxy vào mạng Docker `tuaf-ai-network`
  rồi dùng `http://<tên-container>:8317/...`, sau đó đóng cổng 8317 trên firewall.
- Ngưỡng rate limit mặc định: 40 lượt chẩn đoán / 10 phút / tài khoản, 60 / 10 phút / IP khách.
  Nếu một lớp học dùng chung wifi bị chặn, tăng `PREDICT_RATE_LIMIT_GUEST` trong `.env`.

## Rollback

Có thể quay về image cũ, nhưng những người **đã đăng nhập trên bản mới** sẽ có mật khẩu băm kiểu scrypt
mà bản cũ không đọc được → admin cần đặt lại mật khẩu cho họ. Vì vậy nên rollback sớm (trong vài giờ đầu) nếu cần.
