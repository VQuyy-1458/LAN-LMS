# Handoff bản hoàn thiện

Nguồn quyết định: yêu cầu trực tiếp ngày 25/10, PROJECT_PLAN 1.2, API 1.2, README và REQUIREMENTS_MATRIX. Tài liệu MEMBER_1/INTEGRATION_24_25 là lịch sử.

Có một giữa kỳ và một cuối kỳ/course. Mỗi bài có bất kỳ AC hợp lệ được tính một lần; lỗi hoặc SE sau AC không xóa bài giải. Giảng viên chọn số bài và bảng quy đổi, mặc định 5 bài với ladder [0,5,7,8,9,10]. Trọng số đủ bốn thành phần, tổng 100%. Không lưu kết quả từng test. Không áp dụng lại policy nhiều final/MAX hoặc điểm test lẻ từ bản cũ.

Đã có mã cho auth, LMS, lịch, QR, bài tập, thi, phiên, submission, queue/worker, bảng điểm, WebSocket và backup. README có lệnh chạy; experiments/RESULTS có bằng chứng. Chỉ một API process; judge workers độc lập. SQLite và storage cùng host, không expose Docker ra web.

Người dùng tự điền thông tin nhóm và đã chốt push/merge vào develop sau kiểm thử, giữ nguyên main (cập nhật 26/10/2026). Thư mục gốc D:/Projects/LAN-LMS có thay đổi đang dở của công việc khác; không reset, ghi đè hoặc stage các file đó. Dùng managed checkout của chat này để làm việc.

Ghi đúng giới hạn: Docker Desktop Windows lỗi khởi động; CI Linux không thay nghiệm thu Windows. Loopback không phải hai máy LAN vật lý. Compilatio/bàn giao cần tài khoản và xác nhận thật. Không tạo verdict, số liệu, tỷ lệ đóng góp hoặc kết quả Compilatio giả.
