# Frontend LAN-LMS

Đã có Next.js/React/TypeScript/Tailwind và lockfile. Node 22 hoặc phiên bản tương thích Next.js đã chốt. Chạy từ client/: npm ci; npm run dev. Kiểm tra: npm run typecheck; npm run lint; npm run build. Không dùng create-next-app ghi đè thư mục hiện tại.

Đã nối API thật: login/me, đổi mật khẩu/logout với CSRF, chặn giao diện sai vai trò, khóa học, CSV preview/confirm, tài liệu, bài tập file và chấm tay. Màn exams/attendance/gradebook chưa phải chức năng hoàn chỉnh. Sidebar có các đường dẫn tương lai, không coi tất cả đã xong.

Copy .env.example thành .env.local để dùng API_UPSTREAM trong development; restart Next khi đổi. API gọi /api cùng origin. LAN dùng Nginx chuyển /api và /ws; thêm đúng web origin vào server/.env. Xem docs/INTEGRATION_24_25.md và MEMBER_1_HANDOFF.md.

src/components/: UI chung; src/features/courses/Workspace.tsx: luồng ghép LMS/bài tập; src/lib/api.ts: lỗi/CSRF/multipart; src/types/api.ts: auth types. Backend là nơi kiểm tra quyền thật, không tin chỉ ẩn trang frontend. Tài nguyên giao diện không tải font/CDN bắt buộc từ Internet.
