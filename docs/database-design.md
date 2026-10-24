# D01 — Thiết kế dữ liệu chung (24/10/2026)

**Trạng thái:** Bản thiết kế và ORM/migration đề xuất, chờ TV1 kiểm tra và TV4 xác nhận phần Judge. Không tuyên bố đã được các thành viên phê duyệt. Nhánh dự kiến `codex/feature/database-base` (ZIP không chứa `.git`, không thể tạo Git branch trong bản giao này).

## Cơ sở đối chiếu

- `docs/PROJECT_PLAN.md` mục 60.1–60.4, `docs/api-specification.md` 1.1 và `docs/MEMBER_1_HANDOFF.md`.
- TV1 đã có `users`, `auth_sessions`, `login_attempts` trong `server/app/core/database.py`, revision `0001_auth`. **Không khai báo lại**, không sửa migration cũ.
- Các ORM chung đặt trong `server/app/models/__init__.py`; migration tiếp nối `0002_database_base`. Cấu hình WAL, FK và busy timeout của TV1 được giữ nguyên.

## Danh mục bảng

**TV1, hiện hữu (3):** `users`, `auth_sessions`, `login_attempts`.

**D01 bổ sung (26):**

- Đào tạo: `classes`, `students`, `teachers`, `courses`, `course_classes`, `course_teachers`, `course_enrollments`.
- CSV và LMS: `csv_import_previews`, `course_materials`, `calendar_events`, `attendance_sessions`, `attendance_records`, `assignments`, `assignment_submissions`.
- Thi và Judge: `coding_exams`, `exam_registrations`, `exam_sessions`, `problems`, `test_cases`, `code_submissions`, `judge_jobs`, `judge_results`.
- Tính lặp và điểm: `idempotency_keys`, `grade_components`, `grades`, `audit_logs`.

**Tổng số bảng sau migration: 29**, gồm 3 bảng auth đã tồn tại và 26 bảng mới. `submission_test_results` **không tạo** theo yêu cầu mới nhất của người dùng là không lưu kết quả từng test; điều này khác mục 60.2/60.4 và API 1.1, cần TV4 và TV1 xác nhận cập nhật hợp đồng. Vẫn giữ `test_cases` làm dữ liệu chấm.

## Quan hệ, khóa và nullable

Các cột được định nghĩa cụ thể trong `server/app/models/__init__.py`, là nguồn schema của migration. Tất cả bảng mới có PK `id` integer. FK bắt buộc là NOT NULL trừ khi model khai báo `Mapped[..., None]`; FK dùng `ON DELETE RESTRICT` để tránh xóa dây chuyền dữ liệu học tập và bài thi. FK đều được index. Thời gian nghiệp vụ trong bảng mới dùng epoch UTC dạng float (tương thích kiểu `expires_at` trong auth); API chuyển ISO8601.

**Unique nghiệp vụ:**

- `users.username`, `students.student_code`, `students.user_id`, `teachers.user_id`, `classes.class_code`.
- `courses(course_code, semester, academic_year)`; `course_classes(course_id,class_id)`; `course_teachers(course_id,teacher_id)`; `course_enrollments(course_id,student_id)`.
- `csv_import_previews.preview_id`, `attendance_sessions.token_hash`, `attendance_records(session_id,student_id)`.
- `assignment_submissions(assignment_id,student_id,attempt_no)`; `exam_registrations(exam_id,student_id)`; `exam_sessions.registration_id`.
- `code_submissions(exam_session_id,problem_id,attempt_no)`; `judge_jobs.submission_id`; `judge_results.submission_id`.
- `idempotency_keys(user_id,method,path,key)`; `grade_components(course_id,component_code)`; `grades(component_id,student_id)`.

