# Quyết định

Phụ trách: cả nhóm.

PROJECT_PLAN.md mục 60 và api-specification.md là nguồn quyết định 1.1. Mỗi thay đổi ghi ngày, lý do, ảnh hưởng API/schema và cập nhật hai tài liệu đó; không tự chọn kiến trúc khác trong module.

Cần cập nhật khi triển khai: đường dẫn mã nguồn, lệnh chạy đã thử, kiểm thử thực tế và hạn chế còn lại.


## Cập nhật tích hợp ngày 25/10/2026

Xem [INTEGRATION_24_25.md](INTEGRATION_24_25.md) để biết phần đã triển khai, CI Docker, lệnh chạy và giới hạn môi trường. Chỉ lưu kết quả tổng bài và một kỳ thi cuối kỳ/course. Frontend auth/LMS/bài tập và Docker runner đã có code thật; worker tự động/QR/gradebook chưa hoàn thành.

## Chốt phạm vi hoàn thiện ngày 25/10/2026 (ưu tiên hơn bản tạm)

- Có cả giữa kỳ và một kỳ thi cuối kỳ/course, tối đa một mỗi loại.
- Chấm test case nhưng chỉ AC được tính là giải đúng bài; WA/RTE/TLE/MLE/CE không cộng số bài AC. Không lưu per-test result.
- Một bài có ít nhất một submission AC hợp lệ được tính một lần, các lần sai sau đó không xóa AC.
- Giảng viên cấu hình số bài và bảng quy đổi số AC → điểm 10. Mặc định 5 bài với thang [0,5,7,8,9,10].
- Trọng số chuyên cần/bài tập/giữa kỳ/cuối kỳ do giảng viên cấu hình, tổng 100%.
- Người dùng tự điền thông tin nhóm, cho phép push và merge main sau nghiệm thu kỹ thuật.
