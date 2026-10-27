# Dung lượng và cấu trúc trên máy

Mã nguồn, kiểm thử, tài liệu, báo cáo và số liệu thực nghiệm được giữ trong Git. Không xóa các phần này chỉ vì chúng không được đọc khi web khởi động: chúng cần cho bảo trì và nộp bài tập lớn.

| Thư mục | Vai trò |
| --- | --- |
| `client/src`, `server`, `judge`, `database` | Mã nguồn giao diện, API, bộ chấm và migration |
| `scripts`, `tests`, `demo`, `experiments` | Vận hành, kiểm thử, tạo học liệu và thực nghiệm |
| `docs`, `REPORT`, `statics` | Hướng dẫn, sơ đồ, báo cáo và minh chứng |
| `client/node_modules`, `.venv` | Thư viện đã cài, cần để chạy và build trên máy này |
| `client/.next` | Bản giao diện đã build; thư mục `cache` bên trong có thể tạo lại |
| `tools/nginx` | Nginx đã cài trên máy, thay cho bản trước đây đặt trong `tmp` |
| `.runtime/web` | Database và toàn bộ file học liệu/bài nộp/testcase đang dùng; phải sao lưu cùng nhau |
| `.runtime/tls` | CA và chứng chỉ LAN; giữ nguyên để điện thoại đã cài CA tiếp tục tin cậy |
| `.runtime/launcher` | Trạng thái tiến trình và log vận hành |
| `.runtime/accounts` | `LOGIN.txt`, `students.csv` riêng tư; không đưa lên Git |
| `.runtime/bootstrap` | Môi trường riêng do bộ cài một file tạo và trạng thái cài tiếp; không xóa Python/Node tại đây khi đang dùng |
| `.runtime/releases` | File ZIP bàn giao một-file hiện hành |
| `.runtime/offline-kit` | Một bộ source/thư viện/image để chuyển máy offline; không cần cho web hiện tại, giữ để phục vụ bàn giao USB |
| `.runtime/backups` | Bản sao lưu dữ liệu hiện tại và bản trước khi bỏ khóa mạng |
| `.runtime/audit`, `.runtime/maintenance` | Minh chứng giao diện và nhật ký bảo trì |

Các bộ USB cũ, bản copy source kiểm thử/nộp thử, database pytest, cache build và bản sao VHDX Docker khi sửa lỗi không phải dữ liệu chạy web. Đã loại các bản trùng này. Ổ Docker thực tế do Docker Desktop quản lý ở ngoài repo; thao tác dọn repo không xóa image, container hay volume Docker.

Các sơ đồ đã giao được giữ ở `docs/diagrams`. `docs/CODE_OWNERSHIP.md` và bảng phân công Excel trên máy được giữ nguyên.

## Dọn lần sau

Xem trước bằng PowerShell: `./scripts/clean_workspace.ps1`. Bản áp dụng dùng `-Apply`; phải dừng web, kiểm tra bản backup hiện tại và bộ offline trước. Script kiểm tra đường dẫn nằm trong project, từ chối filesystem link và từ chối dọn khi dịch vụ dự án còn chạy. Không chạy apply khi có file mới tự đặt trong `.runtime` mà chưa đọc danh sách xem trước. Khi ngày backup thay đổi, cập nhật tên bản giữ lại trong script trước.

Đừng copy cả các môi trường cài sẵn khi chỉ muốn chia sẻ source: clone Git hoặc đóng gói bằng `scripts.prepare_usb` theo hướng dẫn offline. Khi cần chuyển đúng dữ liệu hiện tại, dùng snapshot DB/storage trong `classroom-data/server-snapshot` của bộ offline; lệnh nạp từ chối ghi đè database đã tồn tại.


Cập nhật cài tự động: mở `CAI_VA_CHAY_LMS.cmd` để kiểm tra/cài môi trường, nạp dữ liệu và chạy web; xem [ONE_FILE_SETUP.md](ONE_FILE_SETUP.md). Bước cài tay phía trên vẫn dùng được khi môi trường đã có.
