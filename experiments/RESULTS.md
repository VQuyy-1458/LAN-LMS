# Kết quả thực nghiệm LAN-LMS

## HTTP loopback Windows

Ba lần cho mỗi mức client, tổng 324 request đo. Login/CSRF/session/warm-up nằm ngoài latency; không chạy judge trong phép đo này. CPU Intel i5-12500H, 16 CPU logic, 15,73 GiB RAM. Bảng là trung vị ba thống kê từng lượt. Không phải nhiều máy LAN vật lý.

| Client | p50 ms | p95 ms | Request/s | Request đo | Lỗi |
|---|---|---|---|---|---|
| 1 | 7.36 | 19.35 | 80.56 | 9 | 0% |
| 5 | 35.56 | 65.80 | 107.94 | 45 | 0% |
| 10 | 66.21 | 187.70 | 86.86 | 90 | 0% |
| 20 | 137.39 | 327.17 | 87.56 | 180 | 0% |

Raw: [CSV](results/windows-loopback-2026-10-25/network-raw.csv), [môi trường và từng lượt](results/windows-loopback-2026-10-25/network-summary.json).

## Docker một và hai worker

Cùng runner, 20 submission C/C++/Java mỗi lượt, ba lượt/cấu hình. Fresh DB, cùng image và giới hạn 3000 ms/256 MiB, mỗi bài thứ tư chờ một giây. Tất cả 120 submission AC. Wall time gồm overhead Docker.

Môi trường: Linux-6.17.0-1022-azure-x86_64-with-glibc2.39; AMD EPYC 9V45 96-Core Processor; 4 CPU logic; 15.61 GiB RAM; Python 3.12.15; Docker 28.0.4.

| Worker | Wall time s | Bài/s | p50 chờ s | p50 tổng s |
|---|---|---|---|---|
| 1 | 16.47 | 1.214 | 8.77 | 9.20 |
| 2 | 9.04 | 2.211 | 4.04 | 5.08 |

Throughput hai worker bằng 1.82 lần một worker trong bộ đo. Không suy ra tăng tuyến tính cho mọi đề/máy. busy_time_ratio là thời gian worker bận, không phải CPU utilization.

Nguồn [CI](https://github.com/VQuyy-1458/LAN-LMS/actions/runs/40202701438), commit 8ed2c140e70bba601c46566a315e09843adc1060. [Raw JSON](results/ci-linux-40202701438/judge-summary.json), [provenance](results/ci-linux-40202701438/provenance.json). Metadata CPU/RAM/Docker/image ID nằm trong JSON. Các lần đo trước giữ nguyên trong results nhưng không trộn vào bảng này.

## Phân tích và giới hạn

P95 HTTP tăng khi tranh khóa SQLite. Hai worker giảm queue wait ở dataset mẫu nhưng cùng tranh CPU/RAM/Docker. Thứ tự một rồi hai worker và chỉ ba lần có thể chịu cache/nhiễu. Không báo confidence interval từ ba điểm. HTTP Windows và judge Linux là hai phép đo khác nhau, không dùng để so hai OS. Docker Windows và hai máy LAN thật chưa được nghiệm thu.
