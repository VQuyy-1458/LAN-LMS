# LAN-LMS Client

Next.js, React, TypeScript và Tailwind; cài theo lockfile. Từ client chạy `npm ci`, sau đó `npm run dev`, hoặc `npm run build` rồi `npm run start`. Script gốc `scripts/start_client.ps1` mặc định production; thêm `-Dev` khi phát triển.

AppShell/Realtime quản lý layout và WebSocket reconnect. Workspace chia nội dung khóa thành các panel. ExamEditor và ExamPlayer dành cho hai vai trò. REST helper gắn CSRF/cookie và chuẩn hóa lỗi. Thống kê từ API thật, không mock kết quả judge. Bản nháp code giữ theo session/problem trên trình duyệt; không đồng bộ sang thiết bị khác.

Chạy `npm run typecheck`, `npm run lint`, `npm run build`. Demo không phụ thuộc font/CDN/QR service bên ngoài. Khi đổi API, cập nhật docs/api-specification.md và kiểm tra lại quyền/ẩn điểm. README gốc hướng dẫn cùng origin, cấu hình và demo xuyên suốt.
