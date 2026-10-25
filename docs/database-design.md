# Database LAN-LMS

30 bảng đăng ký qua server/app/models và core/database. Triển khai bằng Alembic; không sửa DB thủ công hay dùng create_all trên dữ liệu thật.

| Nhóm | Bảng |
|---|---|
| Auth | users, auth_sessions, login_attempts |
| Hồ sơ/khóa | classes, teachers, students, courses, course_classes, course_teachers, course_enrollments |
| Học liệu/CSV/lịch | course_materials, csv_import_previews, calendar_events |
| Điểm danh/bài tập | attendance_sessions, attendance_records, assignments, assignment_submissions |
| Thi/judge | coding_exams, problems, test_cases, exam_registrations, exam_sessions, code_submissions, judge_jobs, judge_results |
| Điểm/hạ tầng | grade_components, grades, audit_logs, idempotency_keys, realtime_events |

## Ràng buộc

Username/student_code/teacher_code duy nhất; enrollment(course,student), attendance(session,student), registration(exam,student) và attempt(session,problem,attempt_no) duy nhất. Một profile/user; teacher/student FK khác user id. Partial unique index bảo vệ một final và một midterm/course. Một job/result/submission. Idempotency unique(user,method,path,key), không unique riêng user_id. Không có submission_test_results.

Date course YYYY-MM-DD; timestamp khác là UTC epoch trong DB, API xuất ISO timezone. JSON cấu hình languages và score_ladder được validation trước ghi. Foreign keys RESTRICT ngăn xóa dây chuyền dữ liệu học tập ngoài ý muốn. Status/điểm/quy tắc nghiệp vụ kiểm tra tại service; không tự nhận mọi cột Text đều được DB kiểm tra enum.

## Migration

0001 auth; 0002 schema D01 đóng băng tại database/migrations/schema_0002.py; 0003 LMS fields/private file/idempotency/final unique; 0004 lịch/QR/score ladder/midterm unique/worker metrics/realtime_events. Test nâng DB có dữ liệu từ 0002 lên head và dựng DB mới. Nếu dữ liệu cũ vi phạm unique mới, migration dừng để xử lý có chủ đích, không tự xóa dữ liệu. Downgrade có thể từ chối nếu schema cũ không biểu diễn được dữ liệu mới.

```powershell
.\.venv\Scripts\python.exe -m alembic -c server/alembic.ini upgrade head
```

## Điểm và lưu trữ

Grades giữ manual overrides có reason/teacher; điểm tự động tính từ attendance, bản file cuối và tập các problem đã AC. Không lưu per-test result hay password rõ. JudgeResults lưu tổng bài, compiler message và reason_code. Source/test/material path tương đối private storage; không trả browser. Outbox chỉ chứa ID/trạng thái/version và người nhận suy từ DB.

## Backup

Không copy riêng .db đang dùng WAL rồi coi đủ. scripts.backup_database giữ writer reservation ngắn theo toàn snapshot, dùng SQLite backup API trên reader riêng rồi copy storage/manifest. Restore kiểm tra SHA-256/integrity/FK vào đích mới, thu hồi session và reset job đang chạy. Nên dừng API/worker để tránh request bị busy trong lúc copy file lớn. Không đặt WAL DB trên NAS/network share.
