# LAN-LMS — Đặc tả triển khai thống nhất

Phiên bản 1.2, chốt theo yêu cầu trực tiếp ngày 25/10/2026. Tài liệu này thay các quyết định tạm khác về điểm thi. [Yêu cầu giảng viên](requirements/) và [API](api-specification.md) đi cùng bản mã nguồn. Các tài liệu MEMBER_1/INTEGRATION_24_25 là nhật ký mốc trước, không phải phạm vi cuối.

## Phần I Mục tiêu và công nghệ

Hệ thống Client–Server trong LAN phục vụ khóa học, sinh viên, học liệu, lịch/thông báo, QR, bài tập, thi lập trình và điểm. Browser dùng Next.js/TypeScript/Tailwind; API FastAPI; SQLite/SQLAlchemy/Alembic; storage riêng tư; judge worker độc lập và Docker Linux. HTTP REST và WebSocket thể hiện giao tiếp mạng; không bổ sung TCP service chỉ để tăng số giao thức.

## Phần II Kiến trúc

Nginx phục vụ một origin, chuyển web sang Next.js, `/api` và `/ws` sang FastAPI. Chỉ một API process; một hoặc hai worker riêng. SQLite, private files và worker cùng máy. Worker không gọi lệnh từ browser; nhận job đã được API xác thực. Sơ đồ và luồng mạng ở [architecture.md](architecture.md).

## Phần III Vai trò

Visitor truy cập giới thiệu/đăng nhập; không có nội dung khóa riêng tư. Teacher chỉ quản lý khóa có CourseTeachers tương ứng. Student cần enrollment active, chỉ xem dữ liệu cá nhân/bài nộp riêng. User.id khác ID profile Students/Teachers; mọi quyền lấy từ DB. Không có public registration; tạo teacher bằng seed tương tác.

## Phần IV CSV và tài khoản

CSV UTF-8/BOM, tối đa 2 MiB/2.000 dòng. Header: student_id,full_name,date_of_birth,class_name,email; email tùy chọn. DOB DDMMYYYY là chuỗi giữ số 0 đầu. Username mới = student_id; password ban đầu = DOB; hash Argon2id và must_change_password. Không reset password/hồ sơ cũ khi import lại.

Preview lưu server, ràng buộc teacher/course, hết hạn 15 phút. Có lỗi/trùng mã/xung đột thì từ chối toàn bộ. Confirm có Idempotency-Key và kiểm tra lại dưới transaction; accounts, profile, enrollment và kết quả retry commit cùng nhau. UI có tổng dòng, tài khoản mới/cũ, lỗi theo dòng, báo cáo lỗi và kết quả tạo/đăng ký.

## Phần V Trải nghiệm sinh viên

Dashboard hiển thị tên hồ sơ, khóa, lịch/hạn nộp/thi và số liệu thật. Khóa có tổng quan, tài liệu, lịch/thông báo, QR, bài tập, thi và điểm. UI nền trắng/xám nhẹ, điểm nhấn đỏ, chữ xanh đậm; tham khảo bố cục ảnh được cung cấp, không sao chép thương hiệu/chức năng không có trong đề tài.

## Phần VI Tài liệu và bài tập

Private file tối đa 20 MiB; allowlist theo loại nội dung, UUID tên lưu, metadata có tên gốc. Download kiểm tra quyền. Không giải nén ZIP hay thực thi file upload. Bài tập file có đề, deadline server và allow_resubmit; lưu mọi lần nộp hợp lệ. Bản cuối trước hạn là bản hiệu lực. Teacher chấm 0–10/feedback; sửa/nộp lại thu hồi công bố.

## Phần VII Lịch và thông báo

Sự kiện gồm title,description,type,starts_at,ends_at,course_id. Type lesson/exam/deadline/announcement. API kiểm tra timezone và kết thúc không trước bắt đầu. Teacher tạo/sửa/xóa, student chỉ đọc lịch thuộc khóa. Dashboard gộp lịch, lịch thi và deadline.

## Phần VIII Điểm danh

