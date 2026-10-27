# Quy tắc sử dụng và dữ liệu lớp mới

## Phiên thi, xóa và tổng kết

Sinh viên nộp sớm hoặc hết giờ sẽ không mở lại đề, ví dụ, source và màn làm bài. Kết quả vẫn cập nhật tại bảng điểm khi chấm xong. Request nộp đã ghi nhận trước khi kết thúc có thể retry cùng Idempotency-Key để nhận biên nhận cũ; không tạo thêm bài nộp. Giảng viên vẫn xem đề, phiên và xuất điểm thi CSV.

Xóa khóa học, kỳ thi và bài tập đều có hộp thoại xác nhận. Hủy không thay dữ liệu. Xóa trong ứng dụng ẩn tài nguyên và loại khỏi lịch/điểm tự động; dữ liệu lịch sử được giữ để bảo toàn liên kết và backup. Xóa đề cuối kỳ giải phóng vị trí cuối kỳ để tạo đề mới. Khóa đã tổng kết không được xóa.

Chốt tổng kết ở Bảng điểm yêu cầu đủ đầu điểm, không còn thành phần bắt buộc chưa hoàn tất. Sau khi xác nhận, khóa học chuyển sang `finalized`: toàn bộ yêu cầu sửa/xóa/upload/nhập CSV/nộp bài bị máy chủ từ chối, bao gồm gọi API trực tiếp. Vẫn xem hồ sơ, học liệu, lịch, điểm và xuất CSV/ZIP. Không có nút mở khóa hoặc hủy tổng kết.

Các thay đổi được tuần tự hóa trong transaction SQLite trước kiểm tra trạng thái khóa, ngăn thao tác sửa chạy đồng thời với chốt tổng kết. Đổi mật khẩu và đăng nhập vẫn hoạt động bình thường.

## Điểm danh và điểm trực tiếp

Mỗi buổi học có tối đa một phiên điểm danh. Đang mở có thể tạo lại QR để đổi mã, giữ nguyên danh sách. Đã đóng hoặc hết hạn thì chốt vĩnh viễn: không tạo lại, không sửa trạng thái, không sửa/xóa buổi học liên quan. Buổi đã chốt biến mất khỏi lựa chọn tạo QR; lịch sử chỉ còn danh sách sinh viên và trạng thái, phân trang 10 người.

Chuyên cần = max(0, 10 - số buổi đã chốt mà sinh viên vắng). Có mặt và Đến muộn đều tính tham gia. Đóng phiên khiến người chưa điểm danh được tính vắng; điểm tự cập nhật. Điểm bài tập tự tính từ các bài đã có điểm và các bài hết hạn; chưa nộp sau hạn tính 0, bài chờ chấm chưa đủ dữ liệu. Giữa kỳ là trung bình những đề đã có kết quả, cập nhật khi từng đề hoàn tất; chốt tổng kết vẫn cần đầy đủ các đề bắt buộc. Cuối kỳ theo đề cuối kỳ, chờ bộ chấm xử lý xong. Điểm điều chỉnh thủ công được ưu tiên; để trống bỏ điều chỉnh.

## Danh sách, lịch và file đề

Tất cả danh sách hiển thị tối đa 10 mục/trang, có chuyển trang; các API phân trang trả tối đa 10 dù client cũ yêu cầu nhiều hơn. CSV/ZIP vẫn xuất toàn bộ dữ liệu được phép. Bộ chọn và bảng lịch tuần là điều hướng/lưới lịch, không cắt bỏ dữ liệu theo giới hạn danh sách.

Thanh bên hiển thị chức năng thành cây con của Khóa học đang chọn. Khóa được lọc theo kỳ 1/kỳ 2/kỳ hè và năm học. Tạo/sửa khóa dùng danh sách chọn kỳ và hai năm liên tiếp, máy chủ kiểm tra cùng quy tắc.

