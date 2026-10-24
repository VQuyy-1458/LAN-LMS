# Database

Phụ trách: 3.

Auth models hiện ở server/app/core/database.py; không định nghĩa lại bảng users. Model nghiệp vụ mới đặt ở server/app/models/ và migration nối từ 0001_auth. Ghi quan hệ, unique/FK và transaction khi triển khai.

Cần cập nhật khi triển khai: đường dẫn mã nguồn, lệnh chạy đã thử, kiểm thử thực tế và hạn chế còn lại.
