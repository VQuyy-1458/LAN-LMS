# Camera điểm danh trên Android và iPhone

## Cách thông thường — không cài chứng chỉ

Mở địa chỉ HTTP LAN do CHAY_LAN.cmd in ra, ví dụ http://192.168.1.100:8080. Đăng nhập → chọn khóa học → Điểm danh → **Chụp QR để điểm danh**. Điện thoại mở camera hệ thống (nếu hiện bảng lựa chọn, chọn Camera); chụp QR và dùng ảnh đó. Web tự đọc ảnh tại máy và ghi nhận Có mặt, không có bước xác nhận thêm trên web. Có nút Chọn ảnh QR có sẵn cho ảnh đã chụp. Cách này không cần Internet hoặc cài CA. Trên desktop, nút chụp có thể mở hộp chọn ảnh.

Đây là HTML Media Capture của trình duyệt; giao diện chụp tùy Android/iOS. Nếu muốn giữ video camera mở liên tục để đọc QR trong trang, dùng cách HTTPS tùy chọn bên dưới.

## Trên máy chủ

Nhấp đúp CHAY_LAN.cmd. Giữ máy chủ hoạt động. Cửa sổ in:

- Địa chỉ HTTPS, ví dụ https://192.168.1.100:8443.
- Trang cài điện thoại, ví dụ http://192.168.1.100:8080/setup.
- Dấu vân tay SHA-256 của chứng chỉ CA để đối chiếu.

Launcher tạo CA và chứng chỉ cho đúng IP ở .runtime/tls/, dùng OpenSSL của Git for Windows. Không tự cài CA vào kho tin cậy. Chỉ file CA công khai .cer được tải qua API; private key không được chia sẻ hay đưa lên Git.

## Trên điện thoại (một lần cho mỗi máy chủ)

Kết nối cùng mạng với máy chủ, mở trang /setup ở địa chỉ HTTP phía trên. Tải LAN-LMS-CA.cer; đối chiếu dấu vân tay với cửa sổ máy chủ trước khi cài.

**Android:** mở Cài đặt, tìm “Cài đặt chứng chỉ” / “Chứng chỉ CA”, chọn cài CA từ bộ nhớ và chọn file vừa tải. Tên mục tùy hãng. Xác nhận bằng khóa máy nếu được hỏi. [Hướng dẫn Google](https://support.google.com/pixelphone/answer/2844832).

**iPhone/iPad:** tải bằng Safari; vào Cài đặt → Đã tải về hồ sơ, hoặc Cài đặt chung → VPN & Quản lý thiết bị, để cài. Sau đó Cài đặt chung → Giới thiệu → Cài đặt tin cậy chứng nhận, bật tin cậy hoàn toàn cho **LAN-LMS Local CA**. [Hướng dẫn Apple](https://support.apple.com/102390).

Mở địa chỉ HTTPS. Đăng nhập → chọn khóa học → Điểm danh → Mở camera quét QR → cho phép camera. Quét đúng QR đang mở sẽ tự ghi nhận Có mặt; bảng giáo viên nhận sự kiện WebSocket. Nếu mở liên kết QR bằng camera hệ thống, sau đăng nhập hệ thống cũng tự gửi điểm danh.

Camera cần HTTPS được tin cậy hoặc localhost theo [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia). Không bỏ qua cảnh báo SSL hoặc tắt kiểm tra bảo mật để mở camera. Chụp/chọn ảnh QR và nhập mã là phương án dự phòng.

Nếu máy chủ đổi IP, chạy lại CHAY_LAN.cmd; chứng chỉ server sẽ được cấp lại theo IP mới, CA vẫn giữ nguyên. Nếu thay/xóa CA, phải cài lại CA trên điện thoại. Có thể gỡ CA trong cài đặt khi không còn dùng lớp học.

## Khi điện thoại không truy cập được

Kiểm tra cùng LAN, đúng IP, máy chủ đang bật, mạng không cô lập thiết bị Wi-Fi. Firewall cần cho phép Nginx nhận TCP 8080 và 8443 từ mạng lớp học. Launcher không tự sửa firewall; nếu Nginx đã được cho phép theo chương trình thì rule đó có thể đã bao gồm cả hai cổng.
