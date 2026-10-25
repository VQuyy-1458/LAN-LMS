# LAN-LMS — Hợp đồng API 1.1

Cập nhật 24/10/2026. Đây là thiết kế để triển khai, chưa phải danh sách API đã chạy. Nghiệp vụ đầy đủ tại [PROJECT_PLAN.md](PROJECT_PLAN.md), nhất là mục 60. Thay đổi hợp đồng phải được thống nhất trước tích hợp.

## 1. Quy ước, phiên và quyền

- Base path `/api`; browser gọi cùng origin qua proxy. FastAPI nội bộ `http://127.0.0.1:8000`; trình duyệt máy khác không dùng localhost để gọi máy chủ.
- JSON snake_case; upload multipart/form-data; download binary; export text/csv UTF-8 BOM. ID là số nguyên dương, trừ token, preview_id, request_id và idempotency key là chuỗi opaque.
- UTC ISO 8601 có `Z` trong response; input thời gian phải có timezone. Hiển thị giờ Việt Nam ở frontend.
- Cookie session HttpOnly `lan_lms_session`, SameSite=Lax, Path=/, 8 giờ; Secure khi HTTPS. DB lưu hash token. Origin allowlist và CSRF áp dụng cho POST/PATCH/DELETE có session; header `X-CSRF-Token` lấy từ GET /auth/csrf. Login kiểm tra Origin; chưa có session nên không dùng CSRF token.
- Login dùng username cho cả teacher/student. Seed tạo teacher tương tác; không có public registration. Password hash Argon2id; chính sách đổi 8–128 ký tự, khác mật khẩu cũ. Rate limit login: tối đa 10 lần thất bại/phút/IP, vượt trả 429.
- Khi must_change_password=true, chỉ me/csrf/change-password/logout được dùng. Đổi mật khẩu thu hồi tất cả session, trả 204; client đăng nhập lại.
- T = teacher sở hữu khóa học; S = student đã enrollment; O = chủ bài nộp. Teacher không tự có quyền mọi khóa học. Visitor chỉ login. Student chỉ xem điểm của mình và dữ liệu đã công bố.
- List: `{"items":[],"page":1,"page_size":20,"total":0}`, page >=1, page_size 1–100. Thứ tự mặc định id tăng; submissions sắp received_at giảm.
- Create trả 201 và resource; GET/PATCH 200; thao tác không có body trả 204. Khi 202 phải trả resource theo mô tả riêng. ID/owner/timestamp do server tạo, không cho client ghi tùy ý.

## 2. Lỗi và gửi lại

Lỗi thống nhất, kể cả validation 422:

```json
{"detail":"Thông báo đọc được","code":"INVALID_CSV_ROW","request_id":"opaque-id","errors":[{"field":"date_of_birth","row":3,"message":"Ngày không hợp lệ"}]}
```

`errors` có thể rỗng. HTTP: 400 dữ liệu nghiệp vụ sai, 401 chưa đăng nhập, 403 thiếu quyền/buộc đổi mật khẩu, 404 không tìm thấy, 409 xung đột, 413 quá lớn, 422 schema sai, 429 giới hạn tần suất, 503 DB bận/worker tạm không sẵn sàng, 500 lỗi bất ngờ. Không trả stack trace, đường dẫn nội bộ, password hash hay test ẩn.

`Idempotency-Key` bắt buộc khi confirm CSV, nộp file và gửi code; tối đa 128 ký tự. Scope gồm user, method, path; lưu ít nhất 24 giờ. Cùng key/body trả cùng resource và mã thành công ban đầu; khác body trả 409 IDEMPOTENCY_CONFLICT. Request đang xử lý trả 409 REQUEST_IN_PROGRESS, client đợi rồi truy vấn/gửi lại cùng key. Hash multipart dựa trên trường metadata và bytes file, không dựa boundary. Tạo key và resource atomically; không giữ DB transaction lúc đọc file hay chấm code.

## 3. Xác thực

| Method/path | Request | Response |
|---|---|---|
| POST /auth/login | `{username,password}` | 200 `{user:{user_id,username,role,must_change_password}}` và Set-Cookie |
| GET /auth/me | — | `{user_id,username,role,must_change_password}` |
| GET /auth/csrf | — | `{csrf_token}` |
| POST /auth/logout | — | 204, thu hồi session và xóa cookie |
| POST /auth/change-password | `{current_password,new_password}` | 204, thu hồi session |

