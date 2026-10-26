# Chạy LAN và chuyển máy

Máy Windows có thể nhấp CHAY_LAN.cmd: localhost HTTP 8080 cho máy chủ, HTTPS 8443 cho điện thoại. Trang http://IP:8080/setup hướng dẫn cài CA một lần cho Android và iPhone; xem [PHONE_CAMERA](PHONE_CAMERA.md). Cần OpenSSL của Git for Windows hoặc OPENSSL_PATH. Không đổi firewall/trust tự động. QR tạo từ localhost vẫn chứa PUBLIC_ORIGIN HTTPS đúng của LAN.

Sau khi Docker Linux Engine chạy, nhấp BAT_BO_CHAM.cmd để tạo image. Worker nền chờ Engine/image sẵn sàng mới nhận job, có heartbeat cho mục Thi lập trình. Xem [bộ đề thực hành cụ thể](../demo/README.md).
Dùng README gốc mục 10–11. Máy chủ cần Python 3.12, Node.js 22, Docker Linux và Nginx. Tạo venv, cài lockfile, chạy migration, `npm ci` và build frontend, build image judge rồi seed teacher tương tác. Máy sinh viên chỉ cần trình duyệt cùng LAN.

Nginx cổng 8080 là origin web; Next.js cổng 3000 và API cổng 8000 nghe loopback. `ALLOWED_ORIGINS` phải khớp origin trình duyệt dùng, ví dụ `http://192.168.1.10:8080`. Proxy chuyển `/api` và `/ws`, giữ Host, hỗ trợ upgrade WebSocket và chuyển địa chỉ client. Uvicorn chỉ tin forwarded headers từ `127.0.0.1`. Sinh viên truy cập IP máy chủ, không dùng localhost trên máy mình.

Mở API, client, worker và proxy theo scripts. Chỉ chạy một Uvicorn worker; có thể chạy một hoặc hai judge worker tùy tài nguyên. Trên từng máy, chạy `python -m scripts.check_lan --base-url http://IP_MAY_CHU:8080 --username MA_SINH_VIEN` để kiểm tra health, ready, auth, CSRF, WS và logout. Sau đó thử nhận bài, chấm và reconnect trên browser. Loopback hoặc CI thành công không chứng minh đã nghiệm thu hai máy.

HTTP LAN demo không mã hóa đường truyền. Camera trực tiếp trong web cần **HTTPS được trình duyệt tin cậy hoặc localhost**. Trên địa chỉ LAN HTTP, sinh viên dùng **Chụp / chọn ảnh QR** (giải mã tại máy, không upload ảnh) hoặc nhập mã. Muốn mở camera trực tiếp trên điện thoại qua LAN, cấu hình Nginx HTTPS bằng chứng chỉ có SAN khớp IP/tên máy chủ và được các thiết bị tin cậy, đặt `ALLOWED_ORIGINS` đúng origin HTTPS và `SECURE_COOKIE=true`, rồi truy cập bằng HTTPS. Không tắt kiểm tra bảo mật của trình duyệt. Các script không tự cài chứng chỉ, thay firewall hay thiết lập bảo mật của máy.

Khách vào `/` để xem danh mục khóa học, bấm khóa học sẽ được yêu cầu đăng nhập. Nội dung, danh sách sinh viên, lịch học và dữ liệu điểm danh vẫn yêu cầu đăng nhập và quyền của khóa học.

Giảng viên mở **Điểm danh → khóa học**, tạo lịch học nếu chưa có, bấm **Tạo QR điểm danh buổi học này**, chọn thời hạn rồi mở phiên. Bảng phía dưới gồm toàn bộ sinh viên đang học, kể cả người chưa quét; từng dòng có **Có mặt / Đến muộn / Vắng**. Mọi chỉnh tay lưu nhật ký, vô hiệu hóa bảng điểm đã công bố để giảng viên kiểm tra lại. Sinh viên mở **Điểm danh QR → khóa học**, mở camera hoặc chọn ảnh QR; khi đọc được mã hợp lệ, hệ thống tự gửi điểm danh. Quét lại không ghi đè điều chỉnh của giảng viên. Đến muộn được ghi riêng và hiện được tính là có tham gia buổi học khi tính chuyên cần, chưa áp dụng phạt điểm riêng.

Backup/restore dùng `scripts.backup_database` theo README mục 22: giữ DB và storage đồng bộ, kiểm tra checksum, restore sang đích mới. Nên dừng API/worker trước backup lớn để tránh tranh khóa hoặc hết lease. Chuyển cả snapshot, trỏ `DATABASE_URL` và `STORAGE_ROOT` sang đích mới, chạy migration/verify rồi khởi động. Không copy riêng file DB đang dùng WAL; không đưa `.env` hoặc backup thật lên Git.

Cài dependency và build image lần đầu cần Internet. Khi đã cài đủ, web, API, QR và bộ chấm trên LAN không cần dịch vụ ngoài. Để chuyển máy hoàn toàn offline, chuẩn bị bộ cài, cache npm/pip và image qua `docker save/load` đúng phiên bản. Gói source không tự bao gồm các bộ cài này.
