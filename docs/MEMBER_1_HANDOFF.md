> Nhật ký mốc trước bản hoàn thiện. Trạng thái hiện hành xem README, PROJECT_PLAN 1.2 và API 1.2.

# Thành viên 1 — Backend nền tảng

Triển khai ngày 24/10/2026 trên nhánh `codex/member-1-backend`. Không bao gồm code nghiệp vụ thuộc thành viên 2/3/4 và không khai báo toàn bộ sản phẩm đã hoàn thành.

## Phần đã có

- FastAPI app factory `create_app(Settings(...))`; SQLite WAL, foreign keys, busy timeout, SQLAlchemy session dùng riêng cho từng thao tác.
- Alembic revision `0001_auth`: users, auth_sessions, login_attempts. Không tự create_all khi chạy thật.
- Năm API auth đúng hợp đồng: login, logout, me, csrf, change-password; cookie HttpOnly/SameSite=Lax, hash Argon2id, hash session token, phiên tuyệt đối 8 giờ.
- Kiểm tra Origin/CSRF, bắt buộc đổi mật khẩu, giới hạn login bền vững trong DB (10 lần thất bại/phút/IP, tính thêm request đang xử lý để chống vượt giới hạn khi đồng thời).
- Đổi mật khẩu thu hồi toàn bộ session. Không reset mật khẩu khi seed lại username cũ. Tài khoản inactive và phiên hết hạn bị từ chối cả HTTP và WS.
- Chuẩn lỗi, request ID, không phản chiếu password/input lỗi hoặc SQL trong response; no-store cho auth.
- Dependency `current_user`, `learning_user`, `require_role`, `require_course_access` để các module dùng lại, fail closed khi chưa đăng ký policy khóa học.
- `/ws` kiểm tra session/Origin, heartbeat/ack, giới hạn message, cleanup, hàng đợi từng client có giới hạn, lọc recipients từ module tin cậy; `/api/health` kiểm tra kết nối DB.
- Cấu hình Nginx chuyển tiếp `/api`, `/ws`, frontend cùng origin; script Windows, dependency pin và kiểm thử.

## Cài và chạy

Tất cả lệnh dưới chạy từ thư mục gốc repository. Yêu cầu Python 3.12; trên Windows có thể chạy `scripts/setup_windows.ps1` hoặc thực hiện từng bước:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server/requirements.lock
Copy-Item server/.env.example server/.env
.\.venv\Scripts\python.exe -m alembic -c server/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m server.app.seed
.\scripts\start_server.ps1
```

Seed hỏi username/password riêng trên terminal, không truyền password trong command line. Không seed tài khoản mặc định. `.env`/DB không đưa lên Git. Không ghi đè `.env` đã cấu hình. File lock có cả thư viện kiểm thử; requirements.txt là dependency chạy và requirements-dev.txt bổ sung dependency phát triển.

Chạy kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Mở `http://127.0.0.1:8000/docs` xem OpenAPI; trình duyệt Swagger phải gửi Origin đúng allowlist và CSRF cho endpoint có session, do đó thao tác đầy đủ nên dùng frontend hoặc HTTP client. Endpoint health là public; không xuất cấu hình bí mật. Health không khẳng định schema đã migrate (migration là bước bắt buộc).

## LAN và cùng origin

Cài Nginx riêng, dùng `scripts/nginx.conf` làm cấu hình; frontend thành viên 2 chạy 127.0.0.1:3000, backend 127.0.0.1:8000. Browser mở `http://SERVER_IP:8080`; thêm đúng địa chỉ này vào ALLOWED_ORIGINS (không wildcard), rồi khởi động lại backend. Frontend gọi `/api/...`, WebSocket dùng host hiện tại và `/ws`.

Nginx ghi đè X-Forwarded-For bằng IP thực; Uvicorn chỉ tin proxy loopback. Không mở trực tiếp cổng backend ra LAN hay cho proxy không tin cậy gửi forwarded headers. Nhiều máy chung NAT vẫn có thể dùng chung rate limit. HTTPS cần cấu hình chứng chỉ/proxy riêng và SECURE_COOKIE=true; HTTP demo không mã hóa mật khẩu trên đường truyền.

Backend/test/migration đã chạy trên môi trường Python 3.12 Windows. Nginx và frontend chưa có phiên chạy tích hợp LAN thực tế, nên cấu hình proxy là tài nguyên bàn giao cần kiểm thử khi có frontend; không coi checklist nhiều máy là đã đạt.

## Thành viên 2: dùng auth và WS

