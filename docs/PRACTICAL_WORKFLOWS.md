# Các luồng học tập và kiểm tra

## Đăng nhập hai vai trò

Mở hai tab mới bằng cách nhập địa chỉ web, đăng nhập teacher ở tab thứ nhất và student ở tab thứ hai. Phiên được chọn bằng ID riêng trong sessionStorage, cookie xác thực HttpOnly riêng từng tab; REST, WebSocket và tải file cùng dùng phạm vi đó. Đăng xuất một tab chỉ thu hồi phiên của tab đó. Reload giữ phiên; đóng tab rồi mở mới cần đăng nhập lại. Sau nâng cấp này đăng nhập lại từng tab. Không dùng Duplicate tab để tạo một phiên độc lập vì trình duyệt có thể sao chép sessionStorage.

## Phòng thi

Bắt đầu làm bài chuyển tới `/student/exam?exam=ID`; không có menu khóa học hoặc điều hướng khác. Truy cập đường dẫn chức năng khác trong web khi còn phiên thi sẽ quay về phòng thi. Sinh viên có thể nộp sớm qua hộp thoại xác nhận; hết giờ máy chủ kết thúc phiên. Bài đã gửi chờ chấm vẫn được xử lý; sau khi xong điểm được cập nhật vào bảng điểm, trung bình các đề giữa kỳ và một đề cuối kỳ theo cấu hình. Website cảnh báo khi đóng trang/rời tab và ghi nhật ký; trình duyệt không thể khóa các ứng dụng hoặc tab bên ngoài như phần mềm kiosk.

Giảng viên tạo đề nháp, thêm câu hỏi, mở mục Quản lý test case ngay dưới từng câu. Có ba cách nhập: gõ input/output trực tiếp, tải từng cặp file, hoặc ZIP nhiều cặp `.in/.out`. Test không tự sinh từ tên/mô tả. Đủ số câu theo bảng quy đổi và tổng trọng số test đúng điểm tối đa mới mở được đề. Nút Xuất điểm thi CSV nằm ở Theo dõi phiên thi; điểm còn chờ chấm để trống.

## Lịch và điểm danh

Lịch tổng bao gồm các khóa tài khoản có quyền truy cập; lịch trong khóa chỉ thuộc khóa được chọn. Giảng viên chọn buổi học, tạo QR; hộp thoại hiện QR ở trên và danh sách chưa có mặt ở dưới. Sinh viên quét QR sẽ tự nhận buổi học; Có mặt/Đến muộn biến mất khỏi danh sách chờ. Có thể đánh dấu thủ công và sửa lại bằng mã sinh viên trong hộp thoại; kết thúc phiên bằng nút riêng. Đóng cửa sổ chỉ ẩn hộp thoại, không kết thúc phiên. Thời hạn QR vẫn áp dụng; mã cũ sau khi tạo lại không còn dùng được.

QR có nền trắng, khoảng trắng viền và kích thước lớn. Bộ đọc ảnh chuẩn hóa độ phân giải, thử các hướng và tăng tương phản; thông báo phân biệt không đọc được ảnh với mã hết hạn/không hợp lệ. HTTP LAN dùng camera chụp ảnh của thiết bị, HTTPS tin cậy hỗ trợ video liên tục. Vẫn cần kiểm tra camera thực tế Android/iPhone; không thể phục hồi QR bị che, mất góc hoặc nhòe nặng.

Chuyên cần mặc định 10, mỗi phiên đã đóng/hết hạn mà sinh viên không có Có mặt/Đến muộn trừ 1, tối thiểu 0. Các phiên đang mở chưa bị trừ. Tạo lại QR cùng buổi học giữ cùng phiên để không tính trùng.

## Bài tập và điểm

Teacher có Tổng số, Trong hạn, Quá hạn (chỉ theo hạn nộp), và Tiến độ. Bảng tiến độ có mã SV, họ tên, các điểm bài tập và trung bình tự tính. Sửa trực tiếp ô điểm, Enter hoặc chuyển ô để lưu; để trống bỏ điều chỉnh thủ công. Trung bình tính bài đã chấm và bài hết hạn, chưa nộp sau hạn tính 0; bài nộp chờ chấm khiến trung bình chưa đủ dữ liệu. Student chỉ xem điểm của mình, cập nhật qua WebSocket và tải lại định kỳ.

Bảng điểm khóa học sửa trực tiếp Chuyên cần/Bài tập/Giữa kỳ/Cuối kỳ không cần lý do; tổng tự tính theo trọng số. Điểm được hiển thị trực tiếp cho sinh viên, không phải chờ công bố. Điều chỉnh điểm thành phần được ưu tiên hơn kết quả tự động; xóa ô điều chỉnh để lấy lại điểm tự động.

CSV UTF-8 có `student_id` và ít nhất một trong `attendance_score,homework_score,midterm_score,final_score`. Dùng CSV xuất từ bảng làm mẫu. Ô trống giữ điểm hiện có; toàn bộ file được kiểm tra rồi ghi trong một transaction, lỗi bất kỳ không ghi dở. Điểm phải hữu hạn từ 0 đến 10, tối đa 2.000 sinh viên/file, không nhập điểm tổng. Tải CSV được cả khi còn thiếu điểm; giữ cột student_id dạng Text khi mở Excel.

Xem bài trực tiếp trong cửa sổ: PDF; TXT/mã nguồn; nội dung văn bản DOCX/PPTX; danh sách ZIP và file văn bản/mã nguồn bên trong (tối đa 2 MiB để xem). Không chạy source/HTML đã nộp; kiểm tra quyền trước khi đọc. DOC/PPT cũ cần lưu sang PDF hoặc DOCX/PPTX. Việc xem trên web vẫn truyền dữ liệu tới trình duyệt nhưng không bắt lưu file vào Downloads.

## Kiểm tra và chuyển máy

Migration `0008_assignment_grades` lưu điểm từng bài độc lập cả khi sinh viên chưa nộp file. Gói chuyển khóa bao gồm bảng này; gói phiên bản 1 cũ thiếu bảng được hiểu là chưa có điểm điều chỉnh. Sao lưu DB/storage trước nâng cấp. Kiểm thử API tại `tests/integration/test_practical_workflows.py`; kiểm thử ảnh QR và nộp sớm được thực hiện trên bản sao DB, không sửa phiên thi chính.
