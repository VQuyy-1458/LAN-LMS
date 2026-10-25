# Quyết định triển khai

Bản hiện hành 1.2 ngày 25/10/2026: PROJECT_PLAN.md, api-specification.md và README là nguồn chính. MEMBER_1/INTEGRATION_24_25 là nhật ký lịch sử.

1. Next.js/TypeScript/Tailwind, FastAPI, SQLite/Alembic, private files, Docker Linux judge, REST/WS và Nginx cùng origin. Một API process, một/hai judge worker.
2. Server session tám giờ; Argon2id; cookie HttpOnly, CSRF/Origin; bắt buộc đổi mật khẩu ban đầu. Quyền course/enrollment lấy từ DB.
3. CSV preview/confirm all-or-nothing và idempotency; không reset password cũ. Backend quyết định deadline, quyền và điểm.
4. Một giữa kỳ và một cuối kỳ/course. Chỉ AC tính bài giải đúng, mỗi bài một lần; lỗi/SE sau AC không xóa AC. Giảng viên chọn N và ladder; mặc định 5 bài [0,5,7,8,9,10]. Đủ bốn trọng số, tổng 100%. Chỉ lưu aggregate result.
5. Queue lưu SQLite, có lease/fencing/retry; outbox tới WS và REST recovery. Không giả AC khi hạ tầng lỗi.
6. Giữ cấu trúc repo đã thống nhất. Báo cáo DOCX/PDF và gói Source/Report theo yêu cầu nộp. Người dùng tự điền nhóm và đã chốt push/merge vào develop sau kiểm thử; giữ nguyên main theo chỉ dẫn mới nhất ngày 26/10/2026.
7. Số liệu thật và nguồn CI ở experiments. Windows Docker, LAN vật lý, Compilatio và thông tin nhóm phải kiểm chứng riêng; không tự tick.
