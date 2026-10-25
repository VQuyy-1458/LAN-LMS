# Kế hoạch hoàn thiện và nghiệm thu LAN-LMS

Ngày đối chiếu: 25/10/2026. Bản nền: develop `1deaffe`. Nhánh thực hiện: `codex/complete-lan-lms`.

Tài liệu này ghi yêu cầu và bằng chứng cần có, không xác nhận chức năng đã hoàn thành. Khi code hoặc kết quả kiểm thử thay đổi, cập nhật trạng thái theo bằng chứng thực tế.

## 1. Nguồn yêu cầu và thứ tự áp dụng

- Chỉ đạo trực tiếp của người dùng trong cuộc trao đổi, gồm chỉ lưu kết quả tổng bài và một kỳ thi cuối kỳ/course; có cả giữa kỳ và cuối kỳ; điểm thi quy đổi theo số bài đã AC.
- Bốn tài liệu giảng viên: Instruction.md, README.md mẫu, Submission.md, Topics.md trong thư mục final-project được người dùng cung cấp.
- Đặc tả nghiệp vụ docs/PROJECT_PLAN.md, hợp đồng docs/api-specification.md và quyết định đã chốt. Khi có mâu thuẫn phải sửa các tài liệu này cùng code, không vận hành hai chính sách khác nhau.
- Hai ảnh tham khảo giao diện sinh viên chỉ định hướng bố cục, màu sắc và cách trình bày; không bổ sung chức năng ngoài đặc tả chỉ vì xuất hiện trong ảnh. Không sao chép thương hiệu, thông tin liên hệ hay tên người trong ảnh vào sản phẩm.

Instruction.md cho phép thay đổi cấu trúc thư mục nếu dễ đọc, dễ chạy. Giữ client/, server/, judge/, database/, scripts/, docs/, tests/, experiments/, REPORT/ hiện có để tránh phá import và công việc của nhóm. Gói bàn giao cuối có Source/ và Report/ theo Submission.md.

## 2. Kiểm kê ban đầu

| Nhóm | Bản nền đã có | Phần phải hoàn thiện và nghiệm thu |
|---|---|---|
| Auth/quyền | Session, CSRF, Origin, password gate, rate limit, quyền course/enrollment | Hồi quy tất cả endpoint mới, UI phiên hết hạn, không lộ dữ liệu ngoài course |
| Khóa học/CSV | API course/membership, preview/confirm transaction và retry | UI sửa/chi tiết/roster, thống kê tài khoản mới/cũ; test preview hết hạn và confirm đồng thời |
| Tài liệu/bài tập | Private file, deadline, resubmit, lịch sử, chấm tay và feedback | Hoàn thiện UI và trạng thái công bố; kiểm tra toàn luồng teacher/student |
| Lịch/thông báo | CalendarEvents có schema | API CRUD đúng quyền, mô tả/loại sự kiện, lịch theo course và dashboard dùng dữ liệu thật |
| Điểm danh | Schema session/record | Token hữu hạn, QR và nhập mã, đóng phiên, lịch sử, chống trùng, chỉnh sửa có lý do/audit |
| Thi lập trình | Schema exam/problem/test/session/submission/job/result | Toàn bộ API và UI cấu hình đề/test, mở/đóng thi, đăng ký/phiên, giờ server, nộp và lịch sử |
| Judge | Docker runner C17/C++17/Java, stdio/file, limits và tổng điểm | Queue bền vững, claim/lease/heartbeat, recovery, kết quả có fencing, worker CLI và vận hành |
| Realtime | WS xác thực, heartbeat, queue hữu hạn | Sự kiện nghiệp vụ từ worker tới đúng người; reconnect, phục hồi REST, trạng thái kết nối/phiên |
| Bảng điểm | Schema components/grades | Công thức phía server, cấu hình trọng số, null/zero, công bố/thu hồi, CSV và audit |
| Vận hành | Script server/client/proxy, migration, seed | Backup/restore cả DB và storage, script cài/chạy worker, health và hướng dẫn máy mới |
| Thực nghiệm | CI và test nền; thư mục experiments | Script tải đồng thời, raw logs, bảng p50/p95/error/throughput, so sánh 1/2 worker bằng số liệu thật |
| Tài liệu/báo cáo | Đặc tả và tài liệu từng phần | README theo mẫu, báo cáo technical paper DOCX/PDF, sơ đồ, references, demo và gói nộp |

