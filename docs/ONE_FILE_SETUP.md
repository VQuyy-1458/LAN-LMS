# Cài và chạy bằng một file trên Windows

Giải nén toàn bộ bộ ZIP vào ổ cứng, ví dụ `D:\LAN-LMS-USB`, rồi mở **`CAI_VA_CHAY_LMS.cmd`**. Không chạy file bên trong cửa sổ xem ZIP. Máy cần Windows x64 tương thích Docker Desktop (Windows 10 22H2 build 19045 hoặc Windows 11 23H2 build 22631 trở lên), tối thiểu 8 GB RAM và đã bật VT-x/AMD-V trong BIOS/UEFI.

## Lần đầu

File tự kiểm tra Python 3.12, Node.js 24, WSL2 và Docker Desktop. Nếu thiếu Python/Node, cài bản riêng cho project trong `.runtime/bootstrap` để không thay thế phiên bản của dự án khác. Phần mềm nền được tải từ Python.org, Nodejs.org và Docker; installer EXE được kiểm tra chữ ký nhà phát hành, Node ZIP được đối chiếu SHA-256 của nhà phát hành. Thiết lập WSL dùng lệnh Windows/Microsoft.

Khi Windows hỏi Administrator, chọn Yes nếu đồng ý cài các thành phần này. Firewall chỉ cho Nginx của project nhận TCP 8080/8443 từ mạng nội bộ trên profile Private; không tắt firewall, không đổi profile mạng hay tự thêm người dùng vào nhóm docker-users.

Nếu cần reboot, chương trình hỏi trước, ghi một mục RunOnce của tài khoản hiện tại và tiếp tục một lần sau khi đăng nhập. Giữ nguyên vị trí thư mục cho đến khi cài xong. Nếu chưa reboot ngay, có thể reboot sau hoặc chạy lại cùng file. Không tự reset Docker/WSL hay xóa distro, image hoặc volume. Nếu BIOS chưa bật ảo hóa, script dừng và hướng dẫn bật; nó không tự sửa BIOS.

Docker hiển thị điều khoản ở lần mở đầu: người dùng phải tự đọc và chọn Accept nếu đồng ý. Script không truyền cờ tự chấp nhận điều khoản. Nếu đang ở Windows containers, chuyển sang Linux containers trong Docker Desktop. Quá thời gian chờ Engine sẽ báo lỗi để sửa và chạy lại, không giả báo chấm đã hoạt động.

Sau đó chương trình chuẩn bị thư viện, Nginx và image bộ chấm, kiểm tra C/C++/Java thật (mỗi ngôn ngữ phải trả AC), khởi động web và mở trình duyệt. Nó dùng lại môi trường đã hoàn tất; các bước offline bị ngắt có trạng thái để chạy tiếp và không ghi đè thư mục môi trường không do bộ cài quản lý.

## Dữ liệu

- **Bộ ZIP đầy đủ** (`offline-kit`): tự nạp `classroom-data/server-snapshot` vào bản cài mới. Khóa học, tài khoản, mật khẩu đã đổi, học liệu và bài nộp giữ theo thời điểm snapshot. Phiên đăng nhập cũ được thu hồi khi restore; người dùng đăng nhập lại. File ghi chú cấp tài khoản ở `.runtime/accounts` và `classroom-data`; không công khai bộ ZIP vì chứa dữ liệu riêng tư.
- **Clone/tải source GitHub**: tải thư viện và build image qua Internet, tạo bộ hai khóa C/C++/Java và CTDL với 40 tài khoản do nhóm soạn nếu chưa có dữ liệu. Thông tin đăng nhập sinh ra tại `.runtime/accounts/LOGIN.txt` và `students.csv`. Source không có database/mật khẩu của máy đóng gói.
- Nếu đã có database, chương trình giữ nguyên. Database có nhưng thiếu storage hoặc đường dẫn database tùy chỉnh không tồn tại thì dừng để người dùng khôi phục đúng bản sao lưu, không thay bằng dữ liệu mới.

Các máy sinh viên chỉ cần trình duyệt và cùng LAN. Trên máy chủ mở `http://localhost:8080`; máy khác dùng IP chương trình hiển thị. Nếu không có LAN, chương trình mở trên máy chủ trước. Mạng khách có cách ly thiết bị có thể chặn truy cập. Chụp ảnh QR dùng camera hệ thống qua HTTP; HTTPS/quét camera liên tục là tùy chọn theo hướng dẫn cài chứng chỉ, cần OpenSSL trên máy chủ.

## Lần sau và chẩn đoán

Chạy lại cùng `CAI_VA_CHAY_LMS.cmd`; không cài lại toàn bộ. Dùng `DUNG_WEB.cmd` trong thư mục `LAN-LMS` để dừng web. Cần Internet cho các phần mềm nền chưa tải sẵn; khi đã có môi trường, phần thư viện/image trong bộ ZIP không cần tải lại.

Chế độ chỉ kiểm tra, không cài/chỉnh dịch vụ: `powershell.exe -NoProfile -File scripts/bootstrap_windows.ps1 -CheckOnly`. Log các installer ở `.runtime/bootstrap/logs`. Bộ cài dừng nếu thư mục cài đặt đã đổi vị trí hoặc dependency thay đổi giữa lần cài dở; giữ dữ liệu và dùng bản giải nén mới khi cần.

## Phạm vi kiểm thử bản bàn giao

Đã kiểm tra kế hoạch khi thiếu môi trường, truyền tham số Windows, cài offline bị ngắt và chạy tiếp, dữ liệu có sẵn/tùy chỉnh, checksum và backup/restore bằng kiểm thử tự động. Đã cài thật vào thư mục sạch trên máy Windows hiện tại, build giao diện, restore lớp học, chấm C/C++/Java trả AC, khởi động API/frontend/worker và kiểm tra đăng nhập. Chạy lại không cài lại hay thay dữ liệu. Máy kiểm thử đã có Docker/WSL và Python/Node; chưa có bằng chứng nghiệm thu cài phần mềm hệ thống từ đầu và reboot trên một máy Windows trắng khác. Các nhánh đó được kiểm tra bằng chẩn đoán/kế hoạch và lệnh cài từ tài liệu nhà phát hành.

Tài liệu nguồn: [Docker Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [Microsoft WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands), [Python Windows installer](https://docs.python.org/3.12/using/windows.html).