1. POST `/api/auth/login` body `{username,password}`, browser tự gửi Origin, fetch dùng credentials same-origin.
2. GET `/api/auth/me`; nếu must_change_password thì đưa đến trang đổi mật khẩu.
3. GET `/api/auth/csrf`, giữ token trong bộ nhớ; gửi X-CSRF-Token cho các POST/PATCH/DELETE. Token ổn định trong cùng session kể từ bản ngày 24: mở tab khác không làm mất hiệu lực; khi nhận INVALID_CSRF thì lấy lại token; không tự retry thao tác không có idempotency nếu chưa biết kết quả.
4. Đổi mật khẩu trả 204, đưa về login. Logout trả 204; xóa trạng thái người dùng phía client.
5. Mở WS sau khi đăng nhập và đổi mật khẩu. Với `{type:"heartbeat",id}` trả `{type:"heartbeat.ack",id}`. Không có thao tác subscribe user/course tùy ý từ browser.
6. Reconnect sau 1/2/4/8 giây, tối đa 15 giây với jitter. Sau reconnect GET trạng thái; polling bài chưa xong 3 giây/lần khi WS mất; dừng khi rời trang hoặc terminal. Đây là trách nhiệm frontend, chưa có code frontend trong nhánh này.

## Thành viên 3: database và quyền khóa học

Không tạo bảng users khác; import `User` và dùng hasher để tạo student với must_change_password=true. Mọi model mới dùng cùng Base, migration mới có down_revision='0001_auth'. Không sửa revision đã dùng trên máy nhóm nếu có thể bổ sung revision mới.

Khi gắn router course, đăng ký policy đồng bộ:

```python
def course_access(user, course_id):
    # Query DB: teacher sở hữu course hoặc student có enrollment.
    # Trả False nếu khóa học không tồn tại/không thuộc quyền; không tin body role/owner.
    ...

app.state.course_access = course_access
```

Endpoint dùng `Depends(require_course_access)` với path parameter course_id; tạo/sửa khóa học còn phải dùng require_role('teacher') và kiểm tra ownership. Các dependency không thay thế kiểm tra quyền trên material/submission cụ thể. Chưa có bảng course/enrollment nên policy thật phải do module LMS cung cấp; mặc định trả 503 MODULE_NOT_READY, không cấp quyền giả.

## Thành viên 4 và 1: sự kiện sau commit

Sau khi commit trạng thái, route async gọi:

```python
await app.state.hub.publish('submission.updated', {
    'submission_id': submission.id,
    'status': submission.status,
    'version': submission.version,
}, recipient_ids={submission.user_id, owning_teacher_id})
```

IDs phải được tính từ database. Không gửi test ẩn/source/secret. Hàm publish chạy trên event loop của app; worker bên ngoài không được import hub riêng rồi mong browser nhận. Bản đầu API có thể dùng vòng poll DB lấy cập nhật từ worker và publish; thành viên 4 phối hợp bổ sung khi có job/result schema. Chạy đúng một Uvicorn worker vì hub ở memory; scale nhiều API worker cần pub/sub chung.

Hub hỗ trợ submission.updated, exam.updated, session.updated. Chưa có exam_sessions nên việc ghi last_seen_at/IP vào DB và phát session.updated theo phiên thi chờ module thi; không giả lập online trong bảng chưa tồn tại. App chỉ theo dõi connection sống và xác thực lại trước gửi.

## Kiểm chứng và giới hạn

`tests/test_member1.py` kiểm thử login/logout, cookie, Origin/CSRF, mật khẩu/thu hồi toàn bộ session, phân quyền, policy fail closed, expiry/inactive, rate limit, WS heartbeat/delivery/revocation/timeout và migration upgrade/downgrade/upgrade.

Không có secret/DB mẫu thật được commit. Chưa xác nhận hiệu năng, benchmark, frontend hay judge end-to-end, LAN hai máy và sandbox. Nginx phải được kiểm thử trên máy triển khai. Khi thêm router, áp dụng learning_user hoặc dependency chuyên biệt cho mọi endpoint cần bảo vệ. Không sửa current_user để bỏ bắt buộc đổi mật khẩu của các module khác.

## Cập nhật cấu trúc thư mục

Auth router hiện ở server/app/modules/auth/router.py, export qua modules/auth/__init__.py; main.py giữ nguyên import. Các file khung mới được mô tả tại [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md). Không coi các module router rỗng là đã tích hợp.

## Bổ sung nghiệm thu ngày 24/10

Xem [MEMBER_1_DAY_24.md](MEMBER_1_DAY_24.md) để đối chiếu A01–A05, A08 và Q01 với bảng phân công. Có thêm /api/ready (kiểm tra các bảng auth đã migrate), get_db dependency, common Page/Pagination/utc_iso, response model OpenAPI, start_proxy.ps1 và check_lan.py. Frontend và Docker vẫn cần kết quả tích hợp thật từ thành viên phụ trách.
