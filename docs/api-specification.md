# API Specification — LAN-LMS

- **Phiên bản:** 1.0 — hợp đồng API khởi tạo
- **Backend:** Python + FastAPI
- **Giao thức:** HTTP REST API và WebSocket
- **Base URL phát triển:** `http://localhost:8000`
- **Base URL demo LAN:** `http://<SERVER_IP>:8000`

Đây là hợp đồng API ban đầu. Trước khi triển khai endpoint, nhóm phải thống nhất các trường request/response cụ thể. Khi thay đổi hợp đồng, cần cập nhật file này và thông báo các thành viên liên quan.

## 1. Quy ước chung

- Dữ liệu request/response dùng JSON, trừ endpoint upload/download file hoặc export CSV.
- Tên trường JSON dùng `snake_case`.
- Thời gian trao đổi qua API dùng ISO 8601; nhóm phải thống nhất cách lưu và hiển thị múi giờ.
- Backend chịu trách nhiệm xác thực, phân quyền và kiểm tra dữ liệu.
- Frontend không được xem việc ẩn nút giao diện là biện pháp phân quyền.
- Không trả password hash, mật khẩu ban đầu, token bí mật hoặc dữ liệu nhạy cảm không cần thiết về frontend.
- Các endpoint quản lý khóa học phải kiểm tra quyền của giảng viên đối với khóa học tương ứng.

## 2. Quy ước lỗi

Dùng HTTP status code phù hợp và response lỗi thống nhất:

```json
{
  "detail": "Invalid date_of_birth",
  "code": "INVALID_CSV_ROW"
}
```

Các mã lỗi dự kiến:

| HTTP | Ý nghĩa |
|---|---|
| 400 | Dữ liệu không hợp lệ |
| 401 | Chưa xác thực hoặc thông tin đăng nhập không hợp lệ |
| 403 | Không có quyền thực hiện |
| 404 | Không tìm thấy tài nguyên |
| 409 | Trùng dữ liệu hoặc xung đột trạng thái |
| 413 | File vượt quá dung lượng cho phép |
| 422 | Dữ liệu request không đạt kiểm tra schema |
| 500 | Lỗi hệ thống không dự kiến |

Không trả stack trace, secret hoặc thông tin nội bộ nhạy cảm cho client.

## 3. Authentication

### `POST /api/auth/login`

Mục đích: đăng nhập.

Request khởi tạo:

```json
{
  "student_id": "SV001",
  "password": "example-password"
}
```

Đây là ví dụ cho tài khoản sinh viên. Nhóm cần thống nhất cách đăng nhập của giảng viên trong cùng API hoặc endpoint riêng.

Response thành công cần cung cấp thông tin người dùng và trạng thái có bắt buộc đổi mật khẩu hay không. Cơ chế cookie/session hoặc token phải được chốt trước khi frontend tích hợp.

Các trường dự kiến:
- `user_id`
- `username`
- `role`
- `must_change_password`

Không trả password hash.

### `POST /api/auth/logout`

Mục đích: kết thúc phiên đăng nhập hoặc thu hồi token theo cơ chế xác thực đã chọn.

### `GET /api/auth/me`

Mục đích: lấy thông tin tài khoản hiện tại.

Response dự kiến:

```json
{
  "user_id": 1,
  "username": "SV001",
  "role": "student",
  "must_change_password": true
}
```

### `POST /api/auth/change-password`

Mục đích: đổi mật khẩu.

Request dự kiến:

```json
{
  "current_password": "example-old-password",
  "new_password": "example-new-password"
}
```

Backend phải kiểm tra chính sách mật khẩu và cập nhật trạng thái bắt buộc đổi mật khẩu khi đổi thành công.

## 4. Courses

| Method | Endpoint | Quyền dự kiến | Mục đích |
|---|---|---|---|
| GET | `/api/courses` | Người dùng đã đăng nhập | Liệt kê khóa học được phép xem |
| POST | `/api/courses` | Teacher | Tạo khóa học |
| GET | `/api/courses/{course_id}` | Thành viên có quyền | Xem chi tiết |
| PATCH | `/api/courses/{course_id}` | Teacher có quyền quản lý | Cập nhật khóa học |
| GET | `/api/courses/{course_id}/students` | Teacher có quyền quản lý | Xem danh sách sinh viên |

Nhóm phải thống nhất các trường khóa học tối thiểu, chẳng hạn `course_code`, `name`, `description`, `start_date` và `end_date`.

## 5. Import CSV

### `POST /api/courses/{course_id}/students/import-preview`

Mục đích: kiểm tra file CSV trước khi import. Đây là endpoint nhận file upload.

CSV dùng các cột:

```csv
student_id,full_name,date_of_birth,class_name,email
SV001,Nguyen Van An,15032005,D23CNPM01,an@example.com
SV002,Tran Thi Binh,02112005,D23CNPM01,binh@example.com
```

