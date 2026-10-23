# ĐẶC TẢ CHÍNH THỨC VÀ KẾ HOẠCH TRIỂN KHAI ĐỒ ÁN

## Thiết kế và xây dựng hệ thống LMS và thi lập trình trên mạng LAN theo mô hình Client–Server

**Phiên bản:** 1.1 — Khung triển khai thống nhất cho nhóm 4 thành viên; cập nhật 24/10/2026\
**Thời gian kế hoạch:** 22/10/2026 – 31/10/2026; các mốc 22–23/10 là mốc ban đầu, không phải xác nhận đã hoàn thành\
**Môi trường mục tiêu:** Windows, chạy trên một máy chủ trong mạng LAN\
**Mục tiêu:** Xây dựng sản phẩm có thể chạy thực tế, demo xuyên suốt, có mã nguồn và tài liệu bàn giao.

**Cách đọc:** Phần I–XIX giữ khung đặc tả gốc. Phần XX chốt chi tiết triển khai, phân công, thực nghiệm và nộp bài. Đây là thiết kế, không phải xác nhận tính năng đã hoàn thành. Hợp đồng endpoint tại [API 1.1](api-specification.md).

---

# PHẦN I. YÊU CẦU VÀ CÁC QUYẾT ĐỊNH ĐÃ CHỐT

## 1. Mục tiêu hệ thống

Xây dựng một hệ thống LMS (Learning Management System) phục vụ việc quản lý khóa học, sinh viên, tài liệu, điểm danh, bài tập, thi lập trình và điểm số.

Giảng viên và sinh viên sử dụng trình duyệt trên máy tính trong cùng mạng LAN. Một máy tính đóng vai trò máy chủ, chạy frontend, backend, database, kho file và hệ thống chấm bài.

Hệ thống cần đáp ứng các mục tiêu:

1. Quản lý tài khoản giảng viên và sinh viên.
2. Cho phép giảng viên tạo khóa học, import danh sách sinh viên từ CSV và tự động tạo tài khoản.
3. Quản lý tài liệu, lịch học, sự kiện, điểm danh QR và thông báo.
4. Cho phép sinh viên nộp bài tập bằng file hoặc ZIP.
5. Cho phép sinh viên thi lập trình C/C++ và Java.
6. Hỗ trợ cả input/output chuẩn và bài sử dụng file input/output.
7. Có hệ thống chấm bài tự động, giới hạn thời gian và bộ nhớ.
8. Có theo dõi phiên thi và lịch sử nộp bài.
9. Có bảng điểm, trọng số có thể cấu hình và chức năng xuất CSV.
10. Có hướng dẫn cài đặt, chạy LAN, backup, restore và chuyển sang máy tính khác.

## 2. Công nghệ thống nhất

| Thành phần              | Quyết định                                                                    |
| ----------------------- | ----------------------------------------------------------------------------- |
| Frontend                | Next.js + TypeScript                                                          |
| Giao diện               | Tailwind CSS, font Inter hoặc Roboto                                          |
| Backend                 | Python + FastAPI                                                              |
| Giao tiếp nghiệp vụ     | HTTP REST API                                                                 |
| Cập nhật thời gian thực | WebSocket                                                                     |
| Database bản đầu        | SQLite                                                                        |
| ORM và migration        | SQLAlchemy + Alembic                                                          |
| Xác thực                | Session phía server, cookie HttpOnly; mật khẩu hash bằng Argon2id                                |
| File storage            | Lưu file trên ổ đĩa máy chủ, database chỉ lưu metadata và đường dẫn nội bộ    |
| Chấm code               | Judge Worker riêng, không chạy code trong tiến trình API                      |
| Ngôn ngữ chấm           | C/C++ và Java                                                                 |
| Môi trường chạy         | Windows host; Judge chạy trong Docker Linux qua WSL2, phải kiểm thử trước demo |
| Quản lý mã nguồn        | Git                                                                           |
| Tài liệu                | Markdown, README.md và báo cáo trong `REPORT/`                                |

### 2.1. Vì sao chọn REST API kết hợp WebSocket?

REST API dễ thiết kế, kiểm thử và phù hợp với các chức năng như đăng nhập, quản lý khóa học, upload tài liệu, import CSV, nộp bài và xuất điểm.

WebSocket được dùng cho những chức năng cần cập nhật thường xuyên:

- Trạng thái phiên thi.
- Trạng thái kết nối của sinh viên.
- Thông báo bài nộp đang chờ chấm, đang chấm hoặc đã có kết quả.
- Thông báo thời gian còn lại hoặc sự kiện kỳ thi khi cần.

WebSocket chỉ là kênh giao tiếp; mọi quyền hạn, thời hạn thi và kết quả chấm vẫn phải được kiểm tra ở backend.

**Đối chiếu môn học:** Instruction.md cho phép HTTP/REST; Topics.md mục 4.5–4.6 phù hợp với bộ chấm và hệ thống thi. Chọn REST + WebSocket, không bổ sung TCP service chỉ để đáp ứng một yêu cầu không có trong các file đã cung cấp. Nhóm vẫn phải giải thích message flow, connection, concurrency và xử lý lỗi.

### 2.2. Vì sao chọn SQLite?

SQLite phù hợp cho bản demo chạy trên một máy chủ, dễ backup và dễ chuyển bằng USB. Nhóm cần dùng transaction, khóa duy nhất và kiểm thử các thao tác đồng thời.

Nếu hệ thống phải phục vụ nhiều người dùng đồng thời ở quy mô lớn hơn, nhóm có thể chuyển sang PostgreSQL. Trong thời gian đồ án ngắn, không nên tự làm phức tạp triển khai nếu SQLite đáp ứng yêu cầu.

### 2.3. Quy tắc phạm vi cho phần thi lập trình

Phiên bản đầu tiên bắt buộc hỗ trợ:

- C/C++ và Java.
- Bài đọc từ standard input và ghi ra standard output.
- Bài đọc input từ file và ghi output ra file theo tên file do giảng viên cấu hình.
- Nhiều test case, test ẩn, chấm điểm từng test.
- Giới hạn thời gian và bộ nhớ.
- Các trạng thái biên dịch và chấm bài.
- Lưu lịch sử nộp bài.

**Bài nhiều file hoặc cả project:** không triển khai một hệ thống build project tổng quát ngay từ đầu. Chỉ mở rộng sang nhiều file nếu yêu cầu môn học hoặc đề bài mẫu thực sự cần. Khi làm, phải quy định cấu trúc thư mục, file entry point, cách biên dịch và cách đóng gói rõ ràng.

---

# PHẦN II. KIẾN TRÚC HỆ THỐNG

## 3. Sơ đồ tổng thể

```
+---------------------------------------------------+
|             Máy sinh viên / giảng viên            |
|                    Trình duyệt                    |
+---------------------------+-----------------------+
                            |
                        Mạng LAN
                            |
+---------------------------v-----------------------+
|                    Máy chủ Windows                |
|                                                   |
|  +------------------+    +---------------------+  |
|  | Next.js Frontend |    | FastAPI Backend     |  |
|  | Port 3000        |    | Port 8000           |  |
|  +------------------+    +----------+----------+  |
|                                     |             |
|                      +--------------+----------+  |
|                      |              |          |  |
|                 +----v----+   +-----v-----+    |  |
|                 | SQLite  |   | File      |    |  |
|                 | DB      |   | Storage   |    |  |
|                 +---------+   +-----------+    |  |
|                                                |  |
|                          +---------------------v+ |
|                          | Judge Queue / Worker | |
|                          +----------+-----------+ |
|                                     |             |
|                          +----------v-----------+ |
|                          | Isolated Execution   | |
|                          | C/C++ / Java         | |
|                          +----------------------+ |
+---------------------------------------------------+
```

## 4. Trách nhiệm từng thành phần

### Frontend

- Hiển thị giao diện giảng viên và sinh viên.
- Gửi yêu cầu đến API.
- Kiểm tra dữ liệu đầu vào cơ bản để cải thiện trải nghiệm.
- Nhận trạng thái bài nộp và phiên thi qua WebSocket.
- Không tự quyết định người dùng có quyền làm một hành động nhạy cảm hay không.

### Backend

- Xác thực và phân quyền.
- Xử lý nghiệp vụ khóa học, sinh viên, import CSV, tài liệu, điểm danh, bài tập và bảng điểm.
- Kiểm tra thời hạn kỳ thi và quyền nộp bài.
- Lưu dữ liệu và quản lý đường dẫn file.
- Tạo job chấm bài và nhận kết quả từ Judge Worker.
- Phát thông báo qua WebSocket.
- Ghi nhật ký các hành động quan trọng.

### Database

Lưu dữ liệu có cấu trúc như tài khoản, khóa học, đăng ký học, bài tập, phiên thi, submission, điểm danh và điểm số.

### File Storage

Lưu file tài liệu, file bài tập sinh viên nộp, source code và file cần thiết cho bài thi. Không cho phép người dùng tự gửi đường dẫn ổ đĩa để backend tùy ý đọc file.

### Judge Worker

- Nhận job chấm bài.
- Biên dịch code.
- Chạy chương trình trong môi trường cô lập.
- Thực thi test case.
- So sánh kết quả.
- Trả trạng thái và điểm cho backend.

Judge Worker không được phép nhận lệnh tùy ý từ trình duyệt.

---

# PHẦN III. VAI TRÒ VÀ CHỨC NĂNG

## 5. Vai trò người dùng

### 5.1. Visitor

- Truy cập trang giới thiệu.
- Đăng nhập.
- Không xem được nội dung khóa học riêng tư.

### 5.2. Student

- Đăng nhập bằng mã sinh viên và mật khẩu.
- Đổi mật khẩu ban đầu.
- Xem các khóa học đã đăng ký.
- Xem tài liệu và lịch.
- Điểm danh khi có phiên hợp lệ.
- Nộp bài tập file.
- Thi lập trình.
- Xem trạng thái chấm bài và lịch sử nộp bài.
- Xem điểm được công bố.