**Nullable có chủ đích:** `grades.score` (chưa có điểm), `grades.source_exam_id` (điểm nhập tay), `exam_sessions.total_score` (chưa chấm xong), `judge_results.score` (lỗi hạ tầng), `code_submissions.score` (đang xử lý), `judge_jobs.attempt_id/worker_id/lease_until` (chưa nhận job), `csv_import_previews.confirmed_at` (chưa confirm), `auth_sessions.csrf_hash` (đã có từ TV1), `idempotency_keys.response_status/resource_id` (request đang xử lý).

## Luồng nghiệp vụ và transaction

1. **CSV:** lưu `csv_import_previews` gắn `course_id`, `teacher_id`, dữ liệu chuẩn hóa và hash; hết hạn sau 15 phút. Confirm kiểm tra lại hồ sơ/enrollment và import all-or-nothing. Idempotency scope user+method+path+key; hash request phải khớp.
2. **Khóa học:** lớp và giảng viên N–N; enrollment của từng sinh viên là dữ liệu riêng. Kiểm tra quyền dựa vào course_teachers/course_enrollments, không tin course_id từ client.
3. **Thi:** một registration/exam/student, một session/registration; nhiều code submissions/session/problem với `attempt_no` tăng. Không tạo session mới khi reconnect. Bài nộp và job phải commit trong cùng transaction.
4. **Judge:** `judge_jobs` có lease/attempt để worker claim có kiểm soát; `judge_results` là kết quả tổng hợp của submission, không chứa input/output test ẩn. Worker chỉ ghi khi lease attempt vẫn hợp lệ. `is_correct` phản ánh accepted toàn bộ test; `score` có thể khác 0 dù `is_correct=false` nếu tính điểm từng phần theo đặc tả.
5. **Điểm:** `courses.grades_published` mặc định phải được service đặt false khi tạo khóa học; `coding_exams.results_published` dùng để chốt điểm thi. Theo quyết định mới của người dùng, điểm final của sinh viên là **MAX** điểm các đợt thi final đã công bố trong cùng course; thi lại là exam khác. Các điểm khác cần thống nhất với TV1/TV4 vì mục 60.4 mô tả tính tự động chuyên cần/bài tập, trong khi người dùng yêu cầu nhập tay.
6. **Publish:** không hiển thị gradebook cho sinh viên trước khi published; thay đổi điểm/trọng số thu hồi công bố và ghi `audit_logs` trong cùng transaction. `source_exam_id` ghi nguồn của điểm cuối kỳ cao nhất.

## Điểm cần TV1/TV4 duyệt trước khi merge

- **TV1:** không sửa `users/auth_sessions/login_attempts`; xác nhận `course_access` truy vấn course_teachers/enrollments; đăng ký import model trong Alembic; quy tắc CSRF, idempotency 24 giờ.
- **TV4:** xác nhận fields của `judge_jobs`, verdict, lease 60s/heartbeat 15s/attempt tối đa 2, test case trọng số, `is_correct` vs partial score; thống nhất bỏ `submission_test_results` theo yêu cầu người dùng và cập nhật API 1.1.
- **Cả nhóm:** API 1.1 hiện giới hạn một exam/component/course và cho phép override điểm thủ công; yêu cầu mới cho phép nhiều đợt thi final và final auto MAX, do đó **phải cập nhật tài liệu hợp đồng API** trước tích hợp. Bản D01 không tự sửa file chung thuộc nhóm.
- Các constraint cross-table (problem thuộc đúng exam, student enrolled, deadline, role, publish, trọng số tổng 100, score 0–10, idempotency request hash) cần enforce trong service/transaction và kiểm thử, không thể được bảo đảm bằng FK đơn giản.

## Kiểm chứng

Kiểm thử tối thiểu: Alembic upgrade từ `0001_auth` đến `0002_database_base`, downgrade về `0001_auth`; `PRAGMA foreign_key_check`; insert duplicate enrollment/session/attempt bị từ chối; bảo toàn bảng auth; kiểm tra thiếu FK; pytest TV1 không hồi quy. Chưa có xác nhận chạy trên môi trường Python 3.12/SQLAlchemy 2.1.6 của nhóm cho đến khi chạy lệnh thực tế.
