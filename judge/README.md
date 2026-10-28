# Judge LAN-LMS

Build: docker build -t lan-lms-judge:day25 judge. Chạy worker từ gốc repo bằng python -m judge.worker --worker-id worker-1; tiến trình thứ hai dùng worker-2. API và worker dùng cùng DATABASE_URL/STORAGE_ROOT; .env server được nạp bởi Settings. Chỉ dựng image bằng docker compose --profile judge build; Compose hiện không điều phối toàn bộ web/API.

worker.py nhận job bền vững qua job_queue.py, heartbeat và fenced completion; runners/container.py biên dịch/chạy Docker, sandbox_entry.py là supervisor trong container; limits.py, languages/config.py và comparators/output.py định nghĩa runtime. Không chạy code trong API.

Chấm độc lập: python -m judge.cli --language cpp --source Main.cpp --manifest problem.json. Manifest có time_limit_ms,memory_limit_mib,io_mode,comparator,tests; mỗi test có input/expected là path tương đối manifest và points. File mode có input_filename/output_filename là basename khác nhau. Không nhận đường dẫn thoát thư mục hoặc lệnh compiler tùy ý.

RUN_DOCKER_TESTS=1 python -m pytest tests/integration/test_judge_docker.py tests/integration/test_completion.py -q. Chỉ bật khi Docker Linux engine và image sẵn sàng. Docker giới hạn quyền/tài nguyên, không được mô tả an toàn tuyệt đối. Xem docs/coding-judge.md và README gốc.