Không xem file giữ chỗ hoặc router rỗng là chức năng đã có. worker.py, job_queue.py, attendance, coding_exams, submissions, gradebook còn cần triển khai tại thời điểm đối chiếu.

## 3. Trình tự thực hiện

1. Chốt các lựa chọn còn thiếu: giữa kỳ, cách chọn lần nộp, thông tin nhóm và cách bàn giao Git.
2. Đồng bộ quyết định trong đặc tả/API/schema. Mỗi thay đổi schema có migration; thử nâng cấp DB đã có dữ liệu, không chỉ DB trống.
3. Hoàn thiện backend lịch, điểm danh, thi, submission và bảng điểm. Dùng cùng auth, permission, lỗi, pagination và idempotency hiện có.
4. Xây queue/worker độc lập với API; kiểm thử đồng thời, lease hết hạn, worker chết, không ghi đè kết quả của attempt mới bằng attempt cũ.
5. Tích hợp giao diện student và teacher: dashboard, course detail, lịch, QR, assignment, exam editor/player/monitor, gradebook. Dữ liệu từ API thật; có loading/empty/error/retry và thông báo lưu thành công rõ ràng.
6. Tích hợp WS và fallback REST; test mất kết nối sau khi server đã nhận submission, giờ hết hạn và hồi phục phiên.
7. Hoàn thiện scripts vận hành, backup/restore và đóng gói; thử phục hồi dữ liệu và file thực tế trên bản sao biệt lập.
8. Kiểm thử xuyên suốt, chạy thực nghiệm thật, viết README/báo cáo từ đúng kết quả thu được.
9. Kiểm tra diff/secret/artefact, chạy CI và bàn giao nhánh Git theo lựa chọn người dùng. Chỉ cập nhật dấu hoàn thành khi có bằng chứng.

## 4. Định hướng giao diện

- Nền trắng/xám rất nhạt; đỏ làm màu hành động chính, xanh đậm cho tiêu đề, chữ dễ đọc.
- Dashboard có phần chào, thống kê, lịch và hoạt động sắp tới; số liệu được tính từ dữ liệu của người đang đăng nhập.
- Khóa học có tìm kiếm, bộ lọc và thẻ nội dung; chi tiết tách các mục tổng quan/tài liệu/lịch/điểm danh/bài tập/thi/điểm.
- Teacher dùng cùng hệ thống thiết kế nhưng có thao tác quản trị, bảng dữ liệu và form phù hợp.
- Bố cục co giãn cho laptop, không nhồi mọi chức năng vào một form dài; label, focus, trạng thái disabled và thông báo lỗi rõ ràng.
- Chạy LAN không phụ thuộc CDN, font từ Internet hoặc tài nguyên từ website tham khảo.

## 5. Bằng chứng cần đạt

### Chức năng và dữ liệu

- Teacher tạo khóa, import CSV, giao tài liệu/bài tập, chấm và công bố; student bắt buộc đổi password rồi truy cập đúng khóa.
- Teacher tạo đề có test và giới hạn; student thi C/C++/Java cả stdio/file, nhận aggregate verdict/score, xem lịch sử riêng.
- Không trả test ẩn, source của người khác, đường dẫn nội bộ, token hoặc mật khẩu qua API/log/export.
- Server quyết định quyền, deadline và điểm. Đổi đồng hồ trình duyệt không kéo dài giờ thi.
- QR hết hạn/đóng phiên/không thuộc khóa bị từ chối; retry/check-in đồng thời không tạo trùng.
- Điểm chưa có khác điểm 0; trọng số hợp lệ; sửa điểm sau công bố phải thu hồi và ghi audit.

### Độ tin cậy và mạng

