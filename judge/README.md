# Judge — thành viên 4

File khung, chưa có worker chạy được. worker.py điều phối; job_queue.py quản lý claim/lease/retry; limits.py giới hạn tài nguyên; runners/ biên dịch và thực thi cô lập; languages/ cấu hình C/C++/Java; comparators/ so sánh output. Không đặt tên queue.py để tránh trùng module chuẩn Python.

Tuân theo PROJECT_PLAN.md mục 60.2–60.4. Không chạy bài sinh viên trực tiếp trong API. Tạo migration judge_jobs cùng thành viên 3, rồi phối hợp API/submission với thành viên 1. docker-compose.yml hiện là placeholder; chưa có image hoặc sandbox. Không trả kết quả chấm giả.