## 4. Khóa học, CSV và tài liệu

| Method/path | Quyền | Body hoặc kết quả |
|---|---|---|
| GET /courses | T/S | List Course theo quyền |
| POST /courses | Teacher | `{course_code,name,description,start_date,end_date}` → Course |
| GET /courses/{id} | T/S | Course |
| PATCH /courses/{id} | T | Các trường thay đổi trong body tạo; không đổi owner |
| GET /courses/{id}/students | T | List Student |
| POST /courses/{id}/students/import-preview | T | multipart file → 200 Preview; chưa ghi users/enrollment |
| POST /courses/{id}/students/import-confirm | T | `{preview_id}` + key → 200 ImportResult |
| GET /courses/{id}/materials | T/S | List Material |
| POST /courses/{id}/materials | T | multipart title,file → Material |
| GET /materials/{id}/download | T/S | binary với Content-Disposition attachment |

Course: `{id,course_code,name,description,start_date,end_date,teacher_id}`; date là YYYY-MM-DD, end_date >= start_date. Student: `{student_id,full_name,class_name,email}`; không trả DOB trong danh sách mặc định. Material: `{id,course_id,title,original_filename,size_bytes,uploaded_at}`.

CSV bắt buộc student_id,full_name,date_of_birth,class_name; email tùy chọn. DOB DDMMYYYY, UTF-8/BOM. Preview: `{preview_id,expires_at,total_rows,valid_rows,existing_accounts,new_accounts,can_confirm,errors:[{row,field,code,message}],conflicts:[]}`. Bất kỳ lỗi/trùng mã/xung đột hồ sơ nào làm can_confirm=false. Preview lưu phía server, scope course/teacher, hết hạn 15 phút. Confirm kiểm tra lại và all-or-nothing; hết hạn hoặc DB đã thay đổi trả 409 PREVIEW_STALE. ImportResult: `{preview_id,total_rows,created_accounts,existing_accounts,new_enrollments,existing_enrollments,failed_rows:0}`. Không reset mật khẩu cũ.

CSV tối đa 2 MiB/2.000 dòng; materials 20 MiB, allowlist `.pdf,.docx,.pptx,.txt,.zip`. UUID tên lưu nội bộ, original_filename chỉ hiển thị; không giải nén ZIP ở bản đầu. Không trả đường dẫn đĩa cho browser.

## 5. Điểm danh

| Method/path | Quyền | Body/kết quả |
|---|---|---|
| POST /courses/{id}/attendance-sessions | T | `{title,duration_seconds}` → AttendanceSession, mặc định 300, phạm vi 60–3600 |
| GET /attendance-sessions/{id} | T/S | AttendanceSession; chỉ T nhận token/check_in_url |
| PATCH /attendance-sessions/{id} | T | `{status:"closed"}` → AttendanceSession |
| POST /attendance-sessions/{id}/check-in | S | `{token}` → 201 AttendanceRecord; gửi lại trả 200 record cũ |
| GET /attendance-sessions/{id}/records | T | List AttendanceRecord |

AttendanceSession: `{id,course_id,title,status,expires_at,created_at}`. AttendanceRecord: `{id,session_id,student_id,checked_in_at}`. Unique(session,student). Token hết hạn/phiên đóng trả 409 ATTENDANCE_CLOSED; sai token trả 403. Mã nhập và QR đại diện cùng token ngẫu nhiên; không chứa password.

## 6. Bài tập file

| Method/path | Quyền | Body/kết quả |
|---|---|---|
| GET /courses/{id}/assignments | T/S | List Assignment |
| POST /courses/{id}/assignments | T | `{title,description,due_at,allow_resubmit}` → Assignment |
| GET /assignments/{id} | T/S | Assignment |
| PATCH /assignments/{id} | T | title,description,due_at,allow_resubmit |
| POST /assignments/{id}/submissions | S | multipart file + key → FileSubmission |
| GET /assignments/{id}/submissions | T/S | T xem cả lớp, S chỉ của mình; list |
| GET /assignment-submissions/{id}/download | T/O | binary |
| PATCH /assignment-submissions/{id}/grade | T | `{score,feedback}` score 0–10 → FileSubmission |

