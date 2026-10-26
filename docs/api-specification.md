# LAN-LMS API 1.2

Đây là hợp đồng của bản hoàn thiện, thay các hợp đồng dự kiến 1.1. Base `/api`; thời gian có múi giờ, response UTC ISO 8601. Phân trang `page>=1`, `page_size=1..100`: `{items,page,page_size,total}`. JSON dùng snake_case. T = teacher quản lý course; S = student enrollment active; O = chủ tài nguyên.

## Phiên và lỗi

Cookie HttpOnly `lan_lms_session`, SameSite=Lax, 8 giờ, Secure theo cấu hình HTTPS. Login kiểm tra Origin. Mọi POST/PATCH/PUT/DELETE có session cần Origin và `X-CSRF-Token`. Password change thu hồi mọi phiên; logout thu hồi phiên hiện tại và các WS tương ứng. Password gate chặn nghiệp vụ khi must_change_password.

```json
{"detail":"Thông báo","code":"ERROR_CODE","request_id":"uuid","errors":[]}
```

400 dữ liệu nghiệp vụ sai; 401 không có session; 403 thiếu quyền/Origin/CSRF/password gate; 404 không có; 409 dữ liệu trùng/sai trạng thái/hết giờ; 413 quá lớn; 422 validation; 429 rate/queue limit; 503 DB/queue tạm không sẵn sàng; 500 lỗi nội bộ. Không trả stack trace/secret/test ẩn.

Idempotency-Key dài 1–128 ký tự, scope user/method/path, giữ 24 giờ cho confirm CSV/file/code. Cùng body replay cùng resource/mã thành công, khác body 409. Replay vẫn kiểm tra quyền hiện tại; không kiểm tra lại deadline của một request đã được nhận hợp lệ.

## Auth và system

| Method | Path | Body hoặc response |
|---|---|---|
| GET | /health | DB SELECT 1 |
| GET | /ready | Kiểm tra cột auth và schema tích hợp; 503 nếu thiếu |
| GET | /public/connection | Không cần login: origin HTTPS, certificate_available và fingerprint CA công khai |
| GET | /public/lan-certificate | Chỉ tải CA công khai được cấu hình; không nhận đường dẫn từ request, không phục vụ private key |
| POST | /auth/login | `{username,password}` → `{user:{user_id,username,role,must_change_password}}` |
| GET | /auth/me | User |
| GET | /auth/csrf | `{csrf_token}` |
| POST | /auth/logout | 204 |
| POST | /auth/change-password | `{current_password,new_password}` → 204 |
| GET | /dashboard | T/S: full_name, stats, courses, events, exams, assignments, server_time |

Không có public register. Password mới 8–128 ký tự và khác cũ. Đăng nhập sai tối đa 10 lần/phút/IP. CSRF token ổn định trong cùng session để hỗ trợ nhiều tab.

## Courses CSV Materials

| Method | Path | Quyền và dữ liệu |
|---|---|---|
| GET | /public/courses | Khách: danh mục active, chỉ id,course_code,name,description,semester,academic_year; không có dữ liệu học tập/cá nhân |
| GET | /courses/{id}/judge-status | T/S của course: ready, workers có heartbeat dưới 30 giây, pending_jobs trong course, server_time; không công khai đường dẫn/secret |
| GET/POST | /courses | T/S list; Teacher create `{course_code,name,description,semester,academic_year,start_date,end_date}` |
| GET/PATCH | /courses/{id} | T/S detail; T patch các trường thay đổi |
| GET | /courses/{id}/students | T list `{student_id,full_name,class_name,email}` |
| POST | /courses/{id}/students/import-preview | T multipart file → Preview |
| POST | /courses/{id}/students/import-confirm | T `{preview_id}` + key → ImportResult |
| GET/POST | /courses/{id}/materials | T/S list; T multipart title,file |
| GET | /materials/{id}/download | T/S attachment |

Course JSON dùng `name` thay DB `course_name`. student_id ở API LMS là mã sinh viên; ID FK trong DB là profile id, không nhầm user_id. Ngày course YYYY-MM-DD, end>=start.

Preview có preview_id,expires_at,total_rows,valid_rows,new_accounts,existing_accounts,can_confirm,errors,conflicts. Hết hạn 15 phút; errors/conflicts ngăn confirm toàn bộ. Confirm trả created_accounts,existing_accounts,new_enrollments,existing_enrollments,failed_rows=0. CSV 2 MiB/2000 dòng, UTF-8/BOM, DOB DDMMYYYY; không reset password cũ.

Material có id,course_id,title,original_filename,size_bytes,uploaded_at. File 20 MiB; allowlist .pdf/.docx/.pptx/.txt/.zip, lưu UUID private. Không có URL public hay đường dẫn đĩa trả browser.

