# Checklist đưa PlantDoctor lên Apple App Store & Google Play

> Cập nhật: 30/05/2026

---

## 1. Tài khoản nhà phát triển

| # | Hạng mục | Apple | Google | Trạng thái |
|---|----------|-------|--------|------------|
| 1.1 | Đăng ký tài khoản Developer | Apple Developer Program ($99/năm) | Google Play Console ($25 một lần) | ☐ |
| 1.2 | Xác minh danh tính/tổ chức | Cần D-U-N-S Number nếu đăng ký tổ chức | Xác minh danh tính cá nhân hoặc tổ chức | ☐ |
| 1.3 | Thiết lập thông tin thanh toán | Cần cho việc gia hạn hàng năm | Cần nếu bán app/IAP | ☐ |

---

## 2. Chuẩn bị ứng dụng (Code & Build)

| # | Hạng mục | Chi tiết | Trạng thái |
|---|----------|----------|------------|
| 2.1 | Cấu hình `app.json` / `app.config.js` | Bundle ID (com.tuaf.plantdoctor), version, icon, splash | ☐ |
| 2.2 | App Icon | iOS: 1024x1024 (không alpha, không rounded). Android: 512x512 (adaptive icon) | ☐ |
| 2.3 | Splash Screen | Ảnh splash phù hợp nhiều kích thước màn hình | ☐ |
| 2.4 | Cài đặt EAS CLI | `npm install -g eas-cli` + `eas login` | ☐ |
| 2.5 | Cấu hình `eas.json` | Profile: development, preview, production | ☐ |
| 2.6 | Target API level | iOS: SDK 18+ (Xcode 16+). Android: API level 35 (Android 15) | ☐ |
| 2.7 | Build production iOS | `eas build --platform ios --profile production` | ☐ |
| 2.8 | Build production Android | `eas build --platform android --profile production` (output .aab) | ☐ |
| 2.9 | Test trên thiết bị thật | iPhone SE (màn nhỏ) + iPhone 15 (màn lớn) + Android các kích thước | ☐ |
| 2.10 | Kiểm tra crash/ANR | Không crash, không treo, load nhanh | ☐ |

---

## 3. Quyền riêng tư & Bảo mật

| # | Hạng mục | Chi tiết | Trạng thái |
|---|----------|----------|------------|
| 3.1 | Chính sách quyền riêng tư (Privacy Policy) | Trang web công khai, mô tả dữ liệu thu thập/sử dụng | ☐ |
| 3.2 | Apple: Privacy Nutrition Labels | Khai báo trong App Store Connect: camera, photos, location | ☐ |
| 3.3 | Google: Data Safety Section | Khai báo trong Play Console: dữ liệu thu thập, chia sẻ, bảo mật | ☐ |
| 3.4 | Quyền truy cập (Permissions) | Camera, Photo Library, Location — chỉ yêu cầu khi cần, có mô tả rõ ràng | ☐ |
| 3.5 | iOS: NSCameraUsageDescription | Mô tả lý do cần camera trong Info.plist | ☐ |
| 3.6 | iOS: NSPhotoLibraryUsageDescription | Mô tả lý do cần truy cập thư viện ảnh | ☐ |
| 3.7 | iOS: NSLocationWhenInUseUsageDescription | Mô tả lý do cần vị trí (thời tiết) | ☐ |
| 3.8 | Mã hóa dữ liệu | HTTPS cho mọi API call, không lưu ảnh người dùng trên server | ☐ |
| 3.9 | Apple: App Tracking Transparency | Nếu tracking user → cần ATT framework. Nếu không → khai báo "không track" | ☐ |

---

## 4. Nội dung Store Listing

| # | Hạng mục | Apple App Store | Google Play | Trạng thái |
|---|----------|----------------|-------------|------------|
| 4.1 | Tên app | Max 30 ký tự | Max 50 ký tự | ☐ |
| 4.2 | Subtitle / Short description | Max 30 ký tự (iOS) | Max 80 ký tự (Android) | ☐ |
| 4.3 | Mô tả đầy đủ | Max 4000 ký tự | Max 4000 ký tự | ☐ |
| 4.4 | Keywords (iOS) | Max 100 ký tự, phân cách bằng dấu phẩy | Không có (dùng trong mô tả) | ☐ |
| 4.5 | Danh mục | Education hoặc Utilities | Education hoặc Tools | ☐ |
| 4.6 | Xếp hạng nội dung | Tự đánh giá qua questionnaire | Tự đánh giá qua questionnaire | ☐ |
| 4.7 | URL hỗ trợ | Trang web/email hỗ trợ người dùng | Trang web/email hỗ trợ | ☐ |
| 4.8 | URL chính sách quyền riêng tư | Bắt buộc | Bắt buộc | ☐ |

---

## 5. Screenshots & Media

