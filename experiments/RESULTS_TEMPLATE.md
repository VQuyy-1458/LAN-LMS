# Kết quả thực nghiệm LAN-LMS

## HTTP loopback Windows

Ba lần cho mỗi mức client, tổng 324 request đo. Login/CSRF/session/warm-up nằm ngoài latency; không chạy judge trong phép đo này. CPU Intel i5-12500H, 16 CPU logic, 15,73 GiB RAM. Bảng là trung vị ba thống kê từng lượt. Không phải nhiều máy LAN vật lý.

| Client | p50 ms | p95 ms | Request/s | Request đo | Lỗi |
|---|---|---|---|---|---|
@@HTTP_TABLE@@

Raw: [CSV](results/windows-loopback-2026-10-25/network-raw.csv), [môi trường và từng lượt](results/windows-loopback-2026-10-25/network-summary.json).

## Docker một và hai worker

Cùng runner, 20 submission C/C++/Java mỗi lượt, ba lượt/cấu hình. Fresh DB, cùng image và giới hạn 3000 ms/256 MiB, mỗi bài thứ tư chờ một giây. Tất cả 120 submission AC. Wall time gồm overhead Docker.

Môi trường: @@JUDGE_ENV@@.

| Worker | Wall time s | Bài/s | p50 chờ s | p50 tổng s |
|---|---|---|---|---|
@@WORKER_TABLE@@

Throughput hai worker bằng @@SPEEDUP@@ lần một worker trong bộ đo. Không suy ra tăng tuyến tính cho mọi đề/máy. busy_time_ratio là thời gian worker bận, không phải CPU utilization.

Nguồn [CI](@@CI_URL@@), commit @@HEAD@@. [Raw JSON](results/@@DATA_FOLDER@@/judge-summary.json), [provenance](results/@@DATA_FOLDER@@/provenance.json). Metadata CPU/RAM/Docker/image ID nằm trong JSON. Các lần đo trước giữ nguyên trong results nhưng không trộn vào bảng này.

## Phân tích và giới hạn

P95 HTTP tăng khi tranh khóa SQLite. Hai worker giảm queue wait ở dataset mẫu nhưng cùng tranh CPU/RAM/Docker. Thứ tự một rồi hai worker và chỉ ba lần có thể chịu cache/nhiễu. Không báo confidence interval từ ba điểm. HTTP Windows và judge Linux là hai phép đo khác nhau, không dùng để so hai OS. Docker Windows và hai máy LAN thật chưa được nghiệm thu.
