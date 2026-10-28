# Chạy LAN-LMS từ bộ chuyển máy offline Windows

## Máy phòng thi cần cài trước

- Windows x64, Python 3.12 có lệnh `py -3.12`.
- Node.js cùng major với manifest bộ USB (bộ chuẩn bị trên máy hiện tại dùng Node 24).
- Docker Desktop và WSL2 đã cài, Linux Engine đang chạy. Cần đủ RAM/ổ đĩa cho compiler image và dependencies.
- Các máy sinh viên chỉ cần trình duyệt và kết nối LAN với máy chủ; không cài các phần mềm trên.

Bộ offline **không cài Windows/WSL2/Docker/Python/Node** và không đổi firewall. Nếu máy chưa có phần mềm nền hoặc chưa khởi tạo Docker thì phải chuẩn bị trước. Không sao chép `.venv` từ máy cũ.

## Chuẩn bị một lần trên máy có Internet

Tại gốc project, sau khi đã cài dependency frontend và có image chấm:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_usb --output .runtime\usb-kit-20261027
```

Script lấy file source đã được Git theo dõi (nội dung working tree), tải wheel Windows theo lockfile, đóng gói `node_modules` của Windows, Nginx và `docker save` image. Không lấy DB, `.env`, uploads, `.runtime`, Git credentials, báo cáo cá nhân hay file chưa theo dõi. Đóng gói sau khi kiểm thử/commit để source nhất quán. Không chạy npm/pip cập nhật phiên bản trong lúc đóng gói.

Gói lớn nhiều GB: nên dùng USB exFAT/NTFS nếu file Docker tar lớn hơn 4 GB. Sao chép **cả thư mục gói**, gồm `LAN-LMS`, `dependencies`, `manifest.json`, `START_HERE.txt`.

## Trên máy đích không có Internet

1. Copy gói vào đường dẫn ngắn trên ổ đĩa cục bộ, ví dụ `D:\LAN-LMS-USB` (không nên chạy DB trực tiếp trên USB).
2. Mở Docker Desktop, chờ Engine running.
3. Nhấp `LAN-LMS\CAI_OFFLINE.cmd`. Script kiểm checksum, tạo venv mới, cài wheel với `--no-index`, chép frontend dependencies, nạp Docker image và kiểm image ID, migration DB, build giao diện. Cuối cùng hỏi tạo tài khoản teacher trên máy mới.
4. Chạy `LAN-LMS\CHAY_LAN.cmd`. Dùng IP mới mà launcher in ra; IP máy cũ không được mang sang.
5. Đăng nhập teacher → nhập ZIP khóa học xuất từ máy cũ. Sinh viên dùng tài khoản đã chuyển để đăng nhập. Kiểm tra điểm, file, source và một bài chấm thật trước buổi thi.

Nếu thiếu OpenSSL/Git, launcher chạy HTTP LAN; camera chụp QR hệ thống vẫn dùng được. HTTPS là tùy chọn. Nếu máy sinh viên chưa truy cập được, cần người quản lý phòng máy cho phép cổng 8080 qua Windows Firewall; script không tự nới quyền mạng.

`CAI_OFFLINE.cmd` không dùng pip/npm Internet và không tự cập nhật Docker. Môi trường đã cài dở hoặc đã có venv phải được giữ lại; dùng bản gói giải nén mới để thử lại, script không tự xóa cài đặt cũ. Manifest SHA-256 phát hiện lỗi copy, không chứng minh nguồn tin cậy; chỉ dùng bộ do nhóm chuẩn bị.

Kiểm thử cài vào thư mục sạch trên cùng máy không thay cho nghiệm thu ở máy phòng thi khác. Nhóm cần kiểm tra một lượt Windows sạch/máy phòng thi và hai máy LAN dây trước bàn giao chính thức.

Nếu chỉ sửa source/học liệu mà lockfile và judge image không đổi, có thể đóng gói lại không cần Docker chạy: `python -m scripts.prepare_usb --output THU_MUC_MOI --reuse-dependencies THU_MUC_GOI_CU`. Script kiểm SHA-256 của dependency và đối chiếu lockfile/Dockerfile/sandbox trước khi dùng lại.
