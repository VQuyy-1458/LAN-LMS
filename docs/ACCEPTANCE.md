# Kết quả nghiệm thu bản hoàn thiện

Cập nhật ngày 25/10/2026. Phân biệt kiểm thử chức năng bằng dữ liệu giả lập với nghiệm thu trên máy triển khai thật.

| Hạng mục | Bằng chứng | Trạng thái |
|---|---|---|
| Backend trên Windows | `python -m pytest -q`: 65 passed, 9 skipped; các ca Docker không chạy khi chưa có engine | Đạt phần không cần Docker |
| Frontend | ESLint, TypeScript và production build đều thành công | Đạt |
| Docker Linux | [CI bản 8ed2c14](https://github.com/VQuyy-1458/LAN-LMS/actions/runs/40202701438), compiler C/C++/Java, sandbox và pipeline API/worker | Đạt ở mốc CI này; bản cuối cần chạy lại |
| Browser qua Nginx | Dữ liệu giả lập biệt lập: đăng nhập student, dashboard, khóa học, vào thi, gửi C++, thấy xác nhận nhận bài và Pending, giữ nội dung editor | Đã kiểm tra các thao tác này |
| Thực nghiệm HTTP | 324 request đo, 1/5/10/20 client mô phỏng trên cùng máy, raw CSV/JSON | Có bằng chứng; không phải 20 máy thật |
| Thực nghiệm judge | Hai cấu hình 1/2 worker, ba lần mỗi cấu hình, tổng 120 bài được Docker chấm AC | Có raw logs và nguồn CI |
| Báo cáo | Nguồn Markdown, DOCX và biểu đồ tạo từ số đo thật | Đang kiểm tra bản render cuối |
| Gói Source/Report | Script chỉ đóng gói snapshot Git đã commit, không lấy dữ liệu runtime | Chờ báo cáo PDF và commit cuối |
| Docker Desktop Windows | Trước khi khởi động lại, engine chưa sẵn sàng | Chưa nghiệm thu lại |
| Hai máy LAN vật lý | Chưa có log của hai máy độc lập | Chưa thực hiện |
| Thông tin nhóm và Compilatio | Nhóm tự điền và kiểm tra bằng tài khoản học phần | Chưa thực hiện |

Các bài kiểm thử Docker bị bỏ qua trên Windows không được tính là đã đạt. Linux CI không thay thế bằng chứng Docker Windows hoặc LAN vật lý. Lệnh chạy và kịch bản demo ở README mục 10–11 và 21. Khi nghiệm thu LAN, ghi lại máy chủ/client, thời điểm, địa chỉ truy cập, kết quả `scripts.check_lan`, nhận bài, chấm và phục hồi kết nối.