## Calendar và attendance

| Method | Path | Quyền và dữ liệu |
|---|---|---|
| GET/POST | /courses/{id}/events | T/S list; T EventInput |
| PUT/DELETE | /events/{id} | T full EventInput / 204 |
| GET/POST | /courses/{id}/attendance-sessions | T/S list; T `{title,duration_seconds,event_id?}`; event_id phải là lịch lesson của course, dùng tên lịch làm tên phiên |
| GET/PATCH | /attendance-sessions/{id} | T/S detail; T `{status:"closed"}` |
| POST | /attendance-sessions/{id}/check-in | S `{token}` → 201 mới / 200 record cũ |
| GET/PATCH | /attendance-sessions/{id}/records | T list / `{student_id,status,reason}` |
| GET | /attendance-sessions/{id}/roster | T: toàn bộ enrollment active; chưa có record thì id/checked_in_at=null, status=unmarked |

EventInput: title,description,event_type (`lesson|exam|deadline|announcement`), starts_at,ends_at có timezone. Attendance create mặc định 300 giây, 60..3600; response thêm token,check_in_path,qr_svg **chỉ khi tạo**. Không khôi phục token nguyên văn từ DB hash qua GET; mất mã thì tạo phiên mới. List S thêm my_status, không lộ mã. Record status present/absent/late; unmarked chỉ là trạng thái hiển thị của roster, không lưu thành record. Đóng/hết hạn không nhận record mới; token sai 403, thiếu membership 403. Correction yêu cầu reason >=3 ký tự và lưu audit. Quét lại trả record đã có, không ghi đè chỉnh tay. Late hiện tính như present khi tính chuyên cần.

## Bài tập file

| Method | Path | Body |
|---|---|---|
| GET/POST | /courses/{id}/assignments | T/S list; T `{title,description,due_at,allow_resubmit}` |
| GET/PATCH | /assignments/{id} | T/S detail; T partial patch |
| POST | /assignments/{id}/submissions | S multipart file + key → 201 |
| GET | /assignments/{id}/submissions | T cả lớp; S chỉ của mình |
| GET | /assignment-submissions/{id}/download | T/O attachment |
| PATCH | /assignment-submissions/{id}/grade | T `{score,feedback}`, score 0..10 |

File 20 MiB, .pdf/.docx/.txt/.zip/.c/.cpp/.java; không giải nén hay thực thi. Deadline do server kiểm tra. Lịch sử giữ nguyên; bản cuối hợp lệ tính homework. Score/feedback S chỉ thấy khi course công bố.

## Thi lập trình và test

| Method | Path | Quyền và dữ liệu |
|---|---|---|
| GET/POST | /courses/{id}/coding-exams | T/S list (S không thấy draft); T ExamInput |
| GET/PATCH | /coding-exams/{id} | T/S detail; T partial metadata/status |
| GET/POST | /coding-exams/{id}/problems | T list/create; S list từ lúc bắt đầu |
| PATCH/DELETE | /problems/{id} | T partial config / xóa bài và test trước thi |
| GET/POST | /problems/{id}/test-cases | T list metadata / multipart input_file,expected_output_file,points,is_hidden,ordinal |
| DELETE | /test-cases/{id} | T, trước thi, 204 |
| POST | /coding-exams/{id}/sessions/start | S → phiên mới hoặc phiên cũ dùng chung nhiều tab |
| GET | /coding-exams/{id}/my-session | S → ExamSession hoặc null |
| GET | /coding-exams/{id}/sessions | T list monitor |

Tạo trùng thành phần giữa kỳ/cuối kỳ trong cùng khóa trả 409 `EXAM_COMPONENT_EXISTS`, thông báo nêu đề đã tồn tại và hướng dẫn mở để quản lý. Quy tắc áp dụng cả draft/đề đã kết thúc. Form giảng viên chỉ hiện loại chưa có; khi đủ hai đề thì không hiện form tạo thêm. Việc kiểm tra trùng nằm trong khóa ghi DB để hai request đồng thời không rơi vào lỗi SQL chung.
| GET | /exam-sessions/{id} | T/O snapshot |
| POST | /exam-sessions/{id}/finish | O, lặp an toàn |

ExamInput: title,starts_at,ends_at,grade_component (`midterm|final`),score_ladder (mặc định [0,5,7,8,9,10]). Tối đa một mỗi loại/course. Ladder từ 0 đến 10, không giảm, dài N+1 với N=1..20. Số bài phải đúng N khi lên lịch. Response có problem_count và server_time.