### 5.3. Teacher

- Tạo và quản lý khóa học.
- Import danh sách sinh viên.
- Quản lý tài liệu và lịch học.
- Tạo phiên điểm danh QR.
- Tạo bài tập và kỳ thi.
- Quản lý bài nộp và điểm.
- Cấu hình trọng số điểm.
- Theo dõi trạng thái phiên thi.
- Xuất bảng điểm CSV.

### 5.4. Judge Worker

Là thành phần nội bộ, không đăng nhập như người dùng thông thường. Chỉ nhận công việc theo cơ chế được backend cho phép.

---

## 6. Chức năng giảng viên

### 6.1. Dashboard

Hiển thị:

- Danh sách khóa học.
- Số lượng sinh viên.
- Lịch học và lịch thi.
- Bài tập sắp đến hạn.
- Tình trạng nộp bài.
- Điểm danh gần đây.
- Kết quả thi cần xem xét.

### 6.2. Quản lý khóa học

Giảng viên có thể:

- Tạo, sửa và xem chi tiết khóa học.
- Đặt mã khóa học, tên, mô tả và thời gian.
- Quản lý danh sách sinh viên.
- Đăng tài liệu riêng cho từng khóa.
- Tạo lịch học, sự kiện và thông báo.
- Tạo bài tập file.
- Tạo kỳ thi lập trình.
- Xem bảng điểm.

Trong phiên bản đầu tiên, không cần chức năng đóng gói cả khóa học thành ZIP. Giảng viên import danh sách bằng CSV và upload tài liệu riêng.

### 6.3. Quản lý tài liệu

Hỗ trợ những định dạng cần thiết như PDF, DOCX, PPTX, ZIP và các file bài học khác theo danh sách cho phép.

Yêu cầu:

- Kiểm tra loại file và dung lượng.
- Tên file hiển thị không được dùng làm đường dẫn lưu file trực tiếp.
- Tài liệu phải gắn với khóa học.
- Sinh viên chỉ được tải tài liệu nếu có quyền.
- Không lưu file upload vào thư mục mã nguồn hoặc thư mục public tùy tiện.

### 6.4. Quản lý lịch

Giảng viên có thể tạo sự kiện gồm:

- Tên sự kiện.
- Mô tả.
- Thời gian bắt đầu và kết thúc.
- Khóa học liên quan.
- Loại sự kiện: học, thi, hạn nộp hoặc thông báo.

Sinh viên nhìn thấy lịch của khóa học mình tham gia.

---

# PHẦN IV. IMPORT CSV VÀ TỰ ĐỘNG TẠO TÀI KHOẢN

## 7. Yêu cầu bắt buộc

Đây là một trong những chức năng quan trọng nhất, phải triển khai xuyên suốt frontend, backend và database.

Giảng viên mở một khóa học, chọn import CSV và tải danh sách sinh viên. Hệ thống kiểm tra dữ liệu, tạo tài khoản cho sinh viên chưa có tài khoản và đăng ký họ vào khóa học đó.

## 8. Định dạng CSV thống nhất

Tên file ví dụ: `students.csv`.

```
student_id,full_name,date_of_birth,class_name,email
SV001,Nguyen Van An,15032005,D23CNPM01,an@example.com
SV002,Tran Thi Binh,02112005,D23CNPM01,binh@example.com
SV003,Le Van Cuong,09072004,D23CNPM02,cuong@example.com
```

Quy ước:

| Cột             | Bắt buộc | Quy tắc                |
| --------------- | -------- | ---------------------- |
| `student_id`    | Có       | Mã sinh viên, duy nhất |
| `full_name`     | Có       | Họ và tên              |
| `date_of_birth` | Có       | Định dạng `DDMMYYYY`   |
| `class_name`    | Có       | Mã lớp                 |
| `email`         | Không    | Có thể để trống        |

Ngày sinh phải được đọc dưới dạng chuỗi. Ví dụ `02112005` phải giữ nguyên số 0 ở đầu. Không nên đọc cột này thành số nguyên rồi chuyển ngược lại.

CSV cần hỗ trợ UTF-8 và báo lỗi rõ ràng khi thiếu cột hoặc có định dạng không hợp lệ.

## 9. Quy tắc tạo tài khoản

- Username là mã sinh viên.
- Mật khẩu ban đầu là ngày sinh dạng `DDMMYYYY`.
- Ví dụ: `SV002` có ngày sinh `02/11/2005` sẽ có username `SV002` và mật khẩu ban đầu `02112005`.
- Role được gán là `student`.
- Tài khoản mới phải bật trạng thái `must_change_password`.
- Sinh viên phải đổi mật khẩu sau lần đăng nhập đầu tiên trước khi dùng các chức năng học tập.
- Không lưu mật khẩu dạng văn bản thuần.
- Nếu tài khoản đã tồn tại, không tạo tài khoản trùng và không tự ghi đè mật khẩu.
- Nếu sinh viên chưa đăng ký khóa học hiện tại, hệ thống thêm đăng ký học.
- Nếu sinh viên đã đăng ký, không tạo bản ghi đăng ký trùng.
- Nếu tên hoặc lớp trong CSV khác dữ liệu đang có, báo cho giảng viên xem xét; không âm thầm thay đổi dữ liệu cá nhân.
- Không tự đặt mật khẩu ngày sinh mới cho tài khoản đã tồn tại.

## 10. Quy trình import

1. Giảng viên chọn khóa học.
2. Chọn `Sinh viên → Import CSV`.
3. Chọn file CSV.
4. Backend đọc file và kiểm tra cấu trúc.
5. Giao diện hiển thị bản xem trước.
6. Hiển thị lỗi theo số dòng, ví dụ: thiếu mã sinh viên, ngày sinh không hợp lệ hoặc mã trùng.
7. Giảng viên xác nhận import.
8. Backend thực hiện các thao tác trong transaction phù hợp.
9. Tạo tài khoản mới và hồ sơ sinh viên khi cần.
10. Tạo quan hệ đăng ký khóa học.
11. Hiển thị báo cáo kết quả.

Kết quả import phải có:

- Tổng số dòng.
- Số dòng hợp lệ.
- Số tài khoản mới tạo.
- Số tài khoản đã tồn tại.
- Số sinh viên mới được thêm vào khóa học.
- Số sinh viên đã đăng ký từ trước.
- Số dòng thất bại và lý do.

Nên có nút tải báo cáo lỗi CSV. Báo cáo không được chứa mật khẩu.

### 10.1. Quy tắc xử lý lỗi

- Phát hiện mã sinh viên trùng ngay trong file.
- Không tạo hai tài khoản cho cùng một mã sinh viên.
- Không cho dòng sai định dạng âm thầm bỏ qua mà không báo.
- Giới hạn kích thước file và số dòng hợp lý.
- Chỉ giảng viên có quyền quản lý khóa học mới được import.
- Bắt buộc preview rồi confirm; có bất kỳ dòng lỗi hoặc dữ liệu hồ sơ xung đột thì từ chối toàn bộ lượt import. Giảng viên sửa file rồi preview lại.
- Không tạo tài khoản một nửa hoặc đăng ký khóa học một nửa khi xảy ra lỗi không thể khắc phục.

### 10.2. Đổi mật khẩu

Màn hình đổi mật khẩu yêu cầu:

- Mật khẩu hiện tại, nếu phù hợp với luồng xác thực.
- Mật khẩu mới.
- Xác nhận mật khẩu mới.

Mật khẩu mới phải đáp ứng chính sách tối thiểu đã thống nhất, tối thiểu 8 ký tự, tối đa 128 ký tự và khác mật khẩu hiện tại. Sau khi đổi thành công, backend cập nhật `must_change_password = false`.

Ngày sinh là thông tin dễ đoán, vì vậy quy tắc này chỉ dùng cho mật khẩu ban đầu theo yêu cầu đồ án. Không xuất mật khẩu ban đầu ra file và không ghi vào log.

---

# PHẦN V. CHỨC NĂNG SINH VIÊN

## 11. Dashboard sinh viên

Hiển thị:

- Các khóa học đang tham gia.
- Tài liệu mới.
- Bài tập chưa nộp.
- Hạn nộp gần nhất.
- Kỳ thi sắp diễn ra.
- Điểm số đã công bố.
- Thông báo và lịch.

## 12. Trang chi tiết khóa học

Các mục:

1. Tổng quan.
2. Tài liệu.
3. Lịch học và sự kiện.
4. Điểm danh.
5. Bài tập.
6. Thi lập trình.
7. Bảng điểm.

Danh sách sinh viên chỉ hiển thị theo chính sách quyền riêng tư của hệ thống; không mặc định công khai mọi thông tin cá nhân.

## 13. Nộp bài tập file

Sinh viên có thể:

- Xem đề bài.
- Xem thời hạn.
- Upload file hoặc ZIP.
- Xem thời điểm nộp.
- Xem trạng thái nộp.
- Nộp lại nếu giảng viên cho phép.

Backend phải kiểm tra hạn nộp, dung lượng, định dạng file và quyền truy cập. Nếu có giải nén ZIP, cần giới hạn kích thước giải nén, số lượng file và ngăn đường dẫn thoát khỏi thư mục đích.

## 14. Thi lập trình

Sinh viên có thể:

- Mở kỳ thi đang diễn ra.
- Xem đề bài và giới hạn.
- Chọn ngôn ngữ C/C++ hoặc Java.
- Viết hoặc dán code.
- Chọn gửi bài.
- Xem trạng thái biên dịch và chấm.
- Xem điểm được phép công bố.
- Xem lịch sử các lần gửi bài.

Sinh viên không được xem test ẩn, output mong đợi của test ẩn hoặc source code của sinh viên khác.

---

# PHẦN VI. HỆ THỐNG CHẤM CODE

## 15. Các loại bài lập trình

