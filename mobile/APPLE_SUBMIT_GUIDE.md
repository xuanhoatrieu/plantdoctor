# Hướng dẫn Submit PlantDoctor lên Apple App Store

> Từng bước chi tiết — Cập nhật 30/05/2026

---

## Bước 1: Build production iOS

```bash
cd mobile
eas build --platform ios --profile production
```

- EAS sẽ hỏi đăng nhập Apple Developer (dùng email `trieuxuanhoa@tuaf.edu.vn`)
- Chọn **"Yes"** khi hỏi tạo provisioning profile tự động
- Chờ build hoàn thành (~10-20 phút)
- Khi xong sẽ có link download file `.ipa`

---

## Bước 2: Submit build lên App Store Connect

```bash
eas submit --platform ios
```

- Chọn build vừa tạo ở bước 1
- EAS tự động upload lên App Store Connect
- Chờ upload hoàn thành (~5 phút)

---

## Bước 3: Cấu hình trên App Store Connect

Vào https://appstoreconnect.apple.com → **My Apps** → **PlantDoctor**

### 3.1. App Information (Thông tin app)

- **Name**: `PlantDoctor - Bệnh cây AI`
- **Subtitle**: `Chẩn đoán bệnh cây bằng AI`
- **Category**: Education
- **Content Rights**: Chọn "Does not contain third-party content"
- **Age Rating**: Nhấn "Edit" → trả lời tất cả "None" → kết quả sẽ là 4+

### 3.2. Pricing and Availability

- **Price**: Free
- **Availability**: All territories (hoặc chỉ Vietnam nếu muốn)

### 3.3. App Privacy

- Nhấn **"Get Started"**
- **Data Collection**: Yes
- Khai báo từng loại:
  - ✅ **Contact Info** → Phone Number → Used for "App Functionality" → Linked to User
  - ✅ **Photos or Videos** → Photos → Used for "App Functionality" → NOT Linked to User, NOT used for Tracking
  - ✅ **Location** → Coarse Location → Used for "App Functionality" → NOT Linked to User
- Nhấn **Publish**

### 3.4. Privacy Policy URL

```
https://tuaf.edu.vn/bai-viet/chinh-sach-bao-mat-va-quyen-rieng-tu-43449.html
```

---

## Bước 4: Tạo phiên bản mới (Version)

Vào tab **iOS App** → phiên bản 1.0.0 (đã tạo sẵn)

### 4.1. Screenshots

Upload ảnh chụp màn hình app (chụp từ Simulator hoặc thiết bị thật):

| Kích thước | Thiết bị | Bắt buộc |
|------------|----------|----------|
| 6.7" (1290×2796) | iPhone 15 Pro Max | ✅ Bắt buộc |
| 6.5" (1284×2778) | iPhone 15 Plus | ✅ Bắt buộc |
| 5.5" (1242×2208) | iPhone 8 Plus | Tùy chọn |

**Nội dung screenshots nên có:**
1. Màn hình chính (chụp ảnh lá cây)
2. Kết quả chẩn đoán bệnh
3. Đề xuất thuốc BVTV
4. Thư viện bệnh cây
5. Thời tiết

### 4.2. Description (Mô tả)

```
PlantDoctor giúp nông dân và người trồng cây phát hiện bệnh cây trồng nhanh chóng bằng trí tuệ nhân tạo.

🔍 CHẨN ĐOÁN BỆNH BẰNG AI
• Chụp ảnh hoặc chọn ảnh lá cây từ thư viện
• AI phân tích và nhận diện bệnh trong vài giây
• Hỗ trợ 14 loại cây trồng phổ biến, 38+ loại bệnh
• Đánh giá mức độ nghiêm trọng (nhẹ / trung bình / nặng)

💊 ĐỀ XUẤT ĐIỀU TRỊ
• Gợi ý phương pháp điều trị phù hợp
• Tra cứu thuốc bảo vệ thực vật được phép sử dụng tại Việt Nam
• Cảnh báo hoạt chất CẤM theo Thông tư 75/2025/TT-BNNPTNT

📚 THƯ VIỆN BỆNH CÂY
• Tra cứu triệu chứng, điều kiện phát bệnh, cách phòng tránh
• Hình ảnh minh họa, tên khoa học đầy đủ

🌦️ THỜI TIẾT ĐỊA PHƯƠNG
• Hiển thị thời tiết hiện tại và dự báo 3 ngày
• Hỗ trợ đánh giá nguy cơ phát bệnh theo điều kiện thời tiết

🌱 CÂY TRỒNG HỖ TRỢ
Táo, Việt quất, Anh đào, Ngô, Nho, Cam, Đào, Ớt, Khoai tây, Mâm xôi, Đậu nành, Bí, Dâu tây, Cà chua, Lúa và nhiều loại khác.

⚠️ Lưu ý: Kết quả chẩn đoán chỉ mang tính tham khảo. Vui lòng tham vấn chuyên gia nông nghiệp trước khi sử dụng thuốc bảo vệ thực vật.

Phát triển bởi Trường Đại học Nông Lâm Thái Nguyên.
```

