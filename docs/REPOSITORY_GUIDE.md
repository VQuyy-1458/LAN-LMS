# Bản đồ mã nguồn

- `client/src/app`: route và layout public/student/teacher. `components/AppShell` và `Realtime` là khung dùng chung.
- `client/src/features/courses`: Dashboard, Workspace và các panel sinh viên, tài liệu, lịch, điểm danh, bài tập, thi, điểm. ExamEditor dành cho teacher; ExamPlayer dành cho student.
- `server/app/core`: cấu hình, database, bảo mật và WebSocket.
- `server/app/modules`: mỗi module có router/schemas/service; courses có thêm calendar và dashboard.
- `server/app/services`: access, idempotency, private files, audit/outbox và notification bridge.
- `judge`: queue bền vững, worker riêng, Docker runner/supervisor, giới hạn và comparator.
- `database/migrations`: lịch sử 0001–0004; metadata 0002 được đóng băng. Seed demo là dữ liệu tùy chọn.
- `scripts`: cài/chạy, kiểm tra LAN, backup/verify/restore, export và đóng gói.
- `tests`, `experiments`, `statics`, `REPORT`: kiểm thử, số liệu, hình và báo cáo.

Không đặt upload vào public hoặc source. API và worker dùng cùng DB/storage. Triển khai thật dùng migration, không dùng create_all. Không đưa mật khẩu, token, test ẩn, DB hoặc upload thật lên Git. Giữ cấu trúc này khi các thành viên tiếp tục sửa.
