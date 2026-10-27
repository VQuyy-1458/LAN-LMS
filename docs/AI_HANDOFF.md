# Handoff bản hoàn thiện

Nguồn quyết định: yêu cầu trực tiếp ngày 25/10, PROJECT_PLAN 1.2, API 1.2, README và REQUIREMENTS_MATRIX. Tài liệu MEMBER_1/INTEGRATION_24_25 là lịch sử.

Có nhiều giữa kỳ/test và một cuối kỳ/course (chốt ngày 27/10); giữa kỳ lấy trung bình. Mỗi bài có bất kỳ AC hợp lệ được tính một lần; lỗi hoặc SE sau AC không xóa bài giải. Giảng viên chọn số bài và bảng quy đổi, mặc định 5 bài với ladder [0,5,7,8,9,10]. Trọng số đủ bốn thành phần, tổng 100%. Không lưu kết quả từng test. Không áp dụng lại policy nhiều final/MAX hoặc điểm test lẻ từ bản cũ.

Đã có mã cho auth, LMS, lịch, QR, bài tập, thi, phiên, submission, queue/worker, bảng điểm, WebSocket và backup. README có lệnh chạy; experiments/RESULTS có bằng chứng. Chỉ một API process; judge workers độc lập. SQLite và storage cùng host, không expose Docker ra web.

Người dùng tự điền thông tin nhóm và đã chốt push/merge vào develop sau kiểm thử, giữ nguyên main (cập nhật 26/10/2026). Thư mục gốc D:/Projects/LAN-LMS có thay đổi đang dở của công việc khác; không reset, ghi đè hoặc stage các file đó. Làm tại D:/Projects/LAN-LMS; không stage docs/CODE_OWNERSHIP.md và docs/LAN-LMS_Phan-cong-theo-file.xlsx của người dùng.

Ghi đúng giới hạn: Docker Windows đã được khôi phục và chấm thật; không coi CI là thay thế nghiệm thu LAN vật lý. Loopback không phải hai máy LAN vật lý. Compilatio/bàn giao cần tài khoản và xác nhận thật. Không tạo verdict, số liệu, tỷ lệ đóng góp hoặc kết quả Compilatio giả.


Quy định mới và chuyển khóa học/USB ngày 27/10: xem [CHANGES_20261027.md](CHANGES_20261027.md).


Hai khóa học có 40 tài khoản mẫu, PDF tự soạn, assignment có file đề, nhập testcase ZIP và ví dụ công khai: xem [CLASSROOM_DEMO.md](CLASSROOM_DEMO.md). Migration 0006 thêm file đề assignment; gói chuyển khóa phiên bản 1 cũ vẫn được đọc với attachment rỗng.

### Lịch tuần, điểm danh và tài khoản sinh viên

Hai khóa thực hành dùng mã LTM-2026-01 và CTDL-2026-01, mỗi khóa 20 sinh viên, 12 buổi học, 4 thông báo, 6 bài tập và 4 đề lập trình. Danh sách sinh viên của giảng viên có ngày sinh DD/MM/YYYY. Tài khoản tạo mới qua CSV dùng mật khẩu ngày sinh DDMMYYYY và bắt đổi ở lần đăng nhập đầu. Xem [hướng dẫn dữ liệu lớp](CLASSROOM_DEMO.md) và file thông tin cấp tài khoản riêng trong `.runtime/classroom-20261027/accounts.csv`; không commit thông tin đăng nhập.

Sinh viên chỉ mở camera/quét QR để điểm danh; giảng viên chọn buổi học và xem cập nhật danh sách. Các bộ lọc bài tập đếm toàn bộ dữ liệu trước phân trang. Tổng quan có lịch tuần, lịch tháng và hoạt động; danh sách khóa học nằm ở mục Khóa học.

## Phòng thi, điểm danh và bảng điểm

Đã bổ sung phòng thi riêng, phiên đăng nhập theo tab, điểm danh bằng hộp thoại QR, tiến độ bài tập chỉnh sửa tại bảng, nhập/xuất CSV và điểm sinh viên cập nhật trực tiếp. Chuyên cần mặc định 10, trừ 1 mỗi buổi vắng. Xem [quy trình sử dụng và giới hạn định dạng xem trước](PRACTICAL_WORKFLOWS.md).

## Cập nhật vòng đời và dữ liệu 28/10/2026

Quy tắc mới thay thế phần hướng dẫn cũ về mở lại đề, chỉnh điểm danh lịch sử và hủy tổng kết. Khóa đã chốt chỉ được xem/xuất; phiên điểm danh đã chốt không sửa hay tạo lại; danh sách phân trang 10 mục. Xem [hướng dẫn hiện hành và tài khoản bộ dữ liệu mới](LIFECYCLE_AND_DATA.md).