Kết quả preview cần có:
- Tổng số dòng và số dòng hợp lệ.
- Dòng lỗi và lý do lỗi.
- Mã sinh viên trùng trong file.
- Tình trạng tài khoản đã tồn tại hoặc tài khoản mới.
- Các khác biệt dữ liệu cần giảng viên xem xét.

### `POST /api/courses/{course_id}/students/import-confirm`

Mục đích: xác nhận và thực hiện import sau khi xem preview.

Backend phải kiểm tra quyền, tránh tạo tài khoản hoặc đăng ký khóa học trùng, không ghi đè mật khẩu tài khoản cũ và không xuất mật khẩu vào báo cáo.

Nhóm cần thống nhất cách liên kết bước confirm với dữ liệu preview để tránh dùng một preview cũ hoặc bị sửa đổi.

## 6. Materials

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/api/courses/{course_id}/materials` | Liệt kê tài liệu được phép xem |
| POST | `/api/courses/{course_id}/materials` | Teacher upload tài liệu |
| GET | `/api/materials/{material_id}/download` | Tải tài liệu khi có quyền |

File cần được kiểm tra dung lượng, loại file và quyền truy cập. Không dùng tên file người dùng gửi làm đường dẫn lưu file trực tiếp.

## 7. Attendance

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/api/courses/{course_id}/attendance-sessions` | Teacher tạo phiên QR |
| GET | `/api/attendance-sessions/{session_id}` | Xem thông tin phiên |
| POST | `/api/attendance-sessions/{session_id}/check-in` | Student điểm danh |
| GET | `/api/attendance-sessions/{session_id}/records` | Teacher xem kết quả |

Token điểm danh phải có thời hạn. Backend phải kiểm tra sinh viên đã đăng ký khóa học, phiên còn hiệu lực và quy tắc chống điểm danh trùng.

## 8. Assignments

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/api/courses/{course_id}/assignments` | Teacher tạo bài tập |
| POST | `/api/assignments/{assignment_id}/submissions` | Student nộp file |
| GET | `/api/assignments/{assignment_id}` | Xem đề và thông tin bài tập |

Backend kiểm tra hạn nộp, dung lượng, loại file và quyền truy cập.

## 9. Coding exams và submissions

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/api/courses/{course_id}/coding-exams` | Teacher tạo kỳ thi |
| GET | `/api/coding-exams/{exam_id}/problems` | Lấy đề được phép xem |
| POST | `/api/problems/{problem_id}/submissions` | Student gửi code |
| GET | `/api/submissions/{submission_id}` | Xem trạng thái và kết quả được phép công bố |

Submission phải được lưu thành bản ghi riêng. Gửi bài mới không được ghi đè lịch sử bài nộp cũ.

Các trạng thái dùng thống nhất:

- `Pending`
- `Compiling`
- `Running`
- `Accepted`
- `Wrong Answer`
- `Compile Error`
- `Time Limit Exceeded`
- `Memory Limit Exceeded`
- `Runtime Error`
- `System Error`

Backend phải kiểm tra quyền dự thi, thời hạn, ngôn ngữ và giới hạn dữ liệu. Code phải được xử lý bởi Judge Worker, không chạy trực tiếp trong tiến trình API.

## 10. Gradebook

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/api/courses/{course_id}/gradebook` | Xem bảng điểm theo quyền |
| PATCH | `/api/courses/{course_id}/grades` | Teacher cập nhật điểm |
| GET | `/api/courses/{course_id}/gradebook/export-csv` | Teacher xuất CSV |

Các trường điểm cần được thống nhất; dự kiến có mã sinh viên, họ tên, lớp, chuyên cần, bài tập, giữa kỳ, cuối kỳ và tổng kết.

Backend tính điểm tổng kết. Không coi điểm chưa nhập là 0 nếu chính sách chưa quy định như vậy.

## 11. WebSocket

WebSocket dùng để cập nhật:
- Trạng thái phiên thi.
- Trạng thái kết nối nếu cần.
- Trạng thái submission và kết quả chấm.

Kết nối phải được xác thực và kiểm tra quyền. Sự kiện chỉ được gửi đến người dùng có quyền xem. Khi WebSocket ngắt, frontend phải có thể lấy trạng thái mới nhất qua REST API.

Đường dẫn WebSocket cụ thể và định dạng sự kiện cần được chốt trước khi triển khai.

## 12. Quy tắc phối hợp API

1. Thành viên backend đề xuất request/response trước khi viết endpoint.
2. Thành viên frontend tích hợp theo đúng hợp đồng đã thống nhất.
3. Thành viên database thống nhất tên trường và quan hệ dữ liệu.
4. Thành viên Judge thống nhất cấu trúc submission, trạng thái và kết quả với backend.
5. Mọi thay đổi hợp đồng phải cập nhật file này và được thông báo trong nhóm.
6. Có thể dùng OpenAPI/Swagger của FastAPI để kiểm tra endpoint, nhưng tài liệu này vẫn là nơi nhóm ghi các quyết định nghiệp vụ.