Assignment: `{id,course_id,title,description,due_at,allow_resubmit}`. FileSubmission: `{id,assignment_id,student_id,original_filename,size_bytes,received_at,score,feedback}`; score/feedback nullable và chỉ trả cho S khi công bố điểm. File tối đa 20 MiB, allowlist `.pdf,.docx,.txt,.zip,.c,.cpp,.java`; không thực thi/giải nén. Lưu lịch sử; bản nhận cuối trước hạn là bản hiệu lực để chấm. Hết hạn trả 409 DEADLINE_PASSED; không cho nộp lại trả 409 RESUBMIT_DISABLED.

## 7. Kỳ thi, bài lập trình, test và phiên

| Method/path | Quyền | Body/kết quả |
|---|---|---|
| GET /courses/{id}/coding-exams | T/S | List Exam |
| POST /courses/{id}/coding-exams | T | `{title,starts_at,ends_at,grade_component}` → Exam |
| GET /coding-exams/{id} | T/S | Exam |
| PATCH /coding-exams/{id} | T | title,starts_at,ends_at trước khi bắt đầu |
| GET /coding-exams/{id}/problems | T/S | List Problem, S chỉ khi đang thi hoặc đã thi |
| POST /coding-exams/{id}/problems | T | ProblemInput → Problem |
| PATCH /problems/{id} | T | ProblemInput từng phần, chỉ trước khi thi |
| POST /problems/{id}/test-cases | T | multipart input_file,expected_output_file,points,is_hidden,ordinal → TestCaseMetadata |
| GET /problems/{id}/test-cases | T | List metadata; không có endpoint test ẩn cho S |
| DELETE /test-cases/{id} | T | 204; trước khi thi |
| POST /coding-exams/{id}/sessions/start | S | không body → 200 ExamSession (tái dùng nếu đã tạo) |
| POST /exam-sessions/{id}/finish | O | không body → ExamSession; lặp lại trả cùng phiên |
| GET /coding-exams/{id}/sessions | T | List ExamSession |
| GET /exam-sessions/{id} | T/O | ExamSession |

Exam: `{id,course_id,title,starts_at,ends_at,grade_component,status}`; status tính từ giờ server, grade_component là midterm/final, mỗi loại tối đa một exam/course bản đầu. Bài tập file quản lý riêng.

ProblemInput: `{title,statement,languages,io_mode,input_filename,output_filename,time_limit_ms,memory_limit_mib,max_score,comparator}`. languages subset `c,cpp,java`; io_mode `stdio|file`; file mode bắt buộc hai basename hợp lệ; comparator `exact|normalized`. Giới hạn: time_limit_ms 100–10000, memory_limit_mib 64–1024, max_score >0. Test input/output mỗi file <=1 MiB; tối đa 100 test/problem. Điểm test >=0; tổng bằng max_score trước khi thi. Problem thêm id,exam_id; S không nhận metadata test ẩn. Đề bài phải có sample input/output do T nhập trong statement.

Không sửa cấu hình/test sau khi thi bắt đầu; mở thi chỉ khi có bài, mỗi bài có test và tổng điểm hợp lệ. Tổng giới hạn tài nguyên phải phù hợp máy demo.

ExamSession: `{id,exam_id,student_id,started_at,ends_at,submitted_at,status,last_seen_at,connection_status}`. Status `active|finished|expired`; connection `connected|disconnected|unknown` độc lập trạng thái thi. Nhiều tab dùng chung một phiên; online khi còn ít nhất một connection sống. Chỉ T xem IP quan sát được nếu lưu; không trả cho sinh viên khác.

## 8. Code submission và kết quả

| Method/path | Quyền | Body/kết quả |
|---|---|---|
| POST /problems/{id}/submissions | S | `{exam_session_id,language,source_code}` + key → 202 Submission |
| GET /submissions/{id} | T/O | Submission |
| GET /problems/{id}/submissions | T/S | List Submission theo quyền |

Submission: `{id,problem_id,exam_session_id,student_id,language,received_at,status,score,max_score,compile_message,reason_code,version}`. Source tối đa 256 KiB UTF-8. Chỉ chính chủ/T có thể nhận source_code khi GET chi tiết; list không chứa source. Thông báo compiler cắt tối đa 16 KiB và loại đường dẫn nội bộ.

