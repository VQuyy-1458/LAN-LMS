# Thực nghiệm tái lập

Từ gốc repo dùng venv của API:

```powershell
python -m experiments.run_network --output .runtime/network
python -m experiments.run_judge --output .runtime/judge --trials 3 --jobs 20
```

HTTP thử 1/5/10/20 client mô phỏng, ba lần, ba request đo cho mỗi client. Log CSV và JSON có môi trường. Login, CSRF, session start và warm-up nằm ngoài latency. Đây là loopback trên một máy, không phải 20 máy LAN.

Judge cần Docker engine và image thật. Cùng bộ bài C/C++/Java, một/hai worker, database mới cho từng lần. Đo wall time của queue wait, compile, run, end-to-end và throughput. busy_time_ratio là thời gian worker bận, không phải CPU utilization.

Kết quả đã đo ở results/; RESULTS.md giải thích nguồn, cấu hình và hạn chế. CI đo khi commit có marker [benchmark], lưu artifact judge-measurements. Provenance ghi run/head/artifact. Kết quả lịch sử giữ nguyên; báo cáo chọn rõ một lần đo, không trộn số của các máy.