Teacher xem/tạo lịch học, chọn buổi học để tạo QR có duration 60–3600 giây, mặc định 300. Token ngẫu nhiên chỉ trả khi tạo, DB lưu SHA-256. QR SVG tạo trên server, không dùng dịch vụ ngoài. Student mở camera trong mục Điểm danh QR hoặc chụp/chọn ảnh để giải mã ngay tại trình duyệt và tự gửi điểm danh; vẫn có nhập mã tay. Camera trực tiếp cần HTTPS tin cậy hoặc localhost, còn LAN HTTP dùng ảnh/mã. Unique(session,student) và khóa ghi chặn trùng, retry trả record cũ, không ghi đè chỉnh tay của teacher. Mã sai trả 403; phiên hết hạn/đóng không nhận điểm danh mới. Teacher đóng phiên, xem lịch sử và danh sách cả lớp kể cả người chưa quét, đánh dấu có mặt/đến muộn/vắng (present/late/absent), lưu reason/audit. Late hiện tính như present khi tính chuyên cần. QR không chứng minh vị trí tuyệt đối.

Khách không cần tài khoản để xem trang chủ và danh mục khóa học active. Khi chọn khóa học mới yêu cầu đăng nhập; header cũng có nút đăng nhập riêng. Các API nội dung, lịch học, sinh viên và điểm danh giữ nguyên kiểm tra phiên và quyền khóa học; danh mục công khai chỉ chứa thông tin giới thiệu.

## Phần IX Kỳ thi

Mỗi khóa tối đa một midterm và một final, bảo vệ ở DB. Teacher đặt thời gian có timezone và bảng quy đổi; mặc định 5 bài, ladder [0,5,7,8,9,10]. Ladder dài N+1, bắt đầu 0, kết thúc 10, không giảm, số bài 1–20.

Đề tạo ở trạng thái draft. Trước khi lên lịch, phải có đúng N bài, mỗi bài có 1–100 test và tổng trọng số bằng max_score. Đề/test bị khóa khi tới giờ bắt đầu hoặc đã có phiên. Teacher có thể đóng thi sớm; backend kiểm tra giờ và trạng thái, không tin đồng hồ client.

## Phần X Bài và test

Ngôn ngữ C17/C++17/Java17; Java Main, không package. Stdio hoặc file I/O có hai basename khác nhau. Comparator exact hoặc normalized: chuẩn hóa CRLF, bỏ space/tab cuối dòng và newline cuối theo quy tắc runner, không xóa mọi khoảng trắng nội bộ. Time 100–10000 ms, RAM 64–1024 MiB. Input/output test mỗi file tối đa 1 MiB. Sinh viên không nhận test ẩn hoặc expected/actual output.

## Phần XI Phiên thi và nộp code

Student bắt đầu khi exam open; registration/session tự tạo nguyên tử. Nhiều tab dùng chung một session. Finish là thao tác lặp an toàn; đóng/hết giờ ngăn bài mới. Source tối đa 256 KiB UTF-8. Submission và job lưu chung transaction, có attempt_no và version; không ghi đè lịch sử. Cùng key/body replay resource kể cả khi phiên đã đóng sau lần nhận đầu.

Frontend giữ bản nháp theo session/bài trên trình duyệt; source lưu server sau khi gửi thành công. Thời gian client chỉ hiển thị, server quyết định deadline. Pending/Compiling/Running rồi AC/WA/CE/TLE/MLE/RTE/SE; chỉ AC tính bài đã giải. SE không được biến thành điểm 0 học tập hoặc kết quả thành công giả.

## Phần XII Queue worker và sandbox

SQLite queue dùng BEGIN IMMEDIATE cho transaction ngắn. Claim tạo attempt token, lease 60 giây, gia hạn mỗi 10 giây. Job hết lease được nhận lại, tối đa 3 attempt; retry hết giới hạn thành SE. Chỉ attempt hiện hành chưa hết lease ghi được trạng thái/kết quả. Không giữ transaction trong lúc compiler/chương trình chạy.

Compile một lần; mỗi test một container mới. Nonroot, network none, read-only root, cap-drop ALL, no-new-privileges, CPU/RAM/swap/pids/tmpfs/time/output/file limits; không mount database, secret hoặc expected output vào chương trình. Chỉ lưu aggregate verdict/score và compiler message đã giới hạn. Các test được dùng trong bộ nhớ, không có bảng per-test result.

## Phần XIII Realtime và phục hồi

Worker ghi outbox cùng kết quả. API đọc theo ID, lọc người nhận từ DB rồi phát WS. Heartbeat/ACK, session check, queue hữu hạn; client chậm bị đóng để phục hồi REST. Logout/đổi password thu hồi WS tương ứng. Event không cam kết replay; REST snapshot là nguồn chuẩn. Frontend reconnect backoff/jitter và polling mỗi 3 giây; teacher monitor mỗi 5 giây. Connection status riêng với trạng thái phiên; online nếu còn ít nhất một WS sống.