Trạng thái: Pending, Compiling, Running, Accepted, Wrong Answer, Compile Error, Time Limit Exceeded, Memory Limit Exceeded, Runtime Error, System Error. Score null trong khi chờ và System Error; CE =0. Verdict/điểm submission trả ngay cho chủ bài trong phiên; bảng điểm khóa học tuân theo công bố riêng. Không trả nội dung/output test ẩn. T có thể nhận per_test summary, S chỉ nhận tổng.

Server kiểm tra cửa sổ thi, membership và session active, sau đó lưu bài và job cùng transaction. Thời điểm nhận hợp lệ là thời điểm backend nhận đủ body và kiểm tra trước commit; không lấy timestamp của browser. GET sau reconnect là nguồn trạng thái chuẩn. Quy tắc tổng hợp verdict, score và retry worker tại PROJECT_PLAN mục 60.

## 9. Điểm và công bố

| Method/path | Quyền | Body/kết quả |
|---|---|---|
| GET /courses/{id}/gradebook | T/S | `{weights,published,items:[GradeRow]}`; S chỉ một dòng của mình khi published=true, nếu chưa công bố items=[] |
| GET /courses/{id}/grade-components | T | `{attendance:10,homework:20,midterm:30,final:40}` |
| PATCH /courses/{id}/grade-components | T | đủ bốn trọng số >=0, tổng 100 → weights; thu hồi công bố |
| PATCH /courses/{id}/grades | T | `{items:[{student_id,component,score,reason}]}`; score null hoặc 0–10 → 200 `{updated_count}`; all-or-nothing |
| POST /courses/{id}/gradebook/publish | T | `{published:true|false}` → `{published}` |
| GET /courses/{id}/gradebook/export-csv | T | attachment UTF-8 BOM |

GradeRow: `{student_id,full_name,class_name,attendance_score,homework_score,midterm_score,final_score,total_score}`. Các score nullable, total quy tắc mục 60.4. Điểm tính tự động là mặc định; cập nhật thủ công tạo override có reason bắt buộc, lưu audit và thu hồi công bố; nguồn tự động thay đổi sau đó cũng thu hồi công bố. Publish yêu cầu trọng số hợp lệ và các điểm cần thiết đã có. Không có điểm không tự biến thành 0.

CSV dùng đúng các cột GradeRow, null là ô trống; escape ô văn bản có thể được phần mềm bảng tính hiểu thành công thức. Mã giữ dưới dạng chuỗi; CSV không đảm bảo Excel tự giữ số 0 đầu khi mở trực tiếp, README phải hướng dẫn import cột mã dạng Text.

## 10. WebSocket

Đường dẫn `/ws`, cookie session và Origin được kiểm tra trước accept. Không dùng query string chứa session token. Không tự subscribe khóa học bằng ID do client gửi: server suy quyền từ DB.

```json
{"event_id":"opaque-id","type":"submission.updated","occurred_at":"2026-10-24T03:00:00Z","data":{"submission_id":1,"status":"Running","version":2}}
```

Sự kiện `submission.updated`: gửi chủ bài và T quản lý; `exam.updated`: exam_id,status,ends_at gửi thành viên được phép; `session.updated`: exam_session_id,status,connection_status gửi chủ phiên và T. Payload không có test ẩn, token hay source của người khác. event_id để bỏ trùng, version tăng theo entity để bỏ sự kiện cũ; không cam kết replay sự kiện.

Server gửi `heartbeat` mỗi 15 giây, client trả `heartbeat.ack` có id trong 10 giây. Quá 45 giây không ack thì đóng và cập nhật trạng thái; dữ liệu WS tối đa 4 KiB/message. Session hết hạn bị đóng 1008; shutdown 1001, lỗi nội bộ 1011. Client reconnect sau 1,2,4,8 giây rồi tối đa 15 giây, thêm jitter. Sau reconnect luôn GET trạng thái; trong lúc mất WS truy vấn submission chưa xong mỗi 3 giây. Dừng polling khi terminal hoặc rời trang. Client không được gửi lệnh ghi điểm/nhận job qua WS.

