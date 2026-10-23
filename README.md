# LAN-LMS

Hệ thống quản lý học tập (LMS) và thi lập trình qua mạng LAN theo mô hình Client–Server.

## 1. Mục tiêu

Xây dựng hệ thống cho phép giảng viên quản lý khóa học, sinh viên, tài liệu, điểm danh, bài tập, kỳ thi lập trình và bảng điểm. Sinh viên truy cập bằng trình duyệt trên các máy tính trong cùng mạng LAN.

## 2. Công nghệ dự kiến

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- Giao tiếp: REST API và WebSocket
- Database: SQLite cho bản demo ban đầu
- ORM và migration: SQLAlchemy, Alembic
- Judge Worker: chấm bài C/C++ và Java trong môi trường cô lập
- Môi trường triển khai: Windows, mạng LAN

## 3. Chức năng chính

- Đăng nhập, phân quyền giảng viên và sinh viên
- Quản lý khóa học và import danh sách sinh viên từ CSV
- Tạo tài khoản sinh viên và yêu cầu đổi mật khẩu lần đầu
- Upload và tải tài liệu khóa học
- Nộp bài tập bằng file
- Thi lập trình C/C++ và Java, hỗ trợ stdin/stdout và file input/output
- Theo dõi trạng thái bài nộp và kết quả chấm
- Điểm danh bằng QR
- Quản lý điểm, cấu hình trọng số và xuất bảng điểm CSV
- Chạy hệ thống trong mạng LAN

## 4. Tài liệu dự án

- [Đặc tả và kế hoạch triển khai](docs/PROJECT_PLAN.md)
- [Đặc tả API](docs/api-specification.md)

## 5. Cấu trúc repository

- `client/`: ứng dụng frontend
- `server/`: backend và API
- `judge/`: hàng đợi và worker chấm bài
- `storage/`: tài liệu và bài nộp lưu trên máy chủ
- `database/`: migration và dữ liệu khởi tạo
- `scripts/`: script cài đặt, chạy và backup
- `docs/`: tài liệu kỹ thuật và hướng dẫn
- `tests/`: kiểm thử
- `REPORT/`: báo cáo đồ án

Các thư mục ứng dụng sẽ được tạo trong các giai đoạn triển khai tiếp theo.

## 6. Trạng thái dự án

Đây là repository khởi tạo. Chỉ đánh dấu một chức năng là hoàn thành sau khi đã tích hợp và kiểm thử; giao diện minh họa chưa được xem là chức năng hoàn chỉnh.

## 7. Quy tắc làm việc nhóm

- Không commit trực tiếp lên `main`.
- Mỗi tính năng làm trên một nhánh riêng.
- Thay đổi API phải được thống nhất và cập nhật tài liệu.
- Không commit mật khẩu, token, secret hoặc dữ liệu cá nhân thật.
- Tích hợp và kiểm thử thường xuyên trên nhánh chung của nhóm.

## 8. Thời gian dự kiến

22/10/2026 – 31/10/2026.

## 9. Lưu ý

REST API và WebSocket phù hợp với kiến trúc web Client–Server, nhưng nếu yêu cầu môn học bắt buộc xây dựng TCP Socket thuần thì nhóm phải đối chiếu rubric và bổ sung thành phần phù hợp.
