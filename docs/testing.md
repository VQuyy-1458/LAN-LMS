# Kiểm thử và nghiệm thu

README gốc có lệnh cài, test và build. Chạy pytest khi không đặt `RUN_DOCKER_TESTS` sẽ bỏ qua các ca Docker; CI Linux đặt biến bằng `1` và build image thật. Không coi skipped là passed.

- `test_member1` và `integration/test_member1_day24`: auth, cookie/CSRF/Origin, role, session revocation, lỗi, migration, WS heartbeat.
- `test_database`: unique/FK và ghi đồng thời.
- `test_day25`: course/CSV/file/material/assignment/retry/deadline và nâng DB có dữ liệu.
- `test_completion`: QR, CSV expiry/race, exam/private test/source, hết giờ, lease/fencing/retry, AC ladder/điểm/công bố, worker → WS, seed idempotent, API → Docker worker thật.
- `test_backup`: backup/restore DB và file, checksum, tamper và từ chối ghi đè.
- `test_judge_docker`: C/C++/Java, stdio/file, AC/WA/CE/TLE/MLE/RTE, output cap và kiểm tra file/network/nonroot.

Frontend cần qua TypeScript, ESLint và production build. Kịch bản browser qua Nginx gồm teacher/student, dashboard, khóa học, tài liệu, bài tập, QR, thi và bảng điểm. Dùng dữ liệu giả lập biệt lập; ghi rõ bước nào đã kiểm tra tại [ACCEPTANCE.md](ACCEPTANCE.md).

Thực nghiệm dùng `python -m experiments.run_network` và `python -m experiments.run_judge`; tham số `--output`, dữ liệu thô và phân tích ở [experiments/RESULTS.md](../experiments/RESULTS.md). Mô phỏng 20 client trên một máy khác với 20 máy thật. Nghiệm thu LAN hai máy dùng `scripts.check_lan` từ mỗi máy, kiểm tra nhận bài/reconnect và ghi lại thời điểm, môi trường, kết quả thật.

Trước khi nộp, nhóm cần nghiệm thu Docker Windows trên máy demo, hai máy LAN, cài sạch ở máy khác, điền thông tin nhóm, kiểm tra Compilatio và bàn giao theo thông báo học phần. Không tick các bước chưa có bằng chứng.