Draft không xuất hiện cho S. PATCH status `scheduled` kiểm tra đủ đề/test trước khi mở; trạng thái hiển thị `upcoming|open|ended` theo giờ server; `closed` là teacher đóng sớm. Metadata/test bị khóa khi tới giờ hoặc có phiên. PATCH không thay grade_component.

ProblemInput: title,statement,languages subset c/cpp/java,io_mode stdio/file,input_filename,output_filename,time_limit_ms 100..10000,memory_limit_mib 64..1024,max_score>0,comparator exact/normalized. File mode cần basename khác nhau. Statement chứa ví dụ công khai. Test tối đa 100/problem, mỗi input/output 1 MiB; tổng points=max_score. Max_score là tổng trọng số test nội bộ, không phải điểm thang 10 của kỳ thi.

Session có id,exam_id,student_id,full_name,started_at,ends_at,submitted_at,status,last_seen_at,connection_status,accepted_count,problem_count,total_score,pending_count,server_time. Active/finished/expired độc lập connected/disconnected. Không trả IP/source của sinh viên khác.

## Submissions

| Method | Path | Dữ liệu |
|---|---|---|
| POST | /problems/{id}/submissions | S `{exam_session_id,language,source_code}` + key → 202 |
| GET | /problems/{id}/submissions | T list cả lớp; S list riêng |
| GET | /submissions/{id} | T/O, có source_code |

Source <=256 KiB UTF-8, không NUL. API kiểm tra membership, phiên, giờ, ngôn ngữ; ghi submission/job/idempotency cùng transaction. Tối đa 10 bài chưa xong/student, 200 job pending/running toàn hệ thống; vượt trả 429/503 để retry, không tạo bài nửa chừng.

Response: id,problem_id,exam_session_id,student_id,language,received_at,status,verdict_code,score,max_score,compile_message,reason_code,version. List không chứa source. Compiler message tối đa 16 KiB, không lộ đường dẫn host. Trạng thái Pending/Compiling/Running, Accepted/AC, Wrong Answer/WA, Compile Error/CE, Time Limit Exceeded/TLE, Memory Limit Exceeded/MLE, Runtime Error/RTE, System Error/SE. Pending và SE score=null; AC score=max_score, các verdict lỗi bài làm score=0. Không lưu/hiển thị điểm test lẻ. Điểm thi = ladder[số problem khác nhau có AC hợp lệ].

## Bảng điểm

| Method | Path | Quyền và dữ liệu |
|---|---|---|
| GET/PATCH | /courses/{id}/grade-components | T weights / đủ attendance,homework,midterm,final tổng 100 |
| GET | /courses/{id}/gradebook | T cả lớp; S chỉ dòng mình khi công bố |
| PATCH | /courses/{id}/grades | T `{items:[{student_id,component,score,reason}]}`, all-or-nothing |
| POST | /courses/{id}/gradebook/publish | T `{published:true|false}` |
| GET | /courses/{id}/gradebook/export-csv | T UTF-8 BOM attachment |

GradeRow: student_id,full_name,class_name,attendance_score,homework_score,midterm_score,final_score,total_score. Weight=0 bỏ qua, thiếu thành phần weight>0 thì total=null. Override score 0..10; null xóa override về tự động; reason bắt buộc. Publish yêu cầu đủ điểm, không còn phiên điểm danh đang mở/bài tập chưa đến hạn ở thành phần có trọng số dương. Thay nguồn/weight/override thu hồi công bố và có audit cho thao tác nhạy cảm. CSV escape văn bản có thể bị hiểu là công thức; ô null để trống.

## WebSocket

`/ws` dùng cookie và exact Origin, không query credential hoặc subscribe course tùy ý. Message <=4 KiB, queue tối đa 100/connection. Heartbeat 15 giây, ACK trong 10 giây; quá hạn đóng. Logout/password change đóng 1008. Reconnect lấy lại REST; event không cam kết replay.

```json
{"type":"heartbeat","id":"opaque"}
{"type":"heartbeat.ack","id":"opaque"}
{"event_id":"opaque","type":"submission.updated","occurred_at":"2026-10-25T08:00:00Z","data":{"submission_id":1,"status":"Accepted","version":4}}
```

Sự kiện submission.updated gửi owner và T hiện có quyền; exam.updated gửi thành viên khóa; session.updated gửi owner/T. Outbox DB nối worker và API, dọn sau 24 giờ. Source/test/token không nằm trong event.

## Kiểm chứng

Kiểm thử tại tests/, lệnh ở README. [Kết quả](../experiments/RESULTS.md) phân biệt local Windows, CI Linux và nghiệm thu LAN vật lý. Không dùng endpoint/job giả trả AC khi Docker không sẵn sàng.
