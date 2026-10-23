# LAN-LMS

Hệ thống quản lý học tập và thi lập trình trên mạng LAN theo mô hình Client–Server, dành cho nhóm 4 thành viên.

**Trạng thái ngày 24/10/2026:** đã triển khai nền tảng backend thành viên 1 (auth, session, CSRF, quyền dùng chung, WebSocket, migration và kiểm thử). Frontend, nghiệp vụ LMS và judge chưa triển khai. Xem [hướng dẫn chạy và bàn giao](docs/MEMBER_1_HANDOFF.md).

## Tài liệu chính

- [Bản đặc tả và kế hoạch đầy đủ 1.1](docs/PROJECT_PLAN.md): giữ khung 19 phần của bản nhóm cung cấp; bổ sung quyết định kỹ thuật, phân công, thực nghiệm và nộp bài ở phần XX.
- [Hợp đồng API 1.1](docs/api-specification.md): xác thực, request/response, quyền, upload, retry, phiên thi và WebSocket.

## Mục tiêu và phạm vi

Giảng viên tạo khóa học, import CSV để cấp tài khoản, upload tài liệu, giao bài, tổ chức thi C/C++/Java, điểm danh QR và quản lý bảng điểm. Sinh viên dùng trình duyệt trên máy trong LAN để đăng nhập, đổi mật khẩu lần đầu, học và nộp bài.

Luồng nghiệm thu: giảng viên đăng nhập → tạo khóa học → import CSV → sinh viên đăng nhập/đổi mật khẩu → tải tài liệu → nộp file/code → nhận kết quả → điểm danh → xem điểm đã công bố → xuất CSV.

Lịch/sự kiện độc lập, thông báo nâng cao, bài nhiều file/project và PostgreSQL là phần mở rộng. Các chức năng trên là mục tiêu, chưa đánh dấu hoàn thành.

## Kiến trúc và công nghệ

```text
Trình duyệt trên các máy LAN
           | HTTP REST / WebSocket cùng origin
           v
Web frontend / proxy (Next.js, TypeScript, Tailwind)
           |
           v
FastAPI ---- SQLite (SQLAlchemy, Alembic)
   |             | submission + judge_jobs bền vững
File storage     v
            Judge Worker riêng
                 |
            Docker Linux trên WSL2
            C17 / C++17 / Java
```

Máy chủ mục tiêu Windows. Browser không truy cập DB/worker. Auth dùng session cookie HttpOnly và CSRF; password hash Argon2id. Job có lease và phục hồi khi worker lỗi; chỉ báo qua WebSocket sau khi trạng thái được lưu. Mất WS lấy lại trạng thái qua REST. Cấu hình container, concurrency và quyền phải được kiểm thử thực tế.

HTTP/REST và hướng ứng dụng mạng phù hợp tài liệu học phần đã cung cấp; không có yêu cầu bắt buộc tự viết TCP Socket thuần trong các file đó. Nhóm phải giải thích được message flow, concurrency và error handling.

## Phân công

| Thành viên | Phụ trách |
|---|---|
| 1 | Auth, chuẩn API, WebSocket, cấu hình web, tích hợp và tổng hợp bàn giao |
| 2 | Frontend hai vai trò, REST/WS, kiểm thử luồng trên nhiều máy |
| 3 | Database/migration, khóa học, CSV, tài liệu, QR, điểm và backup |
| 4 | Bài tập, kỳ thi, submission, queue/worker/sandbox và benchmark |

Tên/MSSV và tỷ lệ đóng góp thực tế sẽ được nhóm bổ sung; không mặc định ai cũng 25%. Mỗi người có code, test và tài liệu của mình.

## Cấu trúc hiện tại và kế hoạch

Hiện có `server/app/`, `database/migrations/`, `scripts/`, `tests/` và tài liệu. Xem [bàn giao thành viên 1](docs/MEMBER_1_HANDOFF.md) để chạy backend và tích hợp.