- Submission + job được ghi nguyên tử; cùng key/dữ liệu không tạo job trùng, key cũ/dữ liệu khác bị từ chối.
- Worker dừng giữa chừng: job có thể nhận lại sau lease, chỉ attempt sở hữu hiện hành được ghi kết quả.
- WS được xác thực và giới hạn queue; browser kết nối lại lấy trạng thái đúng từ REST.
- Test lỗi dữ liệu, disconnect, timeout, DB busy và dependency không sẵn sàng; không dùng kết quả chấm giả khi Docker lỗi.
- Test filesystem/network isolation thật trong Docker, ngoài các test CPU/RAM/time/output đã có.
- Cài sạch, migration từ dữ liệu cũ, restore cả SQLite + private storage, kiểm tra tính toàn vẹn file.

### Thực nghiệm và báo cáo

- Client đồng thời 1/5/10/20 với tài khoản riêng; ghi p50/p95, error rate và throughput.
- Một/hai worker: cùng dataset, giới hạn và máy, nhiều lần chạy; ghi queue wait, compile/run/end-to-end và throughput.
- Raw logs, thời điểm, cấu hình máy, phiên bản phần mềm, script và cách chạy lại nằm trong experiments/ và tests/load/.
- Không gọi tải mô phỏng trên một máy là kiểm thử nhiều máy vật lý. Không suy ra Windows Docker từ CI Linux.
- Novelty giữ đúng phạm vi kỹ thuật đã cam kết: queue/lease, chống lặp và WS/REST recovery; chỉ nêu đóng góp có code và bằng chứng. Giao diện đẹp không thay cho đóng góp kỹ thuật.

## 6. README và bộ nộp

README theo 24 mục của mẫu giảng viên: thông tin project/nhóm; problem/objective/scope; system overview; architecture; network design; stack; novelty/baseline; cấu trúc; requirements; installation; running/tests/multiple clients; features; experimental setup/results; discussion; limitations; future work; report; references; contribution; demo; submission; verification; contact.

Báo cáo theo Instruction.md: Title, Abstract, Keywords, Introduction, Background/Related Work, Problem Definition, Proposed Approach, System Architecture, Network Communication Design, Implementation, Experimental Setup, Results, Discussion, Novelty/Contributions, Limitations, Future Work, Conclusion, References và Appendix.

Bộ bàn giao theo Submission.md:

```text
NhomXX_LANLMS/
├── Source/
│   └── NhomXX_LANLMS_Source/
└── Report/
    ├── NhomXX_LANLMS_Report.docx
    └── NhomXX_LANLMS_Report.pdf
```

Tên/số nhóm chưa được xác nhận nên XX chỉ là chỗ điền, không phải dữ liệu thật. Không tự khai phần trăm đóng góp cá nhân nếu chưa có xác nhận của nhóm.

Hạn nộp ghi trong tài liệu: 23:59 ngày 31/10/2026, giờ Việt Nam. Submission.md hướng dẫn Compilatio và USB; Instruction.md/README mẫu còn nhắc Drive. Chuẩn bị gói có thể dùng cho cả hai và làm theo thông báo cuối của giảng viên.

## 7. Những việc cần xác nhận hoặc thao tác ngoài code

- Đã chốt: giữa kỳ và một cuối kỳ/course; chỉ bài AC được tính. Một bài đã AC không mất kết quả vì lần sau sai. Giảng viên chọn số bài và bảng quy đổi; mặc định 5 bài: 0/1/2/3/4/5 AC = 0/5/7/8/9/10. Trọng số do giảng viên cấu hình, tổng 100%.
- Người dùng tự điền thông tin nhóm; đã chốt push và merge vào develop sau hoàn thiện/kiểm thử, giữ nguyên main (cập nhật 26/10/2026).
- Số nhóm, họ tên/MSSV/email, giảng viên, đóng góp cá nhân: cần thông tin thật.
- Docker Desktop Windows trước đó bị treo; phải kiểm tra lại engine trước nghiệm thu trên máy này.
- Nghiệm thu hai máy LAN cần hai máy thực; có thể chuẩn bị script/hướng dẫn nhưng không khai đã chạy khi chưa có bằng chứng.
- Compilatio cần tài khoản/kết quả thật của nhóm; chỉ được ghi tỷ lệ thực tế khi kiểm tra xong. Không tự xác nhận đạt ngưỡng 20%.
- Việc nộp Compilatio, gửi lớp trưởng/Drive và xác nhận tất cả thành viên hiểu code cần người dùng thực hiện/xác nhận.
