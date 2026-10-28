> Nhật ký mốc trước bản hoàn thiện. Trạng thái hiện hành xem README, PROJECT_PLAN 1.2 và API 1.2.

# TV1 — nghiệm thu công việc ngày 24/10/2026

Nguồn: bảng Google Sheets do người dùng cung cấp, tab Cong viec và Chi tiet; ngày làm việc theo giờ Việt Nam. Không sửa tiến độ/dấu tích trên Google Sheets vì yêu cầu hiện tại là thực hiện code và push. Bảng dưới phân biệt phần backend đã kiểm chứng với nghiệm thu chung còn chờ người khác.

## Đối chiếu nhiệm vụ

| Mã | Kết quả phần TV1 | Bằng chứng / phần còn chờ |
|---|---|---|
| N01–N03 | Tái sử dụng đặc tả/API/khung đã có (Sheet đã tích) | Không tự khai tên người, xác nhận nhóm hay phiên bản máy của người khác |
| A01 | App/router/config/dependency/health và readiness đã có; bổ sung validation cấu hình | Test cấu hình, OpenAPI, chạy server thật; chưa thay thế xác nhận cài trên máy thành viên khác |
| A02 | DB/session dùng chung, PRAGMA, get_db rollback/close và xử lý DB bận | Test khóa DB, rollback, migration DB mới; schema LMS/thi D01 vẫn do TV3 phối hợp TV4 |
| A03 | Chuẩn lỗi và auth response model OpenAPI, pagination, UTC helper | Test 422/500/503, không lộ input nhạy cảm, request ID, bounds phân trang và timezone |
| A04 | Argon2id, session hash/cookie 8h, login/me/logout; login thay cookie thu hồi phiên bị thay | Test đăng nhập/sai mật khẩu/logout/hash/khởi động lại app; seed teacher đã có; dataset khóa học/student D02 còn chờ TV3 |
| A05 | Gate đổi mật khẩu, 8–128 ký tự, khác cũ; thu hồi mọi phiên | Test student mới, mật khẩu ngắn/dài/giống, login lại sau đổi; CSRF ổn định giữa tab |
| A08 | Proxy template hiện có; bổ sung start_proxy.ps1 và check_lan.py | Probe qua server thật trên loopback đã đạt; chưa có frontend thật, Nginx cài sẵn và kiểm tra từ máy LAN thứ hai nên chưa nghiệm thu toàn luồng |
| Q01 | Chạy suite nền và lập báo cáo ghép ngày 24 | Chưa đạt điều kiện login qua frontend/DB demo đủ/compile ba ngôn ngữ; cần F01/F03, D01/D02, J02 và A08 được kiểm chứng |

A01–A05 có code và kiểm thử backend; các mốc cần người khác xác nhận không được coi là hoàn thành tích hợp chỉ vì unit/integration test đạt. Không tự đánh dấu toàn bộ ngày Done.

## Code bổ sung

- server/app/core/config.py: đọc env từng instance; lỗi origin, bool, URL và đường dẫn DB báo sớm; đường dẫn SQLite độc lập cwd.
- server/app/core/database.py: get_db để các module dùng session theo request; rollback khi có lỗi, đóng session cuối vòng đời.
- server/app/schemas/common.py: ErrorResponse, Page, Pagination, utc_iso; schemas auth riêng có response model.
- server/app/main.py: lỗi OpenAPI đúng schema, giữ HTTPException headers, no-store cho API và /api/ready kiểm tra schema auth.
- modules/auth/: phiên mới thay thế cookie cũ; CSRF ổn định theo phiên; kiểm tra phiên bị thu hồi trong lúc request và optimistic update khi đổi mật khẩu.
- scripts/check_lan.py: kiểm tra API qua public origin; tùy chọn login/CSRF/WS/logout tương tác, không in mật khẩu/cookie.
- scripts/start_proxy.ps1: kiểm tra cấu hình trước khi khởi động Nginx; runtime log/pid nằm .runtime/ đã ignore.

## Kết quả kiểm chứng

Python 3.12 Windows; dùng dependency đã pin của repository. Lệnh từ gốc checkout:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

**27 tests passed**, gồm 11 test nền và 16 ca bổ sung (có tham số hóa). Một cảnh báo deprecation của Starlette TestClient về httpx, không có test fail. Kiểm thử thật có migration DB trống, khởi động Uvicorn loopback và chạy công cụ probe. Đây không phải kết quả benchmark hay LAN hai máy.

Trong phiên làm việc này Nginx không có trong PATH. Docker CLI có nhưng không kết nối được Docker Desktop Linux daemon. Không tự cài/chạy môi trường judge hay làm thay frontend để giả hoàn thành phụ thuộc.

## Hướng dẫn A08 và bàn giao Q01

1. TV3 cung cấp migration/seed LMS theo cùng Base và session; không reset teacher có sẵn.
2. TV2 hoàn thành F01/F03 trong client/, gọi /api và /ws cùng origin; không hard-code IP/localhost trong trang.
3. Tại server, thêm origin web LAN thực vào server/.env (ví dụ http://192.168.1.10:8080), khởi động lại backend bằng scripts/start_server.ps1. Địa chỉ chỉ là ví dụ, không phải IP đã xác minh.
4. TV2 chạy frontend cổng 3000. Với Nginx đã cài, chạy:

```powershell
.\scripts\start_proxy.ps1 -NginxPath 'C:\tools\nginx\nginx.exe'
```

5. Chỉ mở TCP 8080 trên mạng Private/LAN theo chính sách máy; backend vẫn loopback. Không mở firewall tự động trên máy người dùng. Thử từ máy client khác:

```powershell
.\.venv\Scripts\python.exe scripts/check_lan.py --base-url http://192.168.1.10:8080
.\.venv\Scripts\python.exe scripts/check_lan.py --base-url http://192.168.1.10:8080 --username teacher-demo
```

Username phải là tài khoản đã được nhóm tạo; script hỏi mật khẩu và không lưu. Chỉ tài khoản đã đổi mật khẩu được kiểm tra WS đầy đủ. Chạy script trên mỗi client có Python/dependencies, đồng thời TV2 kiểm tra bằng trình duyệt thật; probe không thay thế nghiệm thu UI.

6. TV4 xác minh J02: Docker daemon chạy và C/C++/Java compile/run thật. TV1 chỉ ghép khi có kết quả, không tự tích thay.
7. Ghi ngày, máy, origin/port, kết quả browser/probe và lỗi tái hiện vào docs/testing.md; rồi cập nhật trạng thái A08/Q01 sau khi nhóm xác nhận.

## Git và các thay đổi đang có

Triển khai trên worktree và nhánh codex/member1-day-24 từ origin/develop. Không commit/gộp các thay đổi phân công đang chưa commit trong D:/Projects/LAN-LMS; các file đó giữ nguyên. Nhánh được push riêng để review trước khi ghép vào develop; chưa thay đổi main.
