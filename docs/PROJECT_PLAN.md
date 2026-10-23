# Đặc tả và kế hoạch triển khai LAN-LMS

- **Phiên bản:** 1.0
- **Thời gian dự kiến:** 22/10/2026 – 31/10/2026
- **Quy mô nhóm:** 4 thành viên
- **Môi trường mục tiêu:** Windows, một máy chủ trong mạng LAN

## 1. Mục tiêu

Xây dựng hệ thống LMS và thi lập trình trên mạng LAN theo mô hình Client–Server. Hệ thống có đăng nhập, phân quyền, quản lý khóa học, import CSV, tài liệu, bài tập, thi lập trình, điểm danh QR, bảng điểm và xuất CSV.

## 2. Công nghệ đã thống nhất

| Thành phần | Công nghệ |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| API nghiệp vụ | REST API |
| Cập nhật gần thời gian thực | WebSocket |
| Database demo | SQLite |
| ORM/migration | SQLAlchemy, Alembic |
| Chấm bài | Judge Worker riêng |
| Ngôn ngữ chấm | C/C++, Java |
| Lưu file | Ổ đĩa máy chủ, database lưu metadata |

## 3. Vai trò

### Giảng viên
- Tạo và quản lý khóa học.
- Import sinh viên bằng CSV.
- Upload tài liệu và tạo lịch.
- Tạo phiên điểm danh QR.
- Tạo bài tập, kỳ thi và test case.
- Theo dõi bài nộp, quản lý điểm và xuất CSV.

### Sinh viên
- Đăng nhập bằng mã sinh viên.
- Đổi mật khẩu ban đầu.
- Xem khóa học và tài liệu được cấp quyền.
- Điểm danh khi có phiên hợp lệ.
- Nộp bài tập và thi lập trình.
- Xem trạng thái chấm và điểm được công bố.

### Judge Worker
- Nhận job từ backend.
- Biên dịch và chạy bài C/C++ hoặc Java.
- Chấm test case và trả kết quả.
- Thực thi code trong môi trường cô lập có giới hạn tài nguyên.

## 4. Quy tắc import CSV

Các cột bắt buộc: `student_id`, `full_name`, `date_of_birth`, `class_name`. Cột `email` là tùy chọn.

- Username là mã sinh viên.
- Mật khẩu ban đầu là ngày sinh theo định dạng `DDMMYYYY`.
- Ngày sinh phải được xử lý như chuỗi để giữ số 0 ở đầu.
- Tài khoản mới phải đổi mật khẩu lần đầu.
- Mật khẩu phải được hash, không lưu dạng văn bản thuần.
- Import lại không được tạo tài khoản trùng hoặc ghi đè mật khẩu tài khoản đã tồn tại.
- Cần có bước xem trước, báo lỗi và xác nhận import.

## 5. Quy tắc thi lập trình

- Bắt buộc hỗ trợ C/C++ và Java.
- Hỗ trợ stdin/stdout và file input/output.
- Lưu lịch sử các lần nộp bài.
- Có trạng thái biên dịch, chạy và chấm bài.
- Có giới hạn thời gian, bộ nhớ và quyền truy cập file.
- Không chạy code sinh viên trong tiến trình API.
- Không để sinh viên xem test ẩn hoặc output mong đợi của test ẩn.
- Bài nhiều file/project là phần mở rộng, trừ khi rubric yêu cầu.

## 6. Điểm danh và bảng điểm

Điểm danh QR phải dùng token ngẫu nhiên có thời hạn, kiểm tra sinh viên thuộc khóa học và ngăn điểm danh trùng theo chính sách.

Trọng số mặc định dùng để demo:

- Chuyên cần: 10%
- Bài tập: 20%
- Giữa kỳ: 30%
- Cuối kỳ: 40%

Giảng viên có thể cấu hình trọng số. Tổng trọng số phải bằng 100% trước khi tính hoặc công bố điểm tổng kết. Phải phân biệt điểm chưa có với điểm 0.

## 7. Theo dõi phiên thi

Ghi nhận thời gian bắt đầu/kết thúc, trạng thái phiên, lịch sử nộp bài và trạng thái kết nối khi cần. IP quan sát được chỉ là thông tin tham khảo, không phải bằng chứng duy nhất để kết luận danh tính hoặc gian lận.

Không triển khai giám sát webcam, màn hình hoặc ghi phím trong phạm vi ban đầu.

## 8. Phân công

### Thành viên 1 — Backend và tích hợp
FastAPI, xác thực, phân quyền, API nền tảng, WebSocket và tích hợp.

### Thành viên 2 — Frontend
Next.js, giao diện giảng viên/sinh viên, import CSV preview, hiển thị bài nộp và điểm.

### Thành viên 3 — Database và nghiệp vụ LMS
Schema, migration, hồ sơ sinh viên, khóa học, CSV import, tài liệu, QR, bảng điểm, backup.

### Thành viên 4 — Assignment và Judge Worker
Nộp file, C/C++, Java, stdin/stdout, file I/O, test case, giới hạn tài nguyên và kết quả chấm.

## 9. Lộ trình dự kiến

| Ngày | Mục tiêu |
|---|---|
| 22/10 | Chốt repository, kiến trúc, schema và API |
| 23/10 | Dựng frontend/backend/database và đăng nhập |
| 24/10 | Khóa học, import CSV, tài khoản và tài liệu |
| 25/10 | Bài tập file và Judge C/C++/Java |
| 26/10 | Tích hợp luồng nộp bài và chấm |
| 27/10 | QR, bảng điểm và export CSV |
| 28/10 | Kiểm thử trên mạng LAN |
| 29/10 | Hoàn thiện báo cáo |
| 30/10 | Đóng băng tính năng, sửa lỗi |
| 31/10 | Chạy demo và bàn giao |

## 10. Tiêu chí hoàn thành

Luồng ưu tiên:

Giảng viên đăng nhập → tạo khóa học → import CSV → sinh viên đăng nhập và đổi mật khẩu → xem tài liệu → nộp bài → gửi code → nhận kết quả chấm → điểm danh → xem bảng điểm → xuất CSV.

Chỉ xác nhận hoàn thành khi luồng đã được tích hợp và kiểm thử thực tế.

## 11. Quyết định cần đối chiếu với rubric

REST API và WebSocket không đồng nghĩa với việc tự xây dựng TCP Socket thuần. Nhóm phải kiểm tra yêu cầu chính thức của môn học trước khi chốt phần giao tiếp mạng.

## 12. Tài liệu liên quan

Xem `docs/api-specification.md` để thống nhất endpoint, dữ liệu request/response và quy tắc phân quyền.
