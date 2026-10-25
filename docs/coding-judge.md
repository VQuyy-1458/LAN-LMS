# Thi lập trình và bộ chấm

Mỗi khóa có tối đa một giữa kỳ và một cuối kỳ. Giảng viên chọn số bài và bảng quy đổi; mặc định năm bài với `[0,5,7,8,9,10]`. Một bài có ít nhất một AC hợp lệ trước hạn được tính một lần. Lần WA, RTE hoặc SE sau đó không xóa bài đã giải. Chỉ lưu kết quả tổng của bài, không có bảng kết quả từng test.

Source UTF-8 tối đa 256 KiB. Hỗ trợ C17, C++17 và Java17; Java dùng class Main, không package. Có stdio hoặc file I/O. Compiler và runtime nhận argv cố định, không nhận lệnh shell từ người dùng. Comparator exact giữ nguyên bytes; normalized đổi CRLF thành LF, bỏ space/tab cuối mỗi dòng và newline cuối, giữ khoảng trắng đầu dòng và nội bộ.

API ghi source, submission, job và idempotency nguyên tử rồi trả 202. Worker riêng claim bằng `BEGIN IMMEDIATE`, lease 60 giây, gia hạn mỗi 10 giây, có attempt token và tối đa ba attempt. Compile một lần; mỗi test dùng container mới. Container chạy UID 65534, không có network, root filesystem chỉ đọc, bỏ capabilities, bật no-new-privileges, giới hạn CPU, RAM/swap, pids, tmpfs, output, thời gian và file. Expected output chỉ được đọc ở host. JVM heap còn giới hạn `-Xmx128m`; `memory_limit_mib` là trần toàn container, không phải cam kết heap khả dụng.

Trạng thái Pending/Compiling/Running chuyển sang AC/WA/CE/TLE/MLE/RTE/SE. Lỗi chương trình như CE/WA có score 0; AC có score bằng max_score; pending/SE có score null. Max_score là tổng trọng số test nội bộ; điểm kỳ thi thang 10 là `ladder[số bài AC]`. Worker ghi result và outbox trong cùng transaction; API gửi WS, reconnect lấy snapshot qua GET. SE thể hiện lỗi hạ tầng, không được giả thành AC.

Build bằng `docker build -t lan-lms-judge:day25 judge`, sau đó chạy `python -m judge.worker`. Không expose Docker socket ra web. CLI runner ở [judge/README.md](../judge/README.md); test Docker thật có kiểm tra file/network isolation. Kết quả thực nghiệm tại [experiments/RESULTS.md](../experiments/RESULTS.md). Docker Windows và LAN nhiều máy cần nghiệm thu riêng.
