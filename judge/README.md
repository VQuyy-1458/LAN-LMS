# Judge — nhiệm vụ TV4 ngày 24–25

Đã có Dockerfile, limits.py, languages/config.py, comparators/output.py, sandbox_entry.py, runners/container.py và cli.py. Compiler C17/C++17/JDK17; stdio và file I/O; chấm tất cả test trong container mới từng test, chỉ trả tổng bài. Biên dịch một lần vào thư mục artifact riêng; expected output chỉ ở orchestrator.

Build/run/test và manifest: docs/INTEGRATION_24_25.md. Test Docker thật được chạy trên GitHub CI. CPU/RAM/pids/time/output/file/network được giới hạn; không chạy code sinh viên trực tiếp trên máy chủ. Docker socket chỉ orchestrator tin cậy dùng qua CLI, không mount vào container.

worker.py và job_queue.py vẫn là khung cho ngày 26; CLI runner không phải hàng đợi tự động đã tích hợp API. Docker Desktop Windows trên máy làm việc hiện lỗi khởi động; CI Linux đã kiểm chứng compiler/sandbox. Chưa tuyên bố môi trường nào an toàn tuyệt đối.