### Loại A — Standard Input/Output

- Chương trình đọc từ stdin.
- Chương trình ghi ra stdout.
- Backend cung cấp input của từng test.
- Judge thu output và so sánh với đáp án.

Đây là chế độ ưu tiên đầu tiên vì dễ triển khai và kiểm thử.

### Loại B — File Input/Output

Giảng viên cấu hình:

- `input_mode = file`
- Tên file input.
- Tên file output.
- Các test case tương ứng.

Ví dụ một bài yêu cầu đọc `input.txt` và ghi `output.txt`. Judge tạo file input đúng tên trong thư mục làm việc riêng, chạy chương trình, sau đó thu file output để so sánh.

Tên file không được tự suy đoán. Nếu chương trình không tạo file output theo yêu cầu, xử lý theo quy tắc đã định và trả kết quả phù hợp.

### Loại C — Bài nhiều file hoặc project

Đây là phần mở rộng, không phải điều kiện để hoàn thành phiên bản đầu tiên, trừ khi đề bài bắt buộc.

Nếu triển khai, cần xác định:

- Định dạng gói nộp.
- Cấu trúc thư mục được phép.
- File entry point.
- Quy tắc biên dịch C/C++ hoặc Java.
- Danh sách file được chấp nhận.
- Cách giới hạn dung lượng và kiểm tra ZIP.

Không cho phép người dùng gửi tùy ý lệnh shell hoặc tham số biên dịch không kiểm soát.

## 16. Trạng thái chấm bài

Sử dụng các trạng thái thống nhất:

- `Pending`
- `Compiling`
- `Running`
- `Accepted`
- `Wrong Answer`
- `Compile Error`
- `Time Limit Exceeded`
- `Memory Limit Exceeded`
- `Runtime Error`
- `System Error`

Frontend và backend phải dùng cùng các giá trị trạng thái. Có thể hiển thị bản dịch tiếng Việt trên giao diện.

## 17. Luồng chấm bài

1. Sinh viên gửi source code.
2. Backend kiểm tra tài khoản, quyền, thời hạn thi và ngôn ngữ.
3. Backend lưu submission.
4. Tạo job chấm.
5. Judge Worker nhận job.
6. Tạo thư mục làm việc riêng.
7. Biên dịch code.
8. Nếu biên dịch thất bại, lưu `Compile Error`.
9. Nếu biên dịch thành công, chạy từng test trong môi trường cô lập.
10. Kiểm tra giới hạn thời gian và bộ nhớ.
11. Thu output hoặc file output.
12. So sánh với đáp án.
13. Tính điểm theo điểm từng test.
14. Lưu kết quả.
15. Backend thông báo kết quả cho frontend qua WebSocket hoặc API truy vấn.

## 18. Cấu hình bài lập trình

Mỗi bài nên có:

- Tên bài.
- Đề bài.
- Ngôn ngữ cho phép.
- Thời gian giới hạn.
- Bộ nhớ giới hạn.
- Chế độ input/output.
- Tên file input/output nếu là file mode.
- Tổng điểm.
- Bộ test.
- Điểm từng test.
- Chính sách công khai test.
- Chính sách công khai output và thông báo lỗi.

### 18.1. Cách tính điểm bài

Điểm bài bằng tổng điểm các test đạt, theo cấu hình của giảng viên.

Ví dụ minh họa: bài 100 điểm có 10 test, mỗi test 10 điểm. Nếu đạt 7 test thì được 70 điểm.

Nếu có test trọng số khác nhau, phải lưu điểm test rõ ràng và tổng điểm không vượt quá điểm tối đa của bài.

### 18.2. So sánh output

Hỗ trợ tối thiểu:

- Exact match.
- Chuẩn hóa khoảng trắng đầu/cuối và xuống dòng theo quy tắc được công bố.

Không tự động bỏ tất cả khoảng trắng vì có thể làm thay đổi ý nghĩa output.

Có thể bổ sung so sánh số thực với sai số nếu bài yêu cầu.

## 19. Bảo mật Judge Worker

Đây là yêu cầu bắt buộc, không phải tính năng tùy chọn.

- Không chạy code sinh viên trong tiến trình FastAPI.
- Không chạy với quyền Administrator/root.
- Mỗi submission có thư mục riêng.
- Có giới hạn thời gian, CPU, bộ nhớ và dung lượng file.
- Tắt mạng đối với container biên dịch/chạy code sinh viên.
- Hạn chế quyền đọc/ghi file.
- Không gắn thư mục chứa secret, database hoặc dữ liệu nhạy cảm vào sandbox.
- Không cho chương trình tự do truy cập thư mục của người dùng khác.
- Dọn file tạm sau khi chấm.
- Giới hạn kích thước source và file upload.
- Không hiển thị test ẩn cho sinh viên.
- Ghi log lỗi hệ thống nhưng không ghi secret hoặc mật khẩu.

### 19.1. Windows và sandbox

Windows là môi trường phát triển và demo mục tiêu. Nhóm cần thử môi trường thực thi sớm.

Chọn Docker Linux trên WSL2 để biên dịch và chạy chương trình theo mục 60.3; việc chạy trong container không tự động đảm bảo an toàn. Cần kiểm tra cấu hình quyền, giới hạn tài nguyên, network isolation, volume mounts và quyền truy cập của worker.

Nếu không xây dựng được môi trường cách ly đủ tin cậy trong thời gian đồ án, không được mô tả hệ thống là an toàn tuyệt đối. Phải nêu rõ giới hạn trong báo cáo và chỉ chạy code thử nghiệm trong môi trường demo được kiểm soát.

---

# PHẦN VII. THEO DÕI PHIÊN THI VÀ WEBSOCKET

## 20. Mục tiêu theo dõi phiên thi

Giảng viên cần theo dõi được:

- Sinh viên nào đã bắt đầu phiên thi.
- Thời điểm bắt đầu và thời điểm kết thúc.
- Trạng thái đang thi, đã nộp bài hoặc đã kết thúc.
- Lần gửi bài và thời điểm gửi.
- Trạng thái chấm.
- Trạng thái kết nối WebSocket nếu cần.
- IP quan sát được từ kết nối máy chủ, kèm thời điểm ghi nhận.

Không coi IP là bằng chứng duy nhất để xác định sinh viên hoặc kết luận gian lận. Nhiều máy có thể dùng chung IP thông qua NAT, và IP có thể thay đổi.

Phiên bản đầu tiên không triển khai giám sát màn hình, webcam hoặc ghi phím. Nếu muốn bổ sung các tính năng này, cần có yêu cầu, thông báo và cơ chế bảo vệ riêng.

## 21. Dữ liệu phiên thi

Mỗi phiên thi có thể lưu:

- `exam_session_id`
- `student_id`
- `exam_id`
- `started_at`
- `ends_at`
- `submitted_at` nếu có
- `status`
- `last_seen_at`
- `last_observed_ip` nếu cần
- `connection_status` hoặc sự kiện kết nối

Lịch sử submission phải là dữ liệu riêng, liên kết với phiên thi. Không ghi đè bài nộp cũ khi sinh viên gửi lại.

## 22. Cách dùng WebSocket

WebSocket được dùng để:

- Thông báo kỳ thi đã mở hoặc đã đóng.
- Cập nhật trạng thái phiên.
- Báo submission đang chấm hoặc đã có kết quả.
- Cập nhật danh sách trạng thái kết nối khi cần.

Backend phải xác thực khi mở kết nối và kiểm tra quyền của người dùng. Mỗi thông báo chỉ gửi đến đúng người dùng hoặc giảng viên được phép xem.

Nếu WebSocket bị ngắt, frontend tự chuyển sang truy vấn REST API để lấy trạng thái mới nhất. Việc mất kết nối không được làm mất bài nộp đã lưu.

Thời gian kết thúc kỳ thi phải được kiểm tra bằng đồng hồ phía server, không tin đồng hồ trình duyệt.

---

# PHẦN VIII. ĐIỂM DANH VÀ BẢNG ĐIỂM

## 23. Điểm danh QR

Luồng hoạt động:

1. Giảng viên chọn khóa học.
2. Tạo phiên điểm danh.
3. Backend tạo token phiên ngẫu nhiên có thời hạn.
4. Frontend hiển thị QR.
5. Sinh viên đăng nhập và quét QR hoặc nhập mã phiên.
6. Backend kiểm tra quyền đăng ký khóa học và thời hạn phiên.
7. Backend lưu thời điểm điểm danh.
8. Giảng viên xem danh sách có mặt.

Quy tắc:

- QR không chứa mật khẩu hoặc thông tin xác thực.
- QR phải hết hạn theo cấu hình.
- Sinh viên không được điểm danh khóa học khác.
- Chặn điểm danh trùng nếu chính sách không cho phép.
- Giảng viên có thể đóng phiên điểm danh.
- Có thể cho giảng viên chỉnh sửa trạng thái có lý do và lưu nhật ký.

QR không chứng minh tuyệt đối sinh viên có mặt tại lớp; đây là giới hạn cần ghi rõ.

## 24. Bảng điểm

Các thành phần mặc định:

- Chuyên cần.
- Bài tập.
- Giữa kỳ.
- Cuối kỳ.

Cho phép giảng viên chỉnh sửa trọng số, thang điểm và cách tính. Tổng trọng số cần bằng 100% trước khi công bố điểm tổng kết.

### 24.1. Trọng số mặc định của hệ thống

Nhóm thống nhất dùng bộ mặc định để demo:

| Thành phần | Trọng số mặc định |
| ---------- | ----------------- |
| Chuyên cần | 10%               |
| Bài tập    | 20%               |
| Giữa kỳ    | 30%               |
| Cuối kỳ    | 40%               |
| Tổng       | 100%              |

Đây là cấu hình mặc định dự kiến của phần mềm, không phải quy định chính thức của môn học. Giảng viên có thể thay đổi trước khi tính điểm.

### 24.2. Công thức

