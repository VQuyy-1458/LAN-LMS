# Chạy trên máy khác

## Máy sinh viên

Không cần cài Python, Node hay Docker. Kết nối cùng LAN/Wi-Fi với máy chủ, mở trình duyệt và vào địa chỉ HTTP mà `CHAY_LAN.cmd` hiển thị. Dùng tài khoản giảng viên cung cấp. Với điểm danh qua HTTP, dùng chức năng chụp ảnh QR; quét camera liên tục qua HTTPS cần thiết lập chứng chỉ riêng.

## Chuyển máy chủ — bộ Windows offline hiện tại

1. Chuẩn bị Windows x64, Python 3.12 có Python Launcher (`py -3.12`), Node.js 24.x và Docker Desktop với WSL2/Linux Engine đang chạy. Cài phần mềm nền trước; chúng không nằm trong bộ source. Sau khi cài có thể cần khởi động lại Windows. Kiểm tra `py -3.12 --version`, `node -v`, `docker info`.
2. Chép **toàn bộ** `.runtime/offline-kit` trên máy nguồn sang thư mục ngắn trên ổ cứng máy đích, ví dụ `D:\LAN-LMS-USB`. Giữ nguyên `LAN-LMS`, `dependencies`, `classroom-data`, `manifest.json` và các file CMD. Không chạy trực tiếp từ USB và không chép `.venv` hay `node_modules` của thư mục project chính sang máy mới.
3. Chạy `D:\LAN-LMS-USB\LAN-LMS\CAI_OFFLINE.cmd` một lần trong thư mục mới. Trình cài kiểm tra checksum, dựng thư viện từ bộ có sẵn, nạp image bộ chấm và build giao diện; bước này không dùng npm/pip Internet. Khi bộ có snapshot lớp, không cần tạo tài khoản giảng viên mới.
4. Chạy `D:\LAN-LMS-USB\NAP_DU_LIEU_LOP.cmd` để nạp database và file lớp đang có trong bộ. Lệnh từ chối ghi đè nếu máy đích đã có database web. Tài khoản được giữ theo snapshot, thông tin cấp ban đầu ở `classroom-data\LOGIN.txt` và `students.csv`; mật khẩu đã đổi trên máy nguồn vẫn là mật khẩu tại thời điểm snapshot.
5. Chạy `D:\LAN-LMS-USB\LAN-LMS\CHAY_LAN.cmd`. Mở `http://localhost:8080` trên máy chủ. Các máy khác dùng địa chỉ LAN được cửa sổ lệnh hiển thị; IP thay đổi theo máy và mạng, không lấy IP của máy nguồn. Nếu Windows hỏi firewall, cho phép trên mạng riêng (Private). Các máy phải liên lạc được trong cùng LAN; mạng khách có cách ly thiết bị có thể chặn truy cập.

Các lần sau chỉ mở Docker Desktop, chờ Engine chạy, rồi chạy `CHAY_LAN.cmd`. Dừng web bằng `DUNG_WEB.cmd`. Chưa cần cấu hình MySQL: bộ hiện dùng SQLite và private storage đã đóng gói.

Bộ offline là ảnh chụp dữ liệu lúc đóng gói, không tự đồng bộ những thay đổi sau đó. Nếu cần chuyển dữ liệu mới hơn, dừng web/worker và xuất snapshot nhất quán bằng `scripts.backup_database` hoặc xuất khóa học ZIP theo hướng dẫn README, rồi đóng gói lại.
