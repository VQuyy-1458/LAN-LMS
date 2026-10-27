# Hai khóa học thực hành có dữ liệu đầy đủ

Toàn bộ tên, mã sinh viên, lớp, ngày sinh, bài nộp file, nhận xét và lịch sử điểm danh trong hai khóa `LTM-2026-01` và `CTDL-2026-01` là **giả lập**, không phải hồ sơ hay kết quả học tập thật. Lời giải chuẩn được chạy kiểm thử; không seed verdict AC hoặc số liệu chấm giả vào ứng dụng.

## Nội dung

Mỗi khóa có 20 sinh viên, chia 2 lớp thực hành; 3 học liệu (sổ tay PDF 6 chuyên đề, đề cương TXT, ZIP khung source C/C++/Java); 12 buổi học theo tuần, 4 thông báo và 4 lịch thi; 2 phiên điểm danh cũ đủ 20 trạng thái mẫu; 6 assignment có file đề tải được, 19 bài nộp file mẫu (12 đã chấm, 7 chờ chấm).

Mỗi khóa có 4 đề: luyện tập mở trong 30 ngày từ lúc tạo; giữa kỳ 1 sau 5 ngày; giữa kỳ 2 sau 15 ngày; cuối kỳ sau 25 ngày. Các đề chính thức kéo dài 90 phút. Có 24 câu trong các đề (20 bài gốc, 4 câu luyện tập dùng lại để làm quen) và 152 testcase. Student chỉ thấy câu khi đề mở; teacher xem/sửa trước giờ bắt đầu. Muốn đổi lịch, sửa trước khi mở hoặc tạo đề test mới.

Ngân hàng 20 bài gốc có 126 testcase gồm biên, số lớn, rỗng theo ràng buộc, giá trị trùng, không tới được và trường hợp hiệu năng. Bài A07 đọc `DATA.INP`, ghi `RESULT.OUT`; các bài còn lại dùng stdin/stdout. Mỗi bài hỗ trợ C17/C++17/Java17, ví dụ công khai và test ẩn. File `demo/classroom_problems.py` chứa dữ liệu tự soạn và lời giải C++; kiểm thử `test_classroom_bank.py` chạy Docker cho từng lời giải với toàn bộ test.

## Tạo dữ liệu trên máy đang chạy

