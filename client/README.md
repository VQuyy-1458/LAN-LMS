# Frontend — thành viên 2

Đã có file khung cho các trang và cấu hình TypeScript; chưa có chức năng hoặc dependencies. `package.json` cố ý chưa có scripts/dependencies, không phải ứng dụng chạy được. Chọn phiên bản Next.js/React/TypeScript/Tailwind tương thích, bổ sung scripts dev/build/typecheck, tạo và commit package-lock.json khi bắt đầu triển khai. Không chạy create-next-app thành thư mục client lồng bên trong client.

- src/app: routing/layout/page; public/login ra URL /login, student/* và teacher/* có prefix riêng.
- src/components: thành phần giao diện tái sử dụng.
- src/features: logic/giao diện theo tính năng.
- src/lib: HTTP client, auth/CSRF, WebSocket và tiện ích dùng chung.
- src/types: kiểu dữ liệu API thống nhất với docs/api-specification.md.
- public: tài nguyên tĩnh công khai, không đặt bài nộp/tài liệu riêng tư ở đây.

Thay nội dung placeholder khi triển khai, kiểm tra auth ở backend; không coi việc ẩn trang là phân quyền. Theo docs/MEMBER_1_HANDOFF.md để kết nối auth. Gọi /api và /ws cùng origin, không hard-code localhost/IP trong trang. next-env.d.ts được Next.js sinh khi môi trường đã thiết lập; không tự tạo kiểu giả.
