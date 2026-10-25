# Tích hợp TV1/TV4 ngày 24–25/10/2026

## Quyết định trực tiếp của người dùng ngày 25/10

1. Chỉ lưu kết quả tổng bài: verdict, score/max_score, thông báo biên dịch và lý do lỗi khi cần. Test case vẫn là dữ liệu đề; so sánh và cộng điểm từng test chỉ thực hiện trong bộ nhớ. Không tạo submission_test_results, không trả input/expected output test ẩn.
2. Một kỳ thi cuối kỳ cho mỗi khóa học. Policy single_final_exam thay đề xuất nhiều đợt/MAX trong bản D01. Unique partial index trên coding_exams(course_id) khi grade_component=final bảo vệ ở DB.

Các quyết định này là bản tạm theo chỉ đạo, cần thống nhất lại với nhóm sau; hiện code, schema và tài liệu dùng cùng lựa chọn, không đồng thời hỗ trợ hai chính sách trái nhau.

## Đối chiếu việc

| Người/ngày | Mã | Đã thực hiện |
|---|---|---|
| TV1 24/10 | A01–A05 | Kế thừa auth/session/DB; bổ sung schema, phân trang và test ở nhánh trước; kiểm thử hồi quy trong bản này |
| TV1 24/10 | A08 | Proxy HTTP/WS thật, sửa runtime/temp Nginx và giới hạn multipart; đăng nhập browser qua Nginx thành công |
| TV1 24/10 | Q01 | Ghép frontend, database migration/seed và compiler Docker; browser login/CSV thật và CI Docker đạt |
| TV1 25/10 | A06 | Quyền teacher theo course_teachers, student theo enrollment active; gắn policy thật, chặn resource ngoài khóa học |
| TV1 25/10 | A07 | Session/CSRF/Origin/rate limit dùng lại và kiểm thử; bảo vệ trang frontend, đổi mật khẩu và đăng xuất |
| TV1 25/10 | A09 | Idempotency scope user/method/path/key, 24h; atomic DB lock, trả lại kết quả cùng payload, 409 khác payload; test đồng thời |
| TV1 25/10 | Q02 | Hoàn thiện phụ thuộc course/CSV/material/assignment/UI để có luồng thật; test API và browser; judge chạy trên CI Docker |
| TV4 24/10 | J01 | Thống nhất fields Problems/CodeSubmissions/JudgeJobs/JudgeResults, chỉ kết quả tổng và một final/course |
| TV4 24/10 | J02 | Dockerfile gcc/g++/JDK17, CLI chấm mẫu; test C/C++/Java thật trong GitHub Actions Linux |
| TV4 25/10 | J03 | Assignment CRUD, lịch sử nộp/download, deadline/resubmit, chấm tay/feedback, quyền, limits và idempotency |
| TV4 25/10 | J04 | Mạng tắt, read-only root, user nobody, cap-drop, no-new-privileges, CPU/RAM/pids/time/file/output giới hạn; Docker container riêng từng test |
| TV4 25/10 | J05 | Compile một lần, C17/C++17/Java Main, stdio/file, exact/normalized, điểm từng phần và verdict tổng; AC/WA/CE/TLE/MLE/RE tests thật |

Phụ thuộc đã làm luôn: D04/D05/D06/D07/D08, F04/F05/F06/F07 và màn bài tập cơ bản. Test DB D03 của TV3 đã được giữ lại trong tích hợp. Không nhận thay phần xác nhận yêu cầu nghiệp vụ của người khác; các mục tương lai vẫn phải theo lịch riêng.

## Kiểm chứng

