# Chạy LAN và chuyển máy

Dùng README gốc mục 10–11. Máy chủ cần Python 3.12, Node.js 22, Docker Linux và Nginx. Tạo venv, cài lockfile, chạy migration, `npm ci` và build frontend, build image judge rồi seed teacher tương tác. Máy sinh viên chỉ cần trình duyệt cùng LAN.

Nginx cổng 8080 là origin web; Next.js cổng 3000 và API cổng 8000 nghe loopback. `ALLOWED_ORIGINS` phải khớp origin trình duyệt dùng, ví dụ `http://192.168.1.10:8080`. Proxy chuyển `/api` và `/ws`, giữ Host, hỗ trợ upgrade WebSocket và chuyển địa chỉ client. Uvicorn chỉ tin forwarded headers từ `127.0.0.1`. Sinh viên truy cập IP máy chủ, không dùng localhost trên máy mình.

Mở API, client, worker và proxy theo scripts. Chỉ chạy một Uvicorn worker; có thể chạy một hoặc hai judge worker tùy tài nguyên. Trên từng máy, chạy `python -m scripts.check_lan --base-url http://IP_MAY_CHU:8080 --username MA_SINH_VIEN` để kiểm tra health, ready, auth, CSRF, WS và logout. Sau đó thử nhận bài, chấm và reconnect trên browser. Loopback hoặc CI thành công không chứng minh đã nghiệm thu hai máy.

HTTP LAN demo không mã hóa đường truyền. Nếu triển khai HTTPS, cấu hình reverse proxy, chứng chỉ phù hợp và `SECURE_COOKIE=true`. Camera QR có thể yêu cầu secure context; có thể mở QR bằng camera hệ thống hoặc nhập mã. Các script không tự thay firewall hay thiết lập bảo mật của máy.

Backup/restore dùng `scripts.backup_database` theo README mục 22: giữ DB và storage đồng bộ, kiểm tra checksum, restore sang đích mới. Nên dừng API/worker trước backup lớn để tránh tranh khóa hoặc hết lease. Chuyển cả snapshot, trỏ `DATABASE_URL` và `STORAGE_ROOT` sang đích mới, chạy migration/verify rồi khởi động. Không copy riêng file DB đang dùng WAL; không đưa `.env` hoặc backup thật lên Git.

Cài dependency và build image lần đầu cần Internet. Khi đã cài đủ, web, API, QR và bộ chấm trên LAN không cần dịch vụ ngoài. Để chuyển máy hoàn toàn offline, chuẩn bị bộ cài, cache npm/pip và image qua `docker save/load` đúng phiên bản. Gói source không tự bao gồm các bộ cài này.