## Phần XIV Quy tắc điểm đã chốt

Mỗi bài chỉ cần ít nhất một AC hợp lệ trước lúc kết thúc phiên để được tính một lần. Lần sai sau AC không làm mất bài đó. Không lấy điểm test lẻ, không lấy lần nộp cuối để xóa kết quả AC. Điểm thi = ladder[số bài AC], thang 10. Với mặc định 5 bài: 0/1/2/3/4/5 AC tương ứng 0/5/7/8/9/10.

Chuyên cần = 10 × số phiên present / số phiên đã đóng. Homework = trung bình điểm bản nộp cuối của các bài đã hết hạn; không nộp sau hạn tính 0, có nộp nhưng chưa chấm thì null. Chưa có phiên/bài đã đóng thì null. Điểm thi tự động chỉ chốt sau khi kỳ thi kết thúc và không còn pending/SE ở các bài chưa có AC cần xử lý; pending/SE của bài đã AC không chặn điểm.

Trọng số mặc định 10/20/30/40; teacher cấu hình đủ 4 giá trị không âm, tổng 100. Thành phần weight=0 bỏ qua; thiếu điểm ở weight>0 thì tổng null. Tính bằng dữ liệu chưa làm tròn; làm tròn tổng hai chữ số. Override có reason/audit; score null xóa override để dùng lại tự động. Sửa nguồn/weight/override thu hồi công bố. Student chỉ xem dòng của mình khi published; không public leaderboard.

## Phần XV Dữ liệu và API

30 bảng gồm auth, LMS, exam/judge, grades/audit và realtime_events. Migration 0001–0004; không dùng create_all thay migration trong triển khai thật. Các test/benchmark tạo DB giả lập biệt lập. API, fields và lỗi ở [api-specification.md](api-specification.md); ownership/schema ở [database-design.md](database-design.md).

## Phần XVI Cấu trúc và nhóm

Giữ client/server/judge/database/storage/scripts/docs/tests/experiments/REPORT, bổ sung statics cho sơ đồ/kết quả. Router xử lý HTTP; schemas có model đầu vào; service có tính toán/projection, services chung có access/idempotency/files/activity/notifications. Phân công TV1 nền tảng/tích hợp, TV2 UI, TV3 DB/LMS/điểm, TV4 thi/judge. Họ tên/MSSV/tỷ lệ đóng góp để nhóm tự điền; không suy ra công sức cá nhân từ mã do AI hỗ trợ.

## Phần XVII Kiểm thử và thực nghiệm

Test auth/quyền/CSRF, CSV lỗi/hết hạn/concurrent/retry, private upload, deadline, QR trùng, cấu hình đề, bảo mật test/source, phiên thi, lease/fencing/retry, WS delivery/revocation, điểm/công bố/CSV, migration và backup/restore. Docker thật kiểm chứng ba ngôn ngữ, hai kiểu I/O, verdict/limits và file/network isolation. Frontend typecheck/lint/build và browser qua Nginx.

Thực nghiệm HTTP 1/5/10/20 client mô phỏng ×3; báo cáo p50/p95/error/throughput. Judge 20 submissions C/C++/Java, 1/2 worker ×3, cùng image/host/dataset. Lưu raw logs/metadata và phân tích hạn chế. Không nhận loopback là LAN nhiều máy; không lấy CI Linux thay bằng chứng Windows. [Kết quả](../experiments/RESULTS.md).

## Phần XVIII Vận hành và bàn giao

README có đủ 24 mục mẫu. Script setup/start API/client/worker/proxy, kiểm tra LAN, export, backup/verify/restore và đóng gói. Backup nhất quán DB+storage có manifest SHA-256, integrity/FK; restore đích mới, thu hồi session và reset job đang chạy. Không đưa môi trường, upload, DB thật hoặc secret lên Git/source nộp.

Báo cáo technical paper DOCX/PDF trong REPORT. Gói Source/Report theo Submission.md, hạn 23:59 31/10/2026. Người dùng tự điền nhóm; Compilatio và bàn giao theo thông báo học phần cần dữ liệu/thao tác thật.

## Phần XIX Điều kiện hoàn tất

Chức năng phải có code chạy, test tương ứng, build và tài liệu đúng. Có số đo và nguồn gốc thay vì điền số giả. Giới hạn Windows Docker/LAN vật lý/Compilatio được ghi riêng; không tick hoàn thành khi chưa có bằng chứng. Xem [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md) và README mục Final Verification.