## 11. Thay đổi và kiểm chứng

Thành viên 1 sở hữu chuẩn chung và auth/WS; 3 sở hữu course/CSV/materials/attendance/gradebook; 4 sở hữu assignment/exam/submission/judge; 2 tích hợp frontend. Các module phải dùng response model và test quyền tương ứng. OpenAPI sinh từ code phải khớp tài liệu; hiện chưa có code nên chưa xác nhận endpoint, hiệu năng hay tính an toàn đã đạt.

## 12. Trạng thái triển khai thành viên 1

Đã có auth, health, WS, dependency phân quyền và migration nền tảng; 11 kiểm thử tự động đã qua ngày 24/10/2026. Các API course/CSV/materials/attendance/assignment/exam/submission/gradebook ở trên vẫn là hợp đồng cho các thành viên tích hợp, chưa có implementation. Hướng dẫn chạy và giới hạn tại [MEMBER_1_HANDOFF.md](MEMBER_1_HANDOFF.md).

## 13. Bổ sung nền tảng ngày 24/10/2026

- GET /api/health: 200 khi kết nối DB được; GET /api/ready: 200 khi đọc được các cột/bảng auth cần thiết, 503 DATABASE_UNAVAILABLE nếu chưa migration hoặc DB lỗi. Hai endpoint không cần đăng nhập và không trả secret.
- GET /api/auth/csrf trả token ổn định trong cùng phiên, không làm tab khác mất token. Đổi phiên tạo token mới; logout/đổi mật khẩu thu hồi phiên như trước.
- Đăng nhập lại thành công thu hồi cookie phiên cũ đang được thay thế. Không thu hồi các phiên trên thiết bị khác khi chỉ login; đổi mật khẩu vẫn thu hồi tất cả.
- ErrorResponse và auth response model được xuất trong OpenAPI. Lỗi validation không phản chiếu input mật khẩu. Header X-Request-ID khớp request_id trong lỗi.
- Common Pagination nhận page >=1, page_size 1–100; response items/page/page_size/total. utc_iso yêu cầu datetime có timezone và trả UTC với Z. Các module nghiệp vụ cần dùng các tiện ích này khi triển khai.
- SQLite URL tương đối tính từ gốc repository, không từ thư mục terminal; cấu hình origin/bool/đường dẫn được kiểm tra khi tạo app.

## 14. Hợp đồng tích hợp tạm ngày 25/10/2026 (ưu tiên khi khác mô tả cũ)

Theo người dùng: chỉ lưu/trả kết quả tổng bài, không lưu kết quả từng test; một final/course, không lấy MAX nhiều đợt final. Giữ test case cấu hình để chấm nhưng input/expected ẩn không trả sinh viên.

Course create có thêm semester (mặc định 1), academic_year (2026-2027); schema DB course_name được ánh xạ thành JSON name. PATCH course/assignment nhận trường thay đổi và kiểm tra lại trạng thái sau merge, không bắt frontend gửi lại toàn bộ.

Đã triển khai các endpoint course/list/detail/students, CSV preview/confirm, materials upload/download, assignments create/list/detail/patch/submit/history/download/grade. Idempotency bắt buộc cho CSV confirm và file submission; same key+body replay kết quả, khác body 409. Kiểm tra lại quyền trước khi replay; không coi key là giấy phép truy cập dữ liệu.

Giá trị student_id trong JSON LMS là mã sinh viên; DB foreign key student_id là ID profile Students, không được nhầm user_id. Teacher profile tương tự. Tiện ích access.py là nguồn kiểm tra course role/enrollment.

Upload file tối đa 20 MiB; proxy cho body 21 MiB để chứa multipart envelope, backend vẫn kiểm tra đúng 20 MiB bytes file. File không giải nén, không thực thi. Điểm bài tập chỉ hiển thị cho sinh viên khi khóa học đã công bố; chấm/nộp lại thu hồi công bố.

Runner CLI chấm mẫu không tạo API kỳ thi/queue trước hạn. Những endpoint thi/QR/gradebook trong phần trước vẫn là hợp đồng cần triển khai sau. Schema 0003 bổ sung language/io mode/filenames vào Problems và compile_message/reason_code vào JudgeResults cho TV4 tiếp tục.