Nếu các thành phần cùng thang điểm 10:

`Điểm tổng kết = Chuyên cần × 0,10 + Bài tập × 0,20 + Giữa kỳ × 0,30 + Cuối kỳ × 0,40`

Backend phải tính điểm. Frontend chỉ hiển thị kết quả.

Cần thống nhất cách xử lý điểm chưa có. Không tự coi điểm trống là 0 nếu bài chưa diễn ra hoặc giảng viên chưa nhập điểm. Nên phân biệt `chưa có điểm` với `điểm bằng 0`.

### 24.3. Xuất CSV

Các cột đề xuất:

```
student_id,full_name,class_name,attendance_score,homework_score,midterm_score,final_score,total_score
SV001,Nguyen Van An,D23CNPM01,10,8.5,7.5,9,8.55
```

Yêu cầu:

- Xuất theo khóa học được chọn.
- Mã sinh viên không bị biến đổi.
- Dữ liệu UTF-8.
- Có header.
- Điểm được định dạng thống nhất.
- Không xuất mật khẩu, token hoặc dữ liệu nhạy cảm không cần thiết.

---

# PHẦN IX. DATABASE VÀ API

## 25. Database schema đề xuất

| Bảng                     | Mục đích                                             |
| ------------------------ | ---------------------------------------------------- |
| `users`                  | Tài khoản, username, password hash, role, trạng thái |
| `students`               | Hồ sơ sinh viên và mã sinh viên                      |
| `teachers`               | Hồ sơ giảng viên                                     |
| `classes`                | Lớp học                                              |
| `courses`                | Khóa học                                             |
| `course_enrollments`     | Quan hệ sinh viên–khóa học                           |
| `course_materials`       | Metadata tài liệu                                    |
| `calendar_events`        | Lịch và sự kiện                                      |
| `attendance_sessions`    | Phiên điểm danh                                      |
| `attendance_records`     | Kết quả điểm danh                                    |
| `assignments`            | Bài tập file                                         |
| `assignment_submissions` | File bài tập đã nộp                                  |
| `coding_exams`           | Kỳ thi lập trình                                     |
| `exam_sessions`          | Phiên thi của sinh viên                              |
| `problems`               | Bài lập trình                                        |
| `test_cases`             | Test case                                            |
| `code_submissions`       | Các lần gửi code                                     |
| `judge_results`          | Kết quả chấm                                         |
| `grade_components`       | Cấu hình trọng số                                    |
| `grades`                 | Điểm theo thành phần                                 |
| `audit_logs`             | Nhật ký hành động quan trọng                         |

### 25.1. Ràng buộc bắt buộc

- Username duy nhất.
- Mã sinh viên duy nhất.
- Mỗi sinh viên chỉ có một quan hệ đăng ký cho cùng khóa học.
- Mỗi submission liên kết đúng với người dùng và bài.
- Điểm nằm trong phạm vi hợp lệ.
- Mỗi bài lập trình có cấu hình input/output rõ ràng.
- Mỗi phiên thi có thời điểm bắt đầu và kết thúc hợp lệ.
- Không lưu mật khẩu dạng văn bản thuần.
- Database dùng migration thay vì mỗi thành viên tự sửa schema theo cách riêng.

### 25.2. Quy tắc hồ sơ sinh viên

Tài khoản và hồ sơ sinh viên là hai khái niệm riêng. Khi import lại CSV, phải tái sử dụng tài khoản đã tồn tại theo mã sinh viên; không tạo một tài khoản mới.

Nếu dữ liệu CSV có khác biệt so với dữ liệu cũ, hệ thống báo để giảng viên kiểm tra. Không tự động ghi đè mật khẩu hoặc dữ liệu nhạy cảm.

## 26. API contract

Hợp đồng phiên bản 1.1 được quy định tại [api-specification.md](api-specification.md). Tài liệu đó xác định endpoint, xác thực, quyền, request/response, WebSocket và tính lặp an toàn. Frontend và backend thực hiện theo cùng hợp đồng; mọi thay đổi phải cập nhật tài liệu trước khi tích hợp.

---

# PHẦN X. CẤU TRÚC REPOSITORY

## 27. Cấu trúc thư mục thống nhất

```
LAN-LMS/
├── client/
│   ├── src/app/
│   │   ├── (public)/login/
│   │   ├── student/dashboard/
│   │   ├── student/courses/
│   │   ├── student/exams/
│   │   ├── student/grades/
│   │   ├── teacher/dashboard/
│   │   ├── teacher/courses/
│   │   ├── teacher/students/
│   │   ├── teacher/attendance/
│   │   ├── teacher/exams/
│   │   └── teacher/gradebook/
│   ├── src/components/
│   ├── src/features/
│   ├── src/lib/
│   ├── src/types/
│   ├── package.json
│   └── .env.example
│
├── server/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── modules/
│   │       ├── auth/
│   │       ├── students/
│   │       ├── courses/
│   │       ├── materials/
│   │       ├── attendance/
│   │       ├── assignments/
│   │       ├── coding_exams/
│   │       ├── submissions/
│   │       └── gradebook/
│   ├── requirements.txt
│   └── .env.example
│
├── judge/
│   ├── worker.py
│   ├── job_queue.py
│   ├── runners/
│   ├── comparators/
│   ├── languages/
│   └── limits.py
│
├── storage/
│   ├── course_materials/
│   ├── submissions/
│   └── temporary/
│
├── database/
│   ├── migrations/
│   └── seed/
│
├── scripts/
│   ├── setup_windows.ps1
│   ├── start_server.ps1
│   ├── start_client.ps1
│   ├── backup_database.py
│   └── export_data.py
│
├── docs/
│   ├── architecture.md
│   ├── database-design.md
│   ├── api-specification.md
│   ├── csv-import.md
│   ├── coding-judge.md
│   ├── lan-deployment.md
│   ├── testing.md
│   ├── decisions.md
│   └── AI_HANDOFF.md
│
├── tests/
├── REPORT/
├── docker-compose.yml
├── .gitignore
└── README.md
```

Có thể tinh giản cấu trúc trong giai đoạn đầu, nhưng không được gom toàn bộ logic vào một file lớn. Frontend, backend và judge cần có ranh giới rõ ràng.

---

# PHẦN XI. PHÂN CÔNG 4 THÀNH VIÊN

## 28. Thành viên 1 — Backend nền tảng và tích hợp

### Trách nhiệm

- Dựng FastAPI.
- Cấu hình database connection và migration cùng thành viên 3.
- Xây dựng đăng nhập, đăng xuất và phân quyền.
- API lấy thông tin tài khoản.
- Chuẩn API và hạ tầng dùng chung; thành viên 3 sở hữu API khóa học.
- Hỗ trợ phân quyền và transaction cho CSV; thành viên 3 sở hữu API và nghiệp vụ CSV.
- Kiểm tra quyền giảng viên/sinh viên.
- Cấu hình WebSocket.
- Tích hợp API giữa các module.
- Xử lý lỗi và chuẩn hóa response.

### Đầu ra

- Backend chạy được.
- API auth hoạt động.
- Phân quyền có test.
- API contract được ghi tài liệu.
- Luồng import CSV tích hợp được.

## 29. Thành viên 2 — Frontend và giao diện

### Trách nhiệm

- Dựng Next.js, TypeScript, Tailwind.
- Tạo layout, sidebar và component chung.
- Trang login.
- Dashboard giảng viên và sinh viên.
- Trang khóa học.
- Giao diện import CSV: chọn file, preview, lỗi và kết quả.
- Giao diện tài liệu, lịch, điểm danh.
- Giao diện bài tập và thi lập trình.
- Giao diện trạng thái chấm.
- Bảng điểm và export.
- Tích hợp REST API và WebSocket; kiểm thử nhiều máy và luồng mất kết nối cùng thành viên 1.

### Đầu ra

- Các trang chính hoạt động.
- Dữ liệu hiển thị từ API thật.
- Có loading, lỗi, empty state.
- Responsive cơ bản.
- Hướng dẫn chạy frontend.

## 30. Thành viên 3 — Database và nghiệp vụ LMS

### Trách nhiệm

- Thiết kế schema.
- Viết migration và seed.
- Hồ sơ sinh viên, lớp và khóa học, cùng API tương ứng.
- Đăng ký khóa học.
- Import CSV và quy tắc dữ liệu.
- Quản lý tài liệu.
- Điểm danh QR.
- Thành phần điểm và công thức.
- Xuất bảng điểm CSV.
- Backup và restore database, file storage và hướng dẫn kiểm tra bản phục hồi.

### Đầu ra

- Schema và migration.
- Import CSV chạy thật.
- Không tạo tài khoản/đăng ký trùng.
- Điểm danh và bảng điểm.
- CSV export đúng dữ liệu.

## 31. Thành viên 4 — Bài tập, Judge Worker và chấm code

### Trách nhiệm

- Upload và lưu bài tập file.
- API nộp bài file.
- API quản lý kỳ thi, phiên thi, bài lập trình và test case.
- Judge Worker.
- Hỗ trợ C/C++ và Java.
- Standard input/output.
- File input/output.
- Trạng thái chấm và tính điểm.
- Giới hạn tài nguyên.
- Tích hợp kết quả vào bảng điểm.
- Kiểm thử compile error, wrong answer, TLE và runtime error.

### Đầu ra

- Luồng nộp file.
- Luồng chấm code C/C++ và Java.
- Cấu hình compiler/runtime.
- Tài liệu cài đặt judge.
- Test case demo.

## 32. Quy tắc phối hợp

- Thành viên 1 là đầu mối tích hợp backend.
- Thành viên 2 không tự giả định API; thống nhất response với thành viên 1.
- Thành viên 3 là đầu mối schema và dữ liệu LMS.
- Thành viên 4 phối hợp thành viên 1 về API và thành viên 3 về điểm.
- Không ai tự thay đổi tên trường database hoặc response API mà không báo nhóm.
- Mỗi thành viên chịu trách nhiệm code, test và tài liệu module của mình.
- Nếu có blocker quá nửa ngày, phải báo nhóm để điều chỉnh.