Chỉ tự tạo Lịch học và Thông báo. Lịch thi và hạn bài tập được suy ra từ nguồn, tự cập nhật khi sửa hoặc xóa nguồn; không chỉnh hai loại này trong lịch. Lịch khóa lọc Tổng số/Lịch học/Lịch thi/Hạn bài tập. Lịch tổng vẫn tổng hợp các khóa có quyền truy cập.

Bài tập hỗ trợ tối đa 10 file đề/hướng dẫn, mỗi file 20 MiB, tổng 100 MiB. Chọn file ngay khi tạo; thông tin và tất cả file được ghi cùng transaction. Sau khi tạo, vào Chỉnh sửa để bổ sung file hoặc chọn thay toàn bộ file. File không hợp lệ không để lại bài tập/file dở dang. Xem trực tiếp và tải từng file theo quyền khóa học.

## Bộ dữ liệu ngày 28/10/2026

Bộ dữ liệu ban đầu ngày 28/10 có hai học phần Lập trình mạng (`LTM-D24-01`) và Cấu trúc dữ liệu và Giải thuật (`CTDL-D24-01`). Mỗi khóa: 20 sinh viên, 16 buổi học, 4 thông báo, 12 bài tập với 24 file đề/hướng dẫn, 4 đề code (luyện tập, hai giữa kỳ, một cuối kỳ), 3 học liệu và lịch sử bài tập/điểm danh. Mỗi lịch khóa có 36 mục gồm lịch học, thông báo, đề thi và hạn bài tập. Hạn bài tập đặt 23:59; thi chính thức 08:00; lịch điểm danh khớp giờ buổi học. C/C++/Java và bộ testcase gốc đã được kiểm thử; không sinh verdict AC giả.

Tên, ngày sinh và lịch sử học tập do nhóm tự soạn, không phải hồ sơ của sinh viên thật. Thông tin này nằm trong tài liệu bàn giao, không chèn nhãn thử nghiệm vào màn học tập.

Giảng viên `GV001`, mật khẩu được tạo riêng trong `.runtime/accounts/LOGIN.txt`. Sinh viên `B24DCCN101`–`B24DCCN140`, ngày sinh và mật khẩu ban đầu ở `students.csv` cùng thư mục. Mật khẩu ban đầu DDMMYYYY, phải đổi lần đầu. Các tài khoản cũ đã bị loại khỏi DB đang chạy.

Dữ liệu cũ được sao lưu tại `.runtime/backups/before-activation-20261028`; bản file gốc nằm tại `.runtime/backups/reset-original-files-20261028`. Không đưa database, storage hoặc mật khẩu lên Git. Để dựng thêm bộ mới vào thư mục trống: `python -m scripts.build_fresh_classrooms --output .runtime/new-classrooms`. Lệnh này chỉ dựng riêng, không tự ghi đè DB đang chạy. Sao lưu và dừng web trước khi thay dữ liệu.

Migration `0009_lifecycle_attachments` thêm dấu xóa và bảng `assignment_attachments`; gói chuyển khóa bao gồm các bảng/cột mới và vẫn đọc gói phiên bản 1 cũ. Bộ tạo dữ liệu không thay tài khoản hay khóa sẵn có: đích phải là thư mục mới.


### Thay khóa mạng bằng lập trình nền tảng

Bản đang chạy đã thay `LTM-D24-01` bằng `LT-D24-01` (Lập trình C, C++ và Java), 20 tài khoản được dùng lại và giữ nguyên mật khẩu. Khóa CTDL và lớp C++ do giảng viên tạo được giữ nguyên, kể cả trạng thái đã tổng kết. Khóa mới có 6 bài tập, 12 buổi học, 4 thông báo, 4 đề code, 3 học liệu; điểm và lịch sử của khóa mạng không được chuyển sang. Bản sao lưu trước chuyển đổi: `.runtime/backups/before-programming-switch-20261028`. Khóa mạng được ẩn bằng soft-delete. Chỉ chạy `scripts.switch_programming_curriculum` sau khi dừng API/worker và sao lưu, theo mô tả trong file script.
