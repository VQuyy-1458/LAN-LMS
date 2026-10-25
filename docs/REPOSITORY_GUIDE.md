# Quy ước thư mục và nơi đặt code

Khung thư mục đã tạo theo PROJECT_PLAN.md mục 27. File có chữ scaffold/TODO/chưa triển khai chỉ giữ chỗ; không phải chức năng hoàn chỉnh. `.gitkeep` giúp Git lưu thư mục chưa có nội dung, có thể xóa khi thư mục đã có file thật.

## Phân công và đường dẫn

| Thành viên | Nơi làm việc chính |
|---|---|
| 1 | server/app/core/, server/app/main.py, server/app/modules/auth/, scripts cấu hình và tài liệu tích hợp |
| 2 | client/; routing src/app/, components/, features/, lib/, types/ |
| 3 | server/app/modules/students,courses,materials,attendance,gradebook; server/app/models/; database/; scripts backup/export |
| 4 | server/app/modules/assignments,coding_exams,submissions; judge/; docker-compose.yml; tests/load/ và experiments/ |

Mỗi người bổ sung test trong tests/ và cập nhật tài liệu module trong docs/. REPORT/ là báo cáo dùng chung, thành viên 1 tổng hợp. Không tạo thêm client/client, frontend, backend, report hoặc thư mục riêng theo tên thành viên bên cạnh cấu trúc đã chốt.

## Backend: một nơi sở hữu mỗi loại code

- core/: settings, DB/session, auth dependency và hạ tầng WebSocket dùng chung; đã có code đang chạy.
- modules/<tên>/router.py: endpoint của module; service.py: nghiệp vụ; schemas.py: request/response của riêng module. Các module ngoài auth mới là khung, chưa include vào app.
- api/routes/: điểm ghép router dùng chung khi cần; không viết lại endpoint đã có trong modules/.
- models/: ORM nghiệp vụ do thành viên 3 quản lý. User/AuthSession/LoginAttempt hiện ở core/database.py, chỉ import lại, không tạo định nghĩa bảng trùng.
- schemas/: schema dùng chung nhiều module; schemas riêng ở modules/<tên>/schemas.py.
- repositories/: truy vấn dữ liệu có thể tái sử dụng; services/: nghiệp vụ dùng chung nhiều module. Không sao chép cùng một service vào cả đây và module.
- modules/auth/ đã chuyển từ auth.py sang auth/router.py, public import router giữ nguyên nên main.py và API không đổi.
- Migration ở database/migrations/versions/, seed ở database/seed/. Thành viên 3 chốt thứ tự revision; không tự tạo database/schema.sql song song Alembic.

Khi thêm router phải áp dụng dependency auth/quyền, rồi include trong main.py. Không đăng ký router rỗng thành API giả và không bỏ kiểm tra quyền để frontend chạy demo. Chính sách quyền khóa học thật vẫn chờ course/enrollment.

## Frontend và judge

Frontend có page.tsx/layout.tsx và cấu hình khung; package.json chưa chọn dependencies/scripts nên chưa chạy được. Thành viên 2 bổ sung đúng vào client/, commit lockfile khi chốt phiên bản, không chạy trình tạo ứng dụng ghi đè toàn thư mục. Không dùng `(student)`/`(teacher)` làm prefix URL, hiện đã có student/teacher rõ ràng.

Judge worker.py/job_queue.py/limits.py chưa triển khai, chạy trực tiếp sẽ báo lỗi rõ. docker-compose.yml có services rỗng; không coi là sandbox có sẵn. File start_client.ps1 báo thiếu cấu hình cho đến khi có script dev. backup_database.py/export_data.py chưa tạo backup/export thật; không dùng để bàn giao dữ liệu trước khi thành viên 3 hoàn thành.

## Dữ liệu và kiểm thử

- storage/: dữ liệu runtime, không commit upload/bài nộp; ngoại lệ .gitkeep để clone vẫn có thư mục.
- tests/unit, integration, load, fixtures: kiểm thử và dữ liệu giả lập. Giữ test_member1.py hiện có cho tới khi nhóm thống nhất sắp xếp lại.
- experiments/raw, results: chỉ ghi số liệu thực tế; hiện giữ chỗ, chưa có benchmark.
- docs/: nguồn đặc tả và hướng dẫn; REPORT/: báo cáo cuối và figures/. Không ghi secret vào tài liệu.

## Làm việc sau khi clone

1. Đọc README, PROJECT_PLAN, API và MEMBER_1_HANDOFF; xem module nào thật sự đã triển khai.
2. Tạo nhánh tính năng từ bản chung nhóm thống nhất, cập nhật trước khi làm.
3. Viết vào file khung tương ứng; thư mục con theo tính năng được phép khi cần, cập nhật tài liệu nếu thay đổi cấu trúc cấp cao. Không ép mọi logic vào một file chỉ để giữ nguyên số file.
4. Không commit .venv, node_modules, .env, DB thật, upload hay dữ liệu cá nhân.
5. Test module và các test backend đang có trước khi merge. Cấu trúc khung không đồng nghĩa toàn hệ thống đã chạy.


## Cập nhật tích hợp ngày 25/10/2026

Xem [INTEGRATION_24_25.md](INTEGRATION_24_25.md) để biết phần đã triển khai, CI Docker, lệnh chạy và giới hạn môi trường. Chỉ lưu kết quả tổng bài và một kỳ thi cuối kỳ/course. Frontend auth/LMS/bài tập và Docker runner đã có code thật; worker tự động/QR/gradebook chưa hoàn thành.