Sau migration mới nhất, chạy ở gốc project:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_classroom --teacher TEN_DANG_NHAP_GIANG_VIEN
```

Script tự chọn DB/storage giống launcher (nếu có DB demo thì dùng DB demo). Có thể chỉ định `--database-url`, `--storage-root`, `--output` để dùng môi trường khác. Chỉ tạo khóa mới; không reset khóa, hồ sơ hoặc mật khẩu đang có. Chạy lại giữ nguyên dữ liệu đã học/nộp, không kéo dài lịch thi cũ. Xung đột mã lớp/tài khoản thuộc dữ liệu khác thì dừng để tránh ghi đè.

Thông tin cấp tài khoản nằm tại `.runtime/classroom-20261027/accounts.csv`. Mã đăng nhập là B26DCCN001–B26DCCN040. Mật khẩu ban đầu là ngày sinh viết liền DDMMYYYY (giữ số 0 đầu), bắt buộc đổi ở lần đăng nhập đầu. Ngày sinh hiển thị DD/MM/YYYY trong danh sách lớp của giảng viên. Chỉ giao dòng tương ứng cho từng sinh viên; không phát toàn bộ danh sách mật khẩu cho lớp, không commit file lên GitHub. Tài khoản teacher có sẵn được giữ nguyên.

`teacher-question-bank.zip` ở cùng thư mục chỉ dành cho giảng viên: statement, reference.cpp và tests.zip cho từng bài. **Không đưa ZIP này vào Tài liệu của sinh viên**, vì có đáp án và test ẩn. ZIP starter-code trong học liệu chỉ có khung mã, không có lời giải.

## Các luồng đã bổ sung

- Tổng quan trong khóa có số học liệu, bài chờ chấm/tiến độ nộp, số đề và hoạt động sắp tới; quyền lấy dữ liệu vẫn theo enrollment.
- Teacher tạo assignment rồi đính kèm/thay file đề (20 MiB); student có quyền trong khóa tải được file và nộp file/ZIP. File đề đi cùng gói chuyển khóa.
- Teacher nhập `tests.zip` cho câu chưa có test. Chứa cặp `01.in`/`01.out` ở gốc ZIP; `sample_01.in`/`.out` là ví dụ công khai. Tối đa 100 cặp, 1 MiB/file, 20 MiB nén/50 MiB tổng; chia đều trọng số theo điểm tối đa câu. Test hiện có không bị xóa hoặc ghi đè khi nhập.
- Student xem ví dụ công khai trong màn làm bài; test ẩn không được trả về. Teacher tải input/output để kiểm tra lại testcase.
- Điểm code vẫn theo số câu AC và ladder; trung bình giữa kỳ, một cuối kỳ, trọng số 10/10/10/70. Điểm và nhận xét assignment theo cơ chế công bố hiện có.

## Vận hành buổi học

Chạy `CHAY_LAN.cmd`, kiểm tra worker trong Thi lập trình; teacher chọn khóa và buổi học để mở QR. Student đăng nhập, đổi mật khẩu tạm, vào đúng khóa, đọc tài liệu/nộp bài. Trước buổi thi thật, tạo lịch đề phù hợp và thử nộp một bài qua máy sinh viên.

Khi WSL/Docker không phản hồi, bài nộp được lưu chờ xử lý; chưa được xem là một buổi thi đã nghiệm thu. CI Linux kiểm tra tính đúng của runner/ngân hàng, không thay thế việc chạy thử lâu trên máy chủ phòng thi và nhiều máy LAN vật lý. Bộ USB chỉ dùng trên máy đã chuẩn bị phần mềm nền.

## Tham khảo luồng sử dụng

Thiết kế giao bài/file đề và bài nộp tham khảo [Moodle Assignment](https://docs.moodle.org/503/en/Assignment_activity); cách chọn bài, ngôn ngữ, xem giới hạn và verdict tham khảo [DOMjudge Team Manual](https://www.domjudge.org/docs/manual/main/team.html). Không sao chép nội dung đề hoặc giao diện của các hệ thống này. Nội dung học liệu và dữ liệu mẫu do nhóm tự soạn cho LAN-LMS.

## Cập nhật lớp đã tạo trước đây

Sao lưu DB/storage trước, chạy migration mới nhất rồi `python -m scripts.refresh_classroom --rename-students`. Cờ này chỉ đổi 40 hồ sơ do bộ tạo lớp cũ sinh ra, giữ ID nội bộ, bài nộp và điểm; đặt mật khẩu theo ngày sinh, bắt đổi mật khẩu và thu hồi phiên đăng nhập cũ. Không đổi tài khoản giảng viên hoặc sinh viên ngoài hai lớp. Không dùng để reset mật khẩu thường xuyên.

Tổng quan chỉ hiển thị lịch và số liệu; truy cập khóa học từ thanh điều hướng. Sinh viên quét QR để tự nhận buổi học, không chọn buổi hoặc nhập mã thủ công. Giảng viên chọn buổi học để tạo QR; tạo lại mã cùng buổi giữ nguyên danh sách điểm danh. Trên HTTP điện thoại, nút camera mở chức năng chụp ảnh của thiết bị; camera liên tục cần HTTPS được thiết bị tin cậy.

Bộ lọc bài tập của sinh viên chia thành đã nộp, chưa nộp còn hạn, quá hạn chưa nộp. Giảng viên xem đã nộp đủ cả lớp, chưa đủ còn hạn, hoặc quá hạn chưa đủ. Số đếm bao gồm toàn bộ trang kết quả.
