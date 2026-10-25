# Đối chiếu yêu cầu bài tập lớn

Bốn file gốc ở docs/requirements. Code và tài liệu trong cùng bản phát hành; trạng thái nghiệm thu thực tế được ghi ở ACCEPTANCE.md và experiments/RESULTS.md.

| Nguồn | Yêu cầu | Minh chứng trong project |
|---|---|---|
| Instruction 3 | Problem, objective, architecture | README 2–4; PROJECT_PLAN; sơ đồ statics |
| Instruction 3–6 | Network/message/concurrency/error | API contract; REST/WS; queue/lease; tests auth/WS/race/retry |
| Topics 4.5 | Nhận bài, compiler, test, worker/result | coding_exams/submissions, judge, Docker integration |
| Topics 4.6 | Phiên, giờ, mất kết nối, nhiều client | server deadlines, session reuse, heartbeat, WS/REST recovery |
| Instruction 7 | Novelty/Contributions | Queue/idempotency/fencing và baseline một so với hai worker; không tính UI là novelty |
| Instruction 8 | Technical paper | REPORT_SOURCE và báo cáo DOCX/PDF đủ các phần |
| Instruction 9 | Thực nghiệm thật | Script HTTP 1/5/10/20 và Docker 1/2 worker, raw logs, metadata, biểu đồ và discussion |
| Instruction 12–13 | Cấu trúc và README | Giữ cấu trúc nhóm; README theo đủ 24 mục mẫu, có lệnh cài/run/test |
| README mẫu 1/20 | Nhóm và đóng góp | Bảng có chỗ điền; người dùng xác nhận sẽ tự bổ sung, không tự khai tỷ lệ |
| Submission 1 | Một báo cáo DOCX đúng tên | NhomXX_LANLMS_Report.docx; thêm PDF để đọc |
| Submission 2–3 | Source chạy được, Source/Report | package_submission, lockfile, migration, sample data và hướng dẫn |
| Instruction/Submission | Compilatio | Cần nhóm kiểm tra và lưu kết quả thật; không tự xác nhận đạt |
| Instruction/Topics | Demo nhiều client | Test tải mô phỏng và CI có bằng chứng; LAN hai máy vật lý cần nghiệm thu riêng |
| User 25/10 | Chỉ kết quả tổng bài | Không có per-test result; hidden tests không trả student |
| User 25/10 | Giữa kỳ và một cuối kỳ | Unique index mỗi loại/course, API/UI thống nhất |
| User 25/10 | Điểm theo bài AC | Ladder mặc định [0,5,7,8,9,10], cấu hình N/ladder, AC giữ lại qua các lần sai |
| User 25/10 | Tham khảo UI student | Dashboard/lịch/thẻ khóa, nền sáng/đỏ/xanh đậm; chức năng theo đặc tả riêng |

Các mục cài sạch trên máy khác, Docker Windows, LAN vật lý, điền nhóm, Compilatio và bàn giao chính thức cần người dùng/nhóm thực hiện hoặc cung cấp môi trường. Gói source và test không thay thế bằng chứng cho các mục này.
