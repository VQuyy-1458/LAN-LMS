# Khóa thực hành thi qua mạng

Chạy từ gốc repo sau khi tài khoản teacher/student đã tồn tại:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.seed_network_lab --teacher review_teacher --student review001
~~~

Script thêm khóa LTM-THUCHANH-2026, không reset mật khẩu, không sửa khóa học cũ, không ghi đè đề hay bài nộp khi chạy lại. Trên máy demo hiện tại, dùng DB/storage mà launcher đang dùng. Có thể chỉ định --database-url và --storage-root cho môi trường khác.

Khóa có lịch học để tạo QR, hướng dẫn thực hành, bài tập phân tích HTTP/WebSocket, giữa kỳ và cuối kỳ. Mỗi đề 5 bài, tổng cộng **10 bài / 62 test**. Hai đề demo mở 7 ngày từ lúc seed để thử ngay; lịch thi chính thức do giảng viên tự tạo.

| Giữa kỳ | Cuối kỳ |
|---|---|
| Kiểm tra IPv4 | Kiểm tra cùng subnet |
| IPv4 sang số nguyên | TTL qua router |
| Nhận diện cổng dịch vụ | Tách khung bản tin TCP |
| Tổng kích thước bản tin | Checksum bù một 16 bit |
| Phân loại HTTP status | Độ trễ đường truyền ngắn nhất |

Tất cả bài có input/output, ví dụ, giới hạn, test biên và test ẩn. Hỗ trợ C17, C++17, Java 17. Điểm mặc định theo số bài AC: 0/1/2/3/4/5 bài → 0/5/7/8/9/10. Solution tham chiếu chỉ nằm trong source phục vụ kiểm thử, không có endpoint trả solution hoặc test ẩn cho sinh viên.

## Bộ chấm thật

Mở Docker Desktop, chờ Linux Engine chạy, nhấp BAT_BO_CHAM.cmd để chuẩn bị image. CHAY_LAN.cmd quản lý worker nền. Worker chờ khi Docker/image chưa sẵn sàng; không nhận job rồi trả kết quả giả. Mục Thi lập trình hiển thị worker còn hoạt động và số bài trong hàng đợi.

Nộp bài thật: browser → HTTP POST có CSRF/Idempotency-Key → SQLite submission+job → worker lease → Docker compile/run từng test → aggregate verdict → outbox → WebSocket; REST khôi phục trạng thái khi mất kết nối. Chỉ lưu kết quả tổng bài. Có Pending/Compiling/Running, AC/WA/CE/RTE/TLE/MLE/SE.

Kiểm thử Docker end-to-end cho cả 5 bài cuối kỳ:

~~~powershell
$env:RUN_DOCKER_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest tests/integration/test_network_lab.py -q
~~~

Lệnh này cần engine và image thật. CI Linux chạy cùng bộ test; không có fallback thực thi bài sinh viên trực tiếp trên host.