| # | Hạng mục | Yêu cầu | Trạng thái |
|---|----------|----------|------------|
| 5.1 | Screenshots iOS | Tối thiểu 3 ảnh cho mỗi kích thước: 6.7" (1290x2796), 6.5" (1284x2778), 5.5" (1242x2208) | ☐ |
| 5.2 | Screenshots iPad (nếu hỗ trợ) | 12.9" (2048x2732) | ☐ |
| 5.3 | Screenshots Android | Tối thiểu 4 ảnh, kích thước 16:9 hoặc 9:16, min 320px, max 3840px | ☐ |
| 5.4 | Feature Graphic (Android) | 1024x500 px, bắt buộc | ☐ |
| 5.5 | Video preview (tùy chọn) | iOS: 15-30s. Android: YouTube link | ☐ |
| 5.6 | Nội dung screenshots | Thể hiện chức năng chính: chụp ảnh → kết quả → thuốc BVTV | ☐ |

---

## 6. Kiểm tra trước khi submit

| # | Hạng mục | Chi tiết | Trạng thái |
|---|----------|----------|------------|
| 6.1 | App hoạt động đầy đủ | Không có màn hình "coming soon", không có tính năng bị hỏng | ☐ |
| 6.2 | Không có nội dung placeholder | Không có Lorem ipsum, ảnh test, dữ liệu giả | ☐ |
| 6.3 | Deep links hoạt động | Nếu có universal links / app links | ☐ |
| 6.4 | Đăng nhập/đăng ký hoạt động | Cung cấp tài khoản demo cho reviewer | ☐ |
| 6.5 | Tài khoản demo cho reviewer | Username + password để reviewer test app | ☐ |
| 6.6 | Ghi chú cho reviewer | Giải thích cách sử dụng app, tính năng cần camera | ☐ |
| 6.7 | Kiểm tra trên nhiều thiết bị | Màn hình nhỏ/lớn, iOS/Android versions khác nhau | ☐ |
| 6.8 | Performance | App load < 3s, không lag, không memory leak | ☐ |
| 6.9 | Accessibility | VoiceOver/TalkBack hoạt động, contrast đủ, font đọc được | ☐ |
| 6.10 | Offline handling | Hiển thị thông báo phù hợp khi mất mạng | ☐ |

---

## 7. Quy trình Submit

### 7.1 Apple App Store

```
1. Đăng nhập App Store Connect (appstoreconnect.apple.com)
2. Tạo App mới → điền Bundle ID, tên, ngôn ngữ chính
3. Điền thông tin Store Listing (mục 4 + 5 ở trên)
4. Upload build: `eas submit --platform ios`
5. Chọn build trong App Store Connect
6. Điền App Review Information (tài khoản demo, ghi chú)
7. Khai báo Privacy (mục 3)
8. Submit for Review
9. Chờ review (thường 24-48h, có thể lên 7 ngày)
```

### 7.2 Google Play Store

```
1. Đăng nhập Google Play Console (play.google.com/console)
2. Tạo App mới → điền tên, ngôn ngữ, loại (app/game), free/paid
3. Hoàn thành Dashboard checklist:
   - App access (tài khoản demo)
   - Ads declaration
   - Content rating questionnaire
   - Target audience
   - Data safety form
   - Store listing (mục 4 + 5)
4. Upload .aab: `eas submit --platform android`
5. Tạo Release trong Production track
6. Submit for Review
7. Chờ review (thường 1-7 ngày, app mới có thể lâu hơn)
```

---

## 8. Sau khi được duyệt

| # | Hạng mục | Chi tiết | Trạng thái |
|---|----------|----------|------------|
| 8.1 | Kiểm tra app trên Store | Download và test lại từ Store | ☐ |
| 8.2 | Thiết lập OTA updates | Cấu hình EAS Update cho hotfix không cần re-submit | ☐ |
| 8.3 | Monitoring | Theo dõi crash reports (Sentry/Firebase Crashlytics) | ☐ |
| 8.4 | Phản hồi đánh giá | Trả lời review của người dùng trên Store | ☐ |
| 8.5 | Lên kế hoạch update | Cập nhật định kỳ để duy trì ranking | ☐ |

---

## 9. Lưu ý đặc biệt cho PlantDoctor

| Vấn đề | Giải pháp |
|--------|-----------|
| App dùng camera → Apple yêu cầu giải thích rõ | Thêm mô tả: "Chụp ảnh lá cây để AI chẩn đoán bệnh" |
| App dùng location → cần giải thích | "Lấy vị trí để hiển thị thời tiết địa phương, hỗ trợ đánh giá nguy cơ bệnh" |
| App gọi API bên ngoài → cần HTTPS | Đảm bảo API endpoint dùng HTTPS |
| App có tính năng đăng nhập → Apple yêu cầu Sign in with Apple | Cân nhắc thêm hoặc giải thích tại sao chỉ dùng SĐT |
| Google yêu cầu test 20 người dùng (closed testing) trước production | Tạo closed testing track, mời 20 người test ít nhất 14 ngày |
| Nội dung y tế/nông nghiệp → disclaimer | Thêm disclaimer "kết quả chỉ mang tính tham khảo" rõ ràng |

---

## 10. Chi phí tổng kết

| Hạng mục | Chi phí |
|----------|---------|
| Apple Developer Program | $99/năm (~2.5 triệu VNĐ) |
| Google Play Console | $25 một lần (~625k VNĐ) |
| EAS Build (free tier) | 30 builds/tháng miễn phí |
| D-U-N-S Number (nếu tổ chức) | Miễn phí (đăng ký qua Apple) |
| **Tổng khởi đầu** | **~3.1 triệu VNĐ** |