Khi triển khai sẽ tạo `client/`, `server/`, `judge/`, `database/`, `storage/`, `scripts/`, `tests/`, `experiments/`, `REPORT/`. Không coi các thư mục mô tả trong kế hoạch là đã tồn tại.

## Cài đặt, cấu hình và chạy

Backend đã có dependency lockfile, migration và lệnh chạy trong [hướng dẫn thành viên 1](docs/MEMBER_1_HANDOFF.md). Trước bàn giao toàn hệ thống vẫn cần:

1. Phiên bản Python, Node, compiler/JDK, Docker/WSL2 đã thử.
2. Dependency/lockfile, build image judge và `.env.example` không có secret.
3. Migration, seed giả lập và cách tạo teacher tương tác.
4. Lệnh chạy web, backend, proxy WS và worker; IP LAN, firewall, cookie/origin.
5. Kiểm thử trên máy sạch và ít nhất hai máy LAN; backup nhất quán DB/storage và restore thật.

Demo cốt lõi dự kiến chạy không cần Internet sau cài đặt. Cài dependency/image lần đầu có thể cần Internet; nếu bàn giao offline phải chuẩn bị gói cần thiết. Không tải font/CDN trong luồng bắt buộc.

## Kiểm thử, thực nghiệm và đóng góp

Chưa có kết quả đo. Kế hoạch kiểm thử gồm quyền, CSV trùng/lỗi, hạn thi, gửi bài lặp, C/C++/Java, file I/O, sandbox, mất WS và worker dừng. Thực nghiệm so sánh một/hai worker cùng bộ submission, đo queue wait, thời gian chấm và throughput; thử 1/5/10/20 client mô phỏng. Lưu dữ liệu thô, cấu hình và script tái lập; không bịa số liệu.

Đóng góp dự kiến là tích hợp hàng đợi bền vững, chấm tách API và khôi phục trạng thái qua REST/WS. Chỉ xác nhận đóng góp có bằng chứng triển khai/thực nghiệm, không tuyên bố thuật toán mới.

## Hạn chế và an toàn

SQLite một máy chủ cần kiểm thử ghi đồng thời. Docker/WSL2 cần thiết lập đúng và không bảo đảm an toàn tự động. Ngày sinh chỉ dùng làm mật khẩu khởi tạo theo phạm vi nhóm, buộc đổi trước khi học. QR/IP không chứng minh tuyệt đối sự có mặt/danh tính. Demo HTTP LAN không bảo mật đường truyền như HTTPS.

## Làm việc và nộp bài

Không commit trực tiếp main; nhánh tính năng tích hợp vào develop, kiểm tra trước khi đưa vào main. Không commit secret hoặc dữ liệu cá nhân thật. API/schema thay đổi phải cập nhật tài liệu và thông báo nhóm.

Hạn cuối **23:59 ngày 31/10/2026, giờ Việt Nam**. Theo Submission.md: một báo cáo Compilatio, tên `NhomXX_LANLMS_Report.docx` (khuyến nghị DOCX), source đầy đủ và chạy được; bàn giao `NhomXX_LANLMS/Source/` và `Report/` qua lớp trưởng/USB. Instruction.md/README mẫu còn nhắc Drive; theo dõi thông báo cuối để thống nhất phương thức. Kiểm tra Compilatio theo ngưỡng ≤20%, trích dẫn nguồn và lưu phiên bản báo cáo cuối.

## Nguồn yêu cầu và tham khảo

Nguồn học phần người dùng cung cấp: Instruction.md, Topics.md, README.md mẫu và Submission.md. Báo cáo cuối phải trích dẫn tài liệu kỹ thuật thực sự sử dụng, gồm framework, compiler, runtime và các nguồn liên quan; chưa có mục Related Work hay kết quả thực nghiệm hoàn chỉnh.

- [Next.js — Route Groups](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups): nhóm trong ngoặc không tạo URL prefix; dùng student/teacher để tách đường dẫn.
