# Rà soát chức năng ngày 26/10/2026

## Kết quả có bằng chứng

Backend + Docker thật trên Linux: **90 passed, 1 warning** (78,02 giây). [CI nguồn f73e094](https://github.com/VQuyy-1458/LAN-LMS/actions/runs/40351500700). Cùng CI chạy 5 test frontend, TypeScript, ESLint và build production thành công. Warning hiện tại là cảnh báo httpx/TestClient, không phải lỗi chức năng.

Trên Windows, bộ kiểm thử hồi quy trước khi bật Docker gồm 79 passed và 10 test Docker skipped; skipped không được coi là đã chạy bộ chấm trên Windows. Bản mở rộng chạy cả 10 bài trên CI, gồm giữa kỳ và cuối kỳ.

| Nhóm | Cách kiểm tra và kết quả |
|---|---|
| Khách / đăng nhập / phân quyền | Test HTTP auth/CSRF/role và kiểm tra trình duyệt: khách xem trang chủ, vào khóa học cần login, không đọc được dữ liệu bảo vệ |
| Điều hướng | Xem trực tiếp cả hai vai trò: menu chung chỉ Tổng quan/Khóa học; chọn khóa mới có các tab; course/tab giữ qua tải lại và có kiểm thử parser URL |
| Sinh viên / CSV / tài liệu / bài tập | Bộ regression kiểm tra quyền, deadline, trùng request, upload, đọc file, chấm tay và dữ liệu cá nhân |
| Lịch / QR / chỉnh tay | HTTP + WebSocket thật: quét ghi present, teacher nhận attendance.updated; kiểm tra roster bao gồm người chưa quét; present/late/absent, không ghi đè chỉnh tay khi quét lại |
| QR trên trình duyệt | Tạo QR theo lịch khóa thực hành; sinh viên đọc ảnh QR thật và nhận “Điểm danh bằng QR thành công”, lịch sử chuyển “Đã điểm danh” |
| HTTPS | Request tới IP LAN 8443 với CA xác thực, kiểm tra chain và IP SAN; /ready, /setup, catalogue và CA download trả 200; không bỏ qua xác thực SSL |
| Thi lập trình | 2 kỳ / 10 bài / 62 test cụ thể. Nộp HTTP -> claim job -> Docker thật -> verdict AC; kiểm tra điểm 5/7/8/9/10 qua cả hai kỳ. Các test runner khác kiểm tra C/C++/Java, CE/WA/RTE/TLE/MLE, filesystem/network isolation |
| Mất kết nối / queue / đồng thời | Regression kiểm tra retry, idempotency, lease, fencing, outbox, heartbeat/WS và phục hồi snapshot REST |
| Bảng điểm / backup / đóng gói | Regression kiểm tra AC counting, quyền công bố, trọng số/override, checksum/restore và loại file riêng khỏi gói source |

## Môi trường còn cần xác nhận

- **Camera vật lý Android/iPhone:** cần cài và bật tin cậy CA theo trang /setup rồi truy cập HTTPS. Chưa có xác nhận từ điện thoại thật trong lần rà soát này. Ảnh QR trên web và HTTPS đã được kiểm tra riêng thành công.
- **Docker Desktop Windows:** engine treo tại init /ping; khởi động lại Docker và riêng distro docker-desktop vẫn chưa đưa được Linux Engine lên trạng thái sẵn sàng. Không factory reset, không xóa image/volume. Giao diện báo bộ chấm chưa sẵn sàng; worker chờ và không nhận job khi engine chưa chạy.
- Chưa lấy kết quả loopback/CI thay cho phép đo nhiều máy vật lý trong LAN.

## Dùng bản demo

CHAY_LAN.cmd chạy web; mở http://IP:8080/setup để chuẩn bị camera và https://IP:8443 để dùng trên điện thoại. Chọn khóa **Lập trình mạng — Phòng thực hành thi trực tuyến**. Tài khoản teacher/student demo hiện có được giữ nguyên mật khẩu.

Khóa mới có lịch học, tài liệu hướng dẫn, bài tập phân tích HTTP/WebSocket, hai đề đang mở trong 7 ngày từ lúc seed. Đề demo có thang 0/5/7/8/9/10 và hỗ trợ C17/C++17/Java 17. Không tạo kết quả chấm giả trong dữ liệu ứng dụng.

Để chấm tại máy chủ Windows: đưa Docker Desktop Linux Engine về Running, chạy BAT_BO_CHAM.cmd để chuẩn bị image. Worker nền sẽ tự nhận bài sau đó. DUNG_WEB.cmd dừng các dịch vụ do launcher quản lý.

Trước khi thêm khóa mẫu đã tạo snapshot DB/storage trong .runtime/backups/pre-full-audit-20261026. Script seed không ghi đè khóa/đề/bài nộp khi chạy lại và không đổi mật khẩu tài khoản.