### 4.3. Keywords

```
bệnh cây,nông nghiệp,AI,chẩn đoán,lá cây,thuốc BVTV,plant disease,agriculture,leaf
```

### 4.4. Support URL

```
https://benhcay.tuaf.edu.vn
```

### 4.5. Marketing URL (tùy chọn)

```
https://benhcay.tuaf.edu.vn
```

---

## Bước 5: Chọn Build

- Trong phần **Build** → nhấn dấu **"+"**
- Chọn build vừa upload ở bước 2
- Nếu chưa thấy build → chờ vài phút, Apple đang xử lý

---

## Bước 6: App Review Information

### 6.1. Sign-in Information

- ✅ Tick "Sign-in required"
- **Username**: (SĐT tài khoản demo, ví dụ: `0987654321`)
- **Password**: (mật khẩu demo, ví dụ: `demo123456`)

### 6.2. Contact Information

- **First Name**: Xuân Hòa
- **Last Name**: Triệu
- **Phone**: (SĐT của bạn)
- **Email**: trieuxuanhoa@tuaf.edu.vn

### 6.3. Notes (Ghi chú cho reviewer)

```
PlantDoctor is a plant disease detection app developed by Thai Nguyen University of Agriculture and Forestry (TUAF), Vietnam.

How to test:
1. Login with the demo account provided above
2. Tap "📸 Chụp ảnh" to take a photo of any plant leaf, or "🖼️ Chọn từ thư viện" to pick an existing photo
3. Tap "🔍 Chẩn đoán bệnh" to get AI diagnosis results
4. Results include disease name, severity, treatment suggestions, and recommended pesticides

The app requires camera access to photograph plant leaves for disease diagnosis.
Location is used only to display local weather information relevant to disease risk assessment.

Sign in with Apple is available on the Profile tab for iOS users.
Phone number login is the primary method as our target users are Vietnamese farmers who primarily use phone numbers.
```

---

## Bước 7: Submit for Review

- Kiểm tra lại tất cả mục đã điền đầy đủ (không có warning đỏ)
- Nhấn **"Add for Review"**
- Nhấn **"Submit to App Review"**

---

## Bước 8: Chờ Review

- Thời gian review: thường **24-48 giờ**, có thể lên 7 ngày
- Theo dõi email và App Store Connect để xem trạng thái
- Nếu bị **Reject**: đọc lý do → sửa → submit lại

---

## Các lý do reject phổ biến và cách xử lý

| Lý do | Cách xử lý |
|-------|------------|
| Missing demo account | Đảm bảo tài khoản demo hoạt động |
| Incomplete functionality | Test kỹ tất cả flow trước khi submit |
| Privacy policy không match | Đảm bảo URL privacy hoạt động |
| Crash on launch | Test build production trên thiết bị thật |
| Guideline 4.2 (Minimum Functionality) | Đảm bảo app có đủ tính năng, không quá đơn giản |

---

## Sau khi được duyệt

- App tự động lên App Store (hoặc chọn ngày release thủ công)
- Kiểm tra download từ App Store
- Thiết lập **EAS Update** cho hotfix không cần re-submit:
  ```bash
  eas update --branch production --message "hotfix: ..."
  ```

---

## Tóm tắt lệnh

```bash
# 1. Build
cd mobile
eas build --platform ios --profile production

# 2. Submit
eas submit --platform ios

# 3. Hotfix sau này (không cần review lại)
eas update --branch production --message "fix: mô tả ngắn"
```