---

# PHẦN XII. GIT VÀ QUY TRÌNH LÀM VIỆC

## 33. Nhánh Git

- `main`: bản ổn định.
- `develop`: bản tích hợp.
- `feature/auth`
- `feature/frontend`
- `feature/lms-import-csv`
- `feature/attendance-gradebook`
- `feature/coding-judge`

### Quy tắc

1. Không code trực tiếp trên `main`.
2. Mỗi tính năng dùng một nhánh riêng.
3. Commit có nội dung cụ thể.
4. Merge vào `develop` sau khi kiểm tra.
5. Không commit `.env`, secret, mật khẩu hoặc dữ liệu cá nhân thật.
6. Mỗi lần đổi API phải cập nhật tài liệu.
7. Cuối mỗi ngày, nhóm phải có phiên bản tích hợp chạy được.

## 34. Hợp đồng giao tiếp trước khi code

Hợp đồng 1.1 và mục 60 đã chốt các điểm sau; khi thay đổi phải cập nhật đồng bộ:

- Cách đặt tên API.
- Format lỗi.
- Cách trả danh sách và phân trang nếu cần.
- Cách xác thực.
- Các role.
- Quy tắc tên trường JSON.
- Quy tắc thời gian và múi giờ.
- Các trạng thái submission.
- Quy tắc import CSV.
- Cách lưu đường dẫn file.
- Quy tắc điểm và trọng số.

Ví dụ response lỗi thống nhất:

```
{
  "detail": "Invalid date_of_birth",
  "code": "INVALID_CSV_ROW"
}
```

Các response thật cần được tài liệu hóa theo từng API. Không bắt frontend phải đoán thông báo lỗi từ backend.

---

# PHẦN XIII. LỘ TRÌNH 22/10–31/10/2026

Các mốc 22–23/10 dưới đây giữ để tham chiếu kế hoạch gốc. Từ ngày cập nhật 24/10, dùng mục 63 để điều phối phần việc chưa hoàn thành; không coi ngày trên lịch là bằng chứng hoàn thành.

## 35. Ngày 22/10 — Chốt kiến trúc

- Tạo repository.
- Chốt stack.
- Chốt schema ban đầu.
- Chốt API auth, course, import CSV và submission.
- Tạo README khung.
- Phân công từng module.

**Kết quả:** Mọi thành viên biết mình làm gì và các module kết nối ra sao.

## 36. Ngày 23/10 — Dựng skeleton

- Backend khởi chạy.
- Frontend khởi chạy.
- Database khởi tạo.
- Login và phân quyền bản đầu.
- Tạo migration đầu tiên.
- Tạo component giao diện chung.

**Kết quả:** Frontend gọi được backend.

## 37. Ngày 24/10 — Hoàn thành LMS cơ bản

- Tạo khóa học.
- Import CSV.
- Tạo tài khoản và đăng ký sinh viên.
- Kiểm thử đăng nhập bằng tài khoản import.
- Upload tài liệu.
- Hiển thị khóa học phía sinh viên.

**Kết quả:** Giảng viên import CSV, sinh viên đăng nhập và thấy đúng khóa học.

## 38. Ngày 25/10 — Bài tập và Judge

- Upload bài tập file.
- Tạo bài lập trình.
- Chấm bài C/C++ mẫu.
- Chấm bài Java mẫu.
- Standard input/output.
- Test trạng thái compile error và wrong answer.
- Bắt đầu file input/output.

**Kết quả:** Có ít nhất một bài C/C++ và một bài Java được chấm từ frontend đến kết quả.

## 39. Ngày 26/10 — Tích hợp xuyên suốt

- Kết nối trang bài tập với API.
- Kết nối submission với Judge Worker.
- Lưu kết quả chấm.
- Hiển thị trạng thái.
- Sửa lỗi phân quyền.
- Kiểm thử import CSV và nộp bài.

**Kết quả:** Không còn chỉ là giao diện mock.

## 40. Ngày 27/10 — QR, điểm và export

- Tạo phiên điểm danh.
- Sinh QR.
- Sinh viên check-in.
- Quản lý thành phần điểm.
- Tính tổng kết.
- Xuất CSV.

**Kết quả:** Điểm danh và bảng điểm chạy được.

## 41. Ngày 28/10 — Kiểm thử LAN

- Cấu hình IP server.
- Cấu hình frontend/backend.
- Kiểm tra firewall.
- Kiểm tra CORS, cookie và WebSocket.
- Thử từ ít nhất hai máy client.
- Thử upload, download và chấm code.
- Sửa lỗi đường dẫn và cấu hình.

**Kết quả:** Các máy khác truy cập được hệ thống.

## 42. Ngày 29/10 — Báo cáo

- Sơ đồ kiến trúc.
- Sơ đồ database.
- Mô tả API.
- Ảnh chụp màn hình.
- Kịch bản demo.
- Test cases.
- Hạn chế và hướng phát triển.

**Kết quả:** Báo cáo gần hoàn chỉnh.

## 43. Ngày 30/10 — Đóng băng

- Không thêm tính năng lớn.
- Sửa lỗi nghiêm trọng.
- Chạy thử cài đặt trên môi trường sạch.
- Backup database.
- Kiểm tra README.
- Chốt bản demo.

## 44. Ngày 31/10 — Nộp và demo

- Chạy thử toàn bộ kịch bản.
- Chuẩn bị tài khoản demo.
- Chuẩn bị CSV demo.
- Chuẩn bị bài C/C++ và Java mẫu.
- Kiểm tra USB hoặc bản backup.
- Đảm bảo có thể giải thích kiến trúc và phần việc của từng thành viên.

---

# PHẦN XIV. KIỂM THỬ VÀ NGHIỆM THU

## 45. Kiểm thử tài khoản và CSV

- Import CSV hợp lệ.
- Mã sinh viên có số 0 ở đầu được giữ nguyên.
- Ngày sinh được đọc đúng.
- Ngày sinh không hợp lệ bị báo lỗi.
- Thiếu cột bắt buộc bị báo lỗi.
- Mã sinh viên trùng trong file được phát hiện.
- Import lại không tạo tài khoản trùng.
- Tài khoản đã tồn tại không bị đổi mật khẩu ngoài ý muốn.
- Sinh viên được đăng ký đúng khóa học.
- Sinh viên đổi mật khẩu được.
- Sinh viên không truy cập khóa học ngoài quyền.

## 46. Kiểm thử bài tập và Judge

- Upload file hợp lệ.
- File quá lớn bị từ chối.
- Upload file không được phép bị từ chối.
- Bài C/C++ đúng được chấm đúng.
- Bài Java đúng được chấm đúng.
- Wrong Answer được phát hiện.
- Compile Error được phát hiện.
- Time Limit Exceeded được phát hiện.
- Runtime Error được phát hiện.
- File input/output hoạt động.
- Submission cũ không bị ghi đè.
- Test ẩn không bị lộ.
- Worker không được đọc file nhạy cảm của máy chủ.
- Worker dọn file tạm.

## 47. Kiểm thử điểm danh và bảng điểm

- Phiên điểm danh có hạn.
- Sinh viên ngoài khóa học không điểm danh được.
- Không điểm danh trùng nếu không được phép.
- Giảng viên đóng phiên được.
- Tổng trọng số phải bằng 100%.
- Điểm tổng kết đúng công thức.
- Điểm chưa có được phân biệt với điểm 0.
- CSV export có đúng sinh viên và điểm.
- CSV không chứa thông tin xác thực.

## 48. Kiểm thử LAN

- Frontend truy cập được bằng IP LAN.
- Backend không chỉ bind vào loopback.
- API gọi đúng địa chỉ server.
- WebSocket kết nối từ máy client.
- Mất WebSocket vẫn lấy được trạng thái qua REST.
- Tải file hoạt động.
- Nộp bài hoạt động.
- Không yêu cầu Internet cho luồng demo cốt lõi sau khi cài đặt.
- Có hướng dẫn backup và restore.

---

# PHẦN XV. CÀI ĐẶT VÀ TRIỂN KHAI TRÊN WINDOWS

## 49. Môi trường cần chuẩn bị

Máy phát triển và máy chủ cần có:

- Python phiên bản tương thích với backend.
- Node.js phiên bản LTS tương thích với Next.js.
- Git.
- Compiler C/C++.
- JDK cho Java.
- Công cụ sandbox đã được kiểm thử.
- Các package cần thiết của frontend và backend.

Phiên bản cụ thể cần ghi vào README sau khi nhóm kiểm thử thành công. Không để mỗi thành viên sử dụng một phiên bản không thống nhất.

## 50. Chạy backend

Ví dụ trong PowerShell:

```
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sau khi cấu hình biến môi trường và database:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Địa chỉ `0.0.0.0` cho phép dịch vụ nhận kết nối từ mạng, nhưng firewall vẫn phải giới hạn các kết nối theo nhu cầu.

## 51. Chạy frontend

```
cd client
npm install
npm run dev
```

Khi demo LAN, cần cấu hình để frontend có thể nhận kết nối từ máy khác và trỏ API/WebSocket đến đúng địa chỉ máy chủ.

Ví dụ cấu hình minh họa:

```
NEXT_PUBLIC_API_BASE_URL=/api
NEXT_PUBLIC_WS_PATH=/ws
```

Browser mở địa chỉ web LAN của server; API dùng đường dẫn tương đối cùng origin. URL WebSocket được tạo từ host hiện tại, dùng ws hoặc wss theo HTTP/HTTPS; proxy chuyển /ws về FastAPI. Cổng 8000 là nội bộ trong cấu hình demo đã chốt, không yêu cầu browser gọi trực tiếp.

Không được để client sử dụng `localhost:8000` để gọi backend của server, vì `localhost` trên máy client trỏ về chính máy client.

## 52. Firewall và cấu hình LAN

- Cấu hình IP ổn định cho máy chủ.
- Mở cổng frontend và backend cần thiết trong phạm vi LAN.
- Không mở database ra mạng nếu không cần.
- Không mở cổng Judge Worker cho client.
- Kiểm tra CORS và WebSocket origin.
- Dùng HTTPS nếu môi trường triển khai và chứng chỉ cho phép; nếu dùng HTTP trong LAN demo, ghi rõ giới hạn.
- Kiểm tra kết nối bằng một máy khác, không chỉ dùng trình duyệt trên server.

## 53. Chuyển sang máy khác bằng USB

Cần bàn giao:

- Source code.
- README và docs.
- `.env.example`.
- Script cài đặt.
- Database backup hoặc script khởi tạo.
- Seed data demo.
- Tài liệu mẫu.
- Compiler/runtime C/C++ và Java.
- Cấu hình sandbox.
- Hướng dẫn đổi IP.
- Hướng dẫn backup/restore.

Không đưa mật khẩu thật, token, secret key hoặc dữ liệu cá nhân không cần thiết vào repository hay USB bàn giao.

---

# PHẦN XVI. README VÀ TÀI LIỆU BÀN GIAO

## 54. README.md bản bàn giao bắt buộc có

1. Tên đề tài và mô tả.
2. Chức năng chính.
3. Kiến trúc hệ thống.
4. Công nghệ sử dụng.
5. Phiên bản môi trường.
6. Cấu trúc thư mục.
7. Cài đặt backend.
8. Cài đặt frontend.
9. Cấu hình biến môi trường.
10. Tạo database và seed data.
11. Tạo tài khoản demo.
12. Chạy hệ thống.
13. Import CSV.
14. Tạo khóa học và tài liệu.
15. Tạo bài lập trình.
16. Cài đặt compiler và judge.
17. Chạy trong LAN.
18. Backup/restore.
19. Chạy test.
20. Troubleshooting.
21. Giới hạn bảo mật.
22. Tính năng đã hoàn thành và chưa hoàn thành.
23. Phân công thành viên.
24. Hình ảnh giao diện và sơ đồ.

Chỉ ghi lệnh đã được kiểm thử. Không tuyên bố tính năng hoàn thành nếu mới có giao diện minh họa.

## 55. `docs/AI_HANDOFF.md` (tạo khi có mã nguồn và tiến độ thực tế)

Tạo tài liệu sau để người khác hoặc AI khác có thể tiếp tục dự án mà không phải đọc lại toàn bộ lịch sử:

```
# AI Handoff

## Project
Tên đề tài:
Mục tiêu:
Hạn nộp:

## Tech Stack
Frontend:
Backend:
Database:
Judge:
Môi trường LAN:

## Architecture
Sơ đồ:
Luồng đăng nhập:
Luồng import CSV:
Luồng nộp bài:
Luồng chấm code:
Luồng điểm danh:
Luồng tính điểm:

## Repository
Thư mục quan trọng:
Lệnh chạy frontend:
Lệnh chạy backend:
Lệnh chạy judge:
Cách tạo database:

## Team
Thành viên 1:
Thành viên 2:
Thành viên 3:
Thành viên 4:

## API Contract
Endpoint:
Request/response:
Quyền truy cập:

## Database
Các bảng:
Quan hệ:
Migration/seed:

## Completed
Tính năng đã xong:
Test đã chạy:

## In Progress
Tính năng đang làm:
Người phụ trách:
Blocker:

## Known Bugs
Mô tả:
Cách tái hiện:
Mức độ ưu tiên:

## Decisions
Quyết định đã chốt:
Lý do:

## Next Tasks
Việc tiếp theo theo thứ tự ưu tiên:

## Security Limitations
Xác thực:
Phân quyền:
Upload:
Sandbox:
LAN:

## Demo
Tài khoản demo:
Dữ liệu demo:
Kịch bản demo:
```

Không ghi mật khẩu thật hoặc secret trong tài liệu bàn giao.

---

# PHẦN XVII. KỊCH BẢN DEMO CHÍNH THỨC

## 56. Kịch bản demo khoảng 8–12 phút

### Bước 1 — Giảng viên đăng nhập

- Mở giao diện từ máy giảng viên.
- Đăng nhập bằng tài khoản demo.

### Bước 2 — Tạo khóa học và import CSV

- Tạo khóa học demo.
- Chọn import CSV.
- Xem trước dữ liệu.
- Xác nhận import.
- Hiển thị báo cáo số tài khoản được tạo.

### Bước 3 — Sinh viên đăng nhập

- Mở trình duyệt trên một máy client khác.
- Đăng nhập bằng mã sinh viên và mật khẩu ban đầu.
- Đổi mật khẩu.
- Hiển thị khóa học được đăng ký.

### Bước 4 — Tài liệu và bài tập

- Giảng viên upload tài liệu.
- Sinh viên tải tài liệu.
- Sinh viên nộp bài tập file.

### Bước 5 — Thi lập trình

- Giảng viên mở kỳ thi demo.
- Sinh viên gửi bài C/C++.
- Sinh viên gửi bài Java.
- Một bài được chấm đúng và một bài sai.
- Hiển thị trạng thái chấm.

### Bước 6 — Điểm danh và bảng điểm

- Giảng viên tạo QR.
- Sinh viên điểm danh.
- Giảng viên xem bảng điểm.
- Xuất CSV.

### Bước 7 — Giải thích kiến trúc

- Giới thiệu frontend, backend, database, storage và judge.
- Mô tả REST API và WebSocket.
- Giải thích cách code được chạy trong môi trường cô lập.
- Nêu rõ giới hạn hiện tại và hướng phát triển.

---

# PHẦN XVIII. QUY TẮC QUẢN LÝ PHẠM VI

## 57. Bắt buộc hoàn thành

- Đăng nhập và phân quyền.
- Tạo khóa học.
- Import CSV và tự tạo tài khoản.
- Sinh viên đổi mật khẩu lần đầu.
- Đăng ký khóa học.
- Upload và tải tài liệu.
- Nộp bài tập file.
- Thi C/C++ và Java.
- Standard input/output.
- File input/output.
- Judge Worker với giới hạn tài nguyên phù hợp.
- Theo dõi phiên thi và trạng thái submission.
- Điểm danh QR.
- Bảng điểm và trọng số cấu hình.
- Xuất CSV.
- Chạy được trong LAN.
- README, báo cáo và hướng dẫn cài đặt.

## 58. Có thể làm sau khi phần bắt buộc chạy ổn

- WebSocket nâng cao cho nhiều sự kiện.
- Import ZIP toàn khóa học.
- Bài lập trình nhiều file/project.
- Biểu đồ thống kê phức tạp.
- Thông báo realtime nâng cao.
- Phân tích hành vi thi.
- Nhiều kỳ thi đồng thời với tải lớn.
- Chuyển SQLite sang PostgreSQL.

Không được triển khai tính năng nâng cao bằng cách làm chậm các chức năng bắt buộc.

---

# PHẦN XIX. CÁC QUYẾT ĐỊNH CUỐI CÙNG ĐÃ CHỐT

1. Dùng Next.js, TypeScript, Tailwind CSS cho frontend.
2. Dùng Python FastAPI cho backend.
3. Dùng REST API cho nghiệp vụ và WebSocket cho cập nhật phiên thi/trạng thái chấm.
4. Dùng SQLite cho bản demo đầu tiên; có thể nâng cấp sau nếu cần.
5. Hỗ trợ C/C++ và Java.
6. Hỗ trợ stdin/stdout và file input/output.
7. Bài nhiều file là phần mở rộng nếu yêu cầu thực tế cần.
8. Giảng viên import danh sách sinh viên bằng CSV.
9. Username là mã sinh viên.
10. Mật khẩu ban đầu là ngày sinh `DDMMYYYY`.
11. Sinh viên bắt buộc đổi mật khẩu lần đầu.
12. Import lại không tạo tài khoản trùng hoặc ghi đè mật khẩu tài khoản đã tồn tại.
13. Giảng viên upload tài liệu riêng; không yêu cầu import toàn bộ khóa học bằng ZIP.
14. Theo dõi phiên thi, submission và IP quan sát được; không xem IP là bằng chứng duy nhất của gian lận.
15. Trọng số mặc định là 10% chuyên cần, 20% bài tập, 30% giữa kỳ, 40% cuối kỳ; giảng viên có thể cấu hình.
16. Triển khai mục tiêu trên Windows, có kiểm thử môi trường compiler và sandbox.
17. Ưu tiên hoàn thành luồng demo xuyên suốt trước khi làm tính năng nâng cao.
18. Mọi thành viên phải có code, test và tài liệu cho phần mình phụ trách.

# KẾT LUẬN

Mục tiêu lớn nhất không phải là tạo ra thật nhiều màn hình, mà là hoàn thành một luồng hoạt động thật:

**Giảng viên đăng nhập → tạo khóa học → import CSV → tạo tài khoản sinh viên → sinh viên đăng nhập và đổi mật khẩu → xem tài liệu → nộp bài → gửi code → nhận kết quả chấm → điểm danh → xem bảng điểm → giảng viên xuất CSV.**

Nếu luồng này chạy ổn định trên máy chủ Windows và các máy client trong LAN, hệ thống có tài liệu cài đặt đầy đủ và nhóm giải thích được kiến trúc, đó là nền tảng tốt nhất để hoàn thiện đồ án.

Mọi tính năng đã làm phải được kiểm thử và mô tả trung thực trong báo cáo. Ưu tiên một hệ thống chạy được, có thể cài lại và bàn giao được hơn một hệ thống nhiều chức năng nhưng không tích hợp hoàn chỉnh.

## Việc nhóm nên làm ngay sau khi nhận tài liệu

1. Tạo repository Git và thêm `README.md`, `docs/PROJECT_PLAN.md`, `docs/api-specification.md`.
2. Chốt schema database và API đăng nhập/import CSV trước khi chia nhánh phát triển.
3. Mỗi thành viên dựng phần mình phụ trách, nhưng tích hợp hằng ngày vào `develop`.
4. Ngày đầu tiên cần có frontend gọi được backend; không để đến gần hạn mới tích hợp.
5. Triển khai và giải thích rõ REST/WebSocket, xử lý đồng thời, quản lý trạng thái và xử lý lỗi theo yêu cầu môn học.

Một lưu ý về tiến độ: khoảng thời gian 22–31/10 rất ngắn đối với hệ thống có cả LMS, chấm code và sandbox. Nhóm nên hoàn thành đăng nhập, import CSV, khóa học và một bài C++ được chấm xuyên suốt trước; sau đó mới mở rộng Java, file I/O, điểm danh và các tính năng còn lại.

---

# PHẦN XX. QUYẾT ĐỊNH TRIỂN KHAI VÀ ĐỐI CHIẾU HỌC PHẦN

## 59. Trạng thái và nguồn yêu cầu

Đây là đặc tả thiết kế, chưa phải mô tả sản phẩm đã triển khai. Tại lần rà soát 24/10/2026, repository chỉ có tài liệu và `.gitignore`; chưa có ứng dụng, migration hoặc kết quả kiểm thử. Không đánh dấu Done theo ngày kế hoạch.

Nguồn đối chiếu: Instruction.md (yêu cầu kỹ thuật, báo cáo, thực nghiệm), Topics.md (chủ đề 3, mục 4.5–4.6), README.md mẫu học phần và Submission.md (đóng gói, hạn nộp). Không cần chép đường dẫn máy cá nhân vào repository. Các chức năng CSV, QR, lịch, trọng số, C/C++ và Java là phạm vi nhóm chọn theo trao đổi với giảng viên; không phải tất cả đều được bắt buộc riêng trong bốn file yêu cầu chung.

Nhóm giữ nguyên các chức năng bắt buộc ở mục 57. Lịch/sự kiện và thông báo độc lập chuyển thành phần mở rộng; bản đầu hiển thị lịch thi/hạn nộp từ dữ liệu kỳ thi/bài tập. Không cần xây dựng module calendar riêng trước hạn nộp.

## 60. Các quyết định kỹ thuật cụ thể

### 60.1. Xác thực và triển khai web

- Một địa chỉ web cho trình duyệt; Next.js chuyển tiếp `/api/*` và một reverse proxy chuyển tiếp `/ws` đến FastAPI. Các thành phần nội bộ vẫn có thể dùng cổng 3000 và 8000; trình duyệt gọi URL cùng origin. Script triển khai phải cấu hình cả HTTP lẫn WebSocket.
- Session ngẫu nhiên phía server, cookie `lan_lms_session` HttpOnly, SameSite=Lax, Path=/, thời hạn tuyệt đối 8 giờ. Database chỉ lưu hash session token; logout thu hồi session. Cookie Secure khi dùng HTTPS; demo HTTP LAN ghi rõ giới hạn.
- API thay đổi dữ liệu kiểm tra Origin theo danh sách cho phép và CSRF token gắn với session, gửi qua `X-CSRF-Token`. WebSocket cũng kiểm tra Origin và session.
- Login dùng `username` cho cả hai vai trò. Giảng viên được tạo bằng lệnh seed tương tác, không mở đăng ký công khai và không hard-code mật khẩu. Mật khẩu hash Argon2id; giới hạn độ dài 8–128 ký tự khi tạo/đổi.
- Tài khoản buộc đổi mật khẩu chỉ được dùng me, csrf, logout và change-password. Đổi mật khẩu thu hồi các session cũ và yêu cầu đăng nhập lại.
- Lưu thời gian UTC; API trả ISO 8601 có múi giờ, giao diện hiển thị Asia/Ho_Chi_Minh. Mọi hạn nộp dùng đồng hồ server.
- Giá trị giới hạn bản đầu: CSV 2 MiB/2.000 dòng; tài liệu và bài tập 20 MiB/file; source 256 KiB; output 1 MiB/test. Giới hạn cấu hình phải kiểm tra ở backend và được công bố trên giao diện.

### 60.2. Queue, worker và phục hồi

- Dùng bảng `judge_jobs` bền vững trong SQLite; cùng transaction lưu submission và job. Không chỉ giữ queue trong bộ nhớ.
- Mặc định một worker; cho phép cấu hình hai worker để thực nghiệm. API xử lý I/O, worker là tiến trình riêng; biên dịch/chạy chương trình không chặn tiến trình API.
- Bật foreign keys, WAL và busy timeout 5 giây; transaction ghi ngắn. Không giữ transaction trong khi chạy code. Khi khóa DB kéo dài, trả lỗi có kiểm soát; không mặc định SQLite phục vụ được tải lớn.
- Worker nhận job bằng transaction nguyên tử và gán lease 60 giây; gia hạn mỗi 15 giây. Job có `attempt_id`, `lease_until`, `worker_id`, `attempt_count`. Kết quả chỉ được ghi nếu attempt vẫn sở hữu job.
- Lease hết hạn thì job có thể được nhận lại; tối đa hai lần thử tổng cộng khi lỗi hạ tầng. Hết lượt trả System Error. WA/CE/TLE/MLE/RE không tự retry.
- Có thể thực thi lại sau sự cố nhưng chỉ một kết quả cuối hợp lệ được chấp nhận. Trạng thái, điểm và sự kiện hoàn thành được ghi nhất quán; không cộng điểm nhiều lần.
- WebSocket là thông báo sau khi lưu DB; bỏ lỡ sự kiện thì client lấy trạng thái REST. Sau restart, bài đã lưu không mất và job chưa xong được khôi phục theo lease.
- Bổ sung bảng `auth_sessions`, `csv_import_previews`, `judge_jobs`, `idempotency_keys`, `submission_test_results`; bổ sung cấu hình công bố điểm và chính sách lấy điểm vào schema. Thành viên 3 quản lý migration, thành viên 1/4 chốt trường của module mình.

### 60.3. Môi trường judge

Windows là máy chủ; worker và compiler chạy trong Docker Linux trên WSL2. Worker chỉ nhận job nội bộ; container thực thi riêng cho từng submission/test, không đưa Docker socket vào container chạy code. Quyền điều khiển Docker chỉ thuộc bộ điều phối tin cậy.

Image có compiler C/C++ và JDK được build/pin phiên bản sau khi thử. Code đơn file: C17, C++17, Java với `public class Main`, không package. Biên dịch tối đa 30 giây. Cấu hình mặc định mỗi test: wall time 2 giây, tổng bộ nhớ container 256 MiB, một CPU, tối đa 64 tiến trình; Java cho phép cấu hình bộ nhớ lớn hơn và phải ghi rõ trong đề. Bộ nhớ JVM và tổng bộ nhớ container không được coi là cùng một giới hạn.

Container không có mạng, chạy user không đặc quyền, bỏ capabilities, cấm tăng quyền, filesystem gốc chỉ đọc và vùng ghi tạm giới hạn. Không mount DB, secret hay cả bộ test ẩn vào chương trình; chỉ đưa input của test đang chạy, worker giữ expected output bên ngoài. Hết hạn phải dừng cả cây tiến trình. Giới hạn output được áp dụng cả khi chương trình đang ghi, không chỉ sau khi chạy xong.

Chỉ dùng tên file I/O dạng basename, không cho đường dẫn tuyệt đối hoặc `..`. Không giải nén ZIP bài tập trong bản đầu. Output vượt giới hạn hoặc thiếu file output trả Runtime Error với lý do rõ; không suy đoán MLE nếu không có bằng chứng OOM từ runtime. Container/worker lỗi trả System Error. Phải thử C, C++, Java, timeout, OOM, output quá lớn và quyền file trước khi tuyên bố đáp ứng.

### 60.4. Quy tắc import, thi và điểm

- CSV UTF-8, chấp nhận BOM. Trim khoảng trắng ngoài mã; mã phân biệt hoa/thường và giữ số 0 đầu. Ngày sinh là chuỗi 8 chữ số và phải là ngày thực. Dòng thiếu/sai/trùng/xung đột hồ sơ làm lượt preview không thể xác nhận.
- Preview lưu bản dữ liệu đã kiểm tra phía server, gắn giảng viên và khóa học, hết hạn sau 15 phút. Confirm chỉ gửi preview_id và idempotency key; backend kiểm tra lại dữ liệu hiện tại, import toàn bộ trong một transaction. Có xung đột thì trả 409, yêu cầu preview lại; không ghi một phần.
- Bản đầu dùng cửa sổ thi chung `starts_at`–`ends_at`; không tính thêm thời lượng riêng từ lúc sinh viên vào. Một phiên cho mỗi sinh viên/kỳ thi. Mất kết nối được vào lại cùng phiên, không gia hạn.
- Chỉ nhận bài khi `starts_at <= server_received_at < ends_at`. Bài được lưu hợp lệ trước hạn vẫn chấm sau hạn. Sau khi chủ động kết thúc phiên thì không nhận thêm bài. Không hứa tự động nộp phần code chưa gửi khi trình duyệt mất mạng.
- Submission dùng Idempotency-Key: retry cùng key và nội dung trả cùng bài; cùng key khác nội dung trả 409. Gửi bài mới có key mới và không ghi đè lịch sử.
- Biên dịch một lần; chạy tất cả test để tính điểm từng phần. Điểm bài bằng tổng điểm test đạt. Accepted khi tất cả test đạt, kể cả test có trọng số 0; nếu có test lỗi, verdict lấy lỗi đầu tiên theo thứ tự test. Lưu riêng kết quả từng test; CE/System Error dừng chấm, System Error chưa tính điểm.
- Comparator cấu hình theo bài: exact so sánh nguyên nội dung; normalized chỉ đổi CRLF thành LF và loại khoảng trắng cuối mỗi dòng cùng dòng trống cuối output. Không bỏ khoảng trắng bên trong dòng. Không hỗ trợ số thực ở bản đầu.
- Lấy bài có điểm cao nhất, hòa thì chọn bài được nhận sớm nhất; loại bài System Error. Điểm kỳ thi quy về 10 theo tổng điểm các bài/tổng điểm tối đa. Bài chưa nộp tính 0 khi kỳ thi đã kết thúc; trước đó là điểm tạm.
- Bài tập file do giảng viên chấm thang 10; nhóm homework lấy trung bình các bài đã đóng và chấm xong. Chuyên cần = 10 × số phiên có mặt/số phiên đã đóng, mỗi phiên trọng số như nhau. Chưa có phiên/bài thì điểm thành phần là null.
- Giảng viên gán kỳ thi vào giữa kỳ hoặc cuối kỳ; bản đầu một kỳ thi cho mỗi thành phần/khóa học. Điểm tổng kết null nếu còn thành phần có trọng số dương chưa có điểm; thành phần trọng số 0 được bỏ qua. Làm tròn hai chữ số ở kết quả cuối, không làm tròn trung gian.
- Giảng viên công bố điểm theo khóa học. Sinh viên chỉ xem điểm đã công bố của mình. Mặc định chỉ trả verdict/điểm tổng bài; test ẩn không trả input, expected output hay actual output. Khi sửa điểm/trọng số sau công bố phải thu hồi công bố và lưu audit log.
- QR: một token ngẫu nhiên cho phiên, mặc định 5 phút; nhập mã là phương án thay thế quét camera. Unique(session_id, student_id) chặn check-in trùng; HTTP LAN không được coi là đã kiểm thử camera trên mọi trình duyệt.

## 61. Phân công bổ sung và trách nhiệm tích hợp

| Thành viên | Sở hữu module/API | Minh chứng phải bàn giao |
|---|---|---|
| 1 | Auth/session, CSRF, chuẩn lỗi, WebSocket, cấu hình web cùng origin | Test quyền, mất kết nối, tích hợp; tổng hợp báo cáo và đóng gói |
| 2 | Frontend student/teacher, REST/WS, trạng thái lỗi và retry | Kiểm thử luồng người dùng trên ít nhất hai máy; ảnh/demo và hướng dẫn frontend |
| 3 | Migration/seed, course, CSV, materials, attendance, grades, backup/restore | Ràng buộc dữ liệu, tính điểm, CSV, thử phục hồi và tài liệu schema |
| 4 | Assignment, coding exam/session/problem/test, submission, queue/worker/sandbox | C/C++/Java, test judge, benchmark một/hai worker, hướng dẫn môi trường |

Thành viên 1 hỗ trợ hạ tầng cho thành viên 3, không cùng sở hữu code nghiệp vụ CSV/course. Thành viên 4 thống nhất dữ liệu điểm với thành viên 3; thành viên 2 tích hợp theo hợp đồng đã chốt. Mỗi người viết phần Implementation, Test và Limitations của module mình; thành viên 1 tổng hợp, không tự viết thay toàn nhóm.

## 62. Thực nghiệm và đóng góp kỹ thuật

Không mở rộng đề tài chỉ để tạo novelty. Đóng góp dự kiến: luồng nhận bài bền vững, hàng đợi và worker tách API, cập nhật trạng thái qua WebSocket và khôi phục qua REST. Chỉ công nhận nội dung có implementation/test làm bằng chứng.

Baseline do nhóm xây dựng: cùng pipeline, một worker. Phương án so sánh: hai worker, cùng máy, cùng bộ bài, cùng giới hạn container. Không khẳng định cải thiện trước khi đo; hai worker có thể tranh CPU/RAM và làm tăng thời gian từng bài.

| Kịch bản | Cách đo | Đầu ra |
|---|---|---|
| 1, 5, 10, 20 client đồng thời | Đăng nhập, xem đề, gửi bài; tài khoản riêng | Response time p50/p95, error rate, số client thực tế |
| 1 và 2 worker | Cùng 20 submission C/C++/Java gồm bài nhanh/chậm; chạy ba lần mỗi cấu hình | Queue wait, compile time, execution time, end-to-end time, throughput |
| Ngắt WS và kết nối lại | Lưu bài rồi ngắt mạng, vào lại | Submission còn nguyên, trạng thái REST đúng, thời gian phục hồi |
| Worker dừng khi đang chấm | Dừng worker, đợi lease, khởi động lại | Không mất job, chỉ một kết quả cuối được ghi |
| Retry và dữ liệu lỗi | Cùng key gửi lại; CSV trùng; QR trùng | Không tạo bản ghi trùng, mã lỗi đúng |

Ghi CPU/RAM/OS, phiên bản công cụ, cấu hình LAN, số worker, dataset, lần chạy và cách warm-up. Tải mô phỏng từ một máy không được mô tả thành 20 máy vật lý. Lưu script, dữ liệu giả lập, log thô và bảng tổng hợp trong `tests/load/` và `experiments/`; chưa tạo các thư mục này cho đến khi có nội dung thật.

Không bịa số liệu. Báo cáo theo cấu trúc technical paper trong Instruction.md: Abstract, Keywords, Introduction, Related Work, Problem Definition, Approach, Architecture, Network Design, Implementation, Experimental Setup, Results, Discussion, Contributions, Limitations, Future Work, Conclusion, References và Appendix khi cần.

## 63. Điều phối lại từ 24/10/2026

| Ngày | Ưu tiên và điều kiện đạt |
|---|---|
| 24/10 | Chốt hợp đồng, dựng auth và schema; đồng thời thử Docker/compiler; frontend gọi API thật |
| 25/10 | Course/CSV/materials; một bài C++ từ trình duyệt đến kết quả; thử sớm Java và file I/O |
| 26/10 | Hoàn thiện C/C++/Java, queue bền vững, phiên thi, retry và WebSocket |
| 27/10 | QR, bảng điểm, export; tích hợp luồng demo; ghi báo cáo song song |
| 28/10 | Kiểm thử nhiều máy LAN, benchmark, ngắt kết nối và worker lỗi; lưu dữ liệu thật |
| 29/10 | Phân tích kết quả, hoàn thiện báo cáo, kiểm tra Compilatio và sửa nội dung cần thiết |
| 30/10 | Đóng băng tính năng, cài lại trên môi trường sạch, phục hồi backup, đóng gói |
| 31/10 | Kiểm tra phiên bản cuối và bàn giao trước 23:59 |

Đây là mục tiêu, không xác nhận tiến độ. Nếu thiếu thời gian, loại phần mở rộng trước; không lặng lẽ bỏ các yêu cầu nhóm đã cam kết. Blocker compiler/sandbox cần xử lý ngay ngày đầu thay vì dồn cuối lịch.

## 64. Nộp bài, README và checklist cuối

- Hạn nộp: **23:59 ngày 31/10/2026, giờ Việt Nam** theo Submission.md.
- Mỗi nhóm một báo cáo Compilatio; dùng tên `NhomXX_LANLMS_Report.docx`. Submission.md khuyến nghị DOCX; có thể xuất thêm PDF để đọc. Kiểm tra ngưỡng tương đồng theo Instruction.md (≤20%) và trích dẫn nguồn đúng.
- Thư mục source đặt tên `NhomXX_LANLMS_Source`. Gói bàn giao cuối `NhomXX_LANLMS/Source/` và `NhomXX_LANLMS/Report/`; lớp trưởng thu vào USB theo Submission.md.
- Instruction.md/README mẫu còn nhắc Google Drive; lưu ý khác biệt này và cập nhật theo thông báo cuối của giảng viên/lớp trưởng. Không coi GitHub là thay thế hình thức nộp chính thức.
- Source gồm README, source, lockfile/requirements, `.env.example`, migration/seed giả lập, test, script, cấu hình và hướng dẫn build image judge. Nếu yêu cầu cài offline thì kèm gói cài/image cần thiết; phân biệt rõ cài đặt cần Internet với chạy demo không cần Internet.
- Backup phải nhất quán cả SQLite và storage: dừng ghi, dùng SQLite backup API hoặc quy trình checkpoint/backup đã kiểm thử; không chỉ copy một file DB đang có WAL rồi coi là bản sao đầy đủ. Thử restore thực tế.
- README cuối phải có kiến trúc, mạng/message, môi trường, lệnh đã chạy thử, setup DB, chạy client/server/worker, test, thực nghiệm/kết quả, contributions, limitations, references và đóng góp cá nhân tổng 100%. Hiện chưa có tên/MSSV nên chưa điền thay nhóm.
- [ ] Luồng demo và quyền trên hai máy được kiểm thử.
- [ ] Retry không tạo submission/điểm danh/import trùng.
- [ ] Worker lỗi và WebSocket lỗi được kiểm thử.
- [ ] Có log thực nghiệm, bảng kết quả và discussion.
- [ ] Tất cả thành viên giải thích được giao tiếp mạng và phần code của mình.
- [ ] Báo cáo đúng bản cuối; Compilatio và tên file đúng.
- [ ] Source build/run được, backup restore được, không có secret thật.

## 65. Ghi nhận thay đổi phiên bản 1.1

Giữ khung 19 phần và nghiệp vụ chính từ bản nhóm cung cấp; sửa đường dẫn Next.js trùng URL, bỏ cảnh báo TCP không có căn cứ trong yêu cầu hiện có, chốt session/CSRF và triển khai cùng origin, bổ sung queue/lease và sandbox cụ thể, quy tắc CSV/thi/điểm, ranh giới phân công, thực nghiệm, lịch cập nhật và quy định nộp bài. Các mục 59–64 cụ thể hóa lựa chọn còn để mở ở các phần trước; khi có cách diễn đạt chung, áp dụng quyết định cụ thể tại các mục này và hợp đồng API 1.1.