- Backend mới: kiểm thử quyền khóa học, CSV hợp lệ/lỗi/trùng/rollback, giữ mật khẩu cũ, retry cùng/khác key, nộp file đồng thời, quá hạn, cấm resubmit, file quá lớn, private download, ẩn điểm chưa công bố.
- Migration: dựng DB mới và nâng cấp DB có dữ liệu từ 0002 lên 0003; không đổi password, không mất dữ liệu, FK check sạch. Bỏ unique user_id sai trong idempotency, cho nhiều key độc lập cùng user. Đóng băng metadata của 0002 để lịch sử không thay đổi theo model mới.
- Frontend: typecheck/lint/build thành công. Chốt TypeScript 6.0.3 phù hợp typescript-eslint; sửa dependency hook login, xử lý multipart/CSRF, giữ idempotency key khi retry; key sinh được cả trên HTTP LAN không có crypto.randomUUID.
- Browser thật qua Nginx: teacher login → tạo course → upload CSV preview → confirm → logout → student mới login → trang bắt buộc đổi mật khẩu. Database và file thử nằm .runtime/ bị ignore.
- CI lần đầu [40186218326](https://github.com/VQuyy-1458/LAN-LMS/actions/runs/40186218326) đạt toàn bộ: build Docker image, pytest có RUN_DOCKER_TESTS=1, frontend typecheck/lint/build. Bao gồm 7 ca Docker (có tham số hóa): ba ngôn ngữ stdio, ba ngôn ngữ file I/O, và nhóm verdict/limits.
- Máy Windows này có Docker CLI nhưng Docker Desktop bị kẹt socket dockerInference, nên không tuyên bố đã chạy sandbox thành công trên Windows. CI Linux là bằng chứng compiler/sandbox; Windows cần chạy lại cùng bộ test sau khi sửa Docker Desktop.
- Proxy/browser thử trên loopback một máy. Chưa có bằng chứng hai máy vật lý trên LAN; kiểm thử hai máy chính thức vẫn thuộc bước triển khai Q05. Không tự mở firewall hay làm yếu bảo mật máy.

## Chạy và tích hợp

Từ gốc repository, Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m pip install -r server/requirements.lock
.\.venv\Scripts\python.exe -m alembic -c server/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m server.app.seed
.\scripts\start_server.ps1
```

Seed teacher hiện tạo cả profile. Teacher cũ chưa có profile có thể chạy database.seed.seed_demo với username tương ứng để tạo profile/dữ liệu giả; không chạy seed demo trên dữ liệu thật. Không ghi mật khẩu vào tài liệu hay lệnh.

Client: npm ci; npm run dev. Development có thể copy client/.env.example thành client/.env.local để dùng API_UPSTREAM. LAN dùng Nginx /api và /ws cùng origin, xem scripts/nginx.conf và scripts/start_proxy.ps1. ALLOWED_ORIGINS phải là origin web thực tế; giữ backend ở loopback. Không đồng thời tạo hai proxy mâu thuẫn.

Bộ chấm mẫu:

```powershell
docker build -t lan-lms-judge:day25 judge
$env:RUN_DOCKER_TESTS='1'
.\.venv\Scripts\python.exe -m pytest tests/integration/test_judge_docker.py -q
.\.venv\Scripts\python.exe -m judge.cli --language cpp --source path/to/Main.cpp --manifest path/to/problem.json
```

Manifest ví dụ (đường dẫn test tương đối thư mục manifest, không cho thoát ra ngoài):

```json
{"time_limit_ms":2000,"memory_limit_mib":256,"io_mode":"stdio","comparator":"exact","tests":[{"input":"01.in","expected":"01.out","points":10}]}
```

Expected output chỉ đọc ở orchestrator host, không mount vào container chương trình sinh viên. Java dùng public class Main, không package; file I/O thêm input_filename/output_filename là basename an toàn.

## Giới hạn phạm vi

Đây là hoàn thiện công việc ngày 24–25 và phụ thuộc cần để ghép. Chưa phải hoàn thiện toàn bộ đồ án: API tổ chức kỳ thi/phiên/code submissions, worker queue tự động, realtime kết quả chấm, QR và gradebook hoàn chỉnh thuộc ngày tiếp theo. judge.cli là runner thật cho bài mẫu; judge/worker.py và job_queue.py chưa được tuyên bố triển khai. Không biến kết quả sandbox CI thành kết quả thi của sinh viên giả.

DB upgrade sẽ dừng nếu dữ liệu hiện có vi phạm unique student/user hoặc có nhiều final/course, để nhóm giải quyết có chủ đích thay vì xóa dữ liệu. Downgrade 0003 từ chối nếu một user đã có nhiều idempotency key vì 0002 không biểu diễn được; không tự bỏ bớt key.

SQLAlchemy chốt 2.0.46 thay 2.1.6 để chạy được trên Windows App Control với Python fallback chính thức. Không tắt bảo vệ hệ điều hành. Lockfile đã được cập nhật và CI Linux đã thử cài sạch.
