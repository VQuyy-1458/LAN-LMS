# Kết quả nghiệm thu bản hoàn thiện

Cập nhật ngày 26/10/2026. Bản phát hành được tích hợp vào develop; main được giữ nguyên theo yêu cầu mới nhất. Phân biệt kiểm thử bằng dữ liệu giả lập với nghiệm thu trên máy triển khai thật.

| Hạng mục | Bằng chứng | Trạng thái |
|---|---|---|
| Backend trên Windows | `python -m pytest -q`: 65 passed, 9 skipped; các ca Docker không chạy khi chưa có engine | Đạt phần không cần Docker |
| Frontend | ESLint, TypeScript và production build đều thành công | Đạt |
| Docker Linux | [CI 5caa298](https://github.com/VQuyy-1458/LAN-LMS/actions/runs/40223686336): 74 passed, gồm compiler C/C++/Java, sandbox và pipeline API/worker; các commit sau chỉ sửa tài liệu/báo cáo | Đạt toàn bộ bộ kiểm thử tại mốc này |
| Browser qua Nginx | Dữ liệu giả lập biệt lập: đăng nhập student/teacher, dashboard, khóa học, vào thi, gửi C++, xác nhận nhận bài và Pending, giữ nội dung editor; teacher tạo QR, student điểm danh thành công; logout | Đã kiểm tra các thao tác này |
| Mobile | Viewport 390 × 844: nút đăng xuất hiển thị; body không tràn ngang | Đạt tại kích thước đã kiểm tra |
| Thực nghiệm HTTP | 324 request đo, 1/5/10/20 client mô phỏng trên cùng máy, raw CSV/JSON | Có bằng chứng; không phải 20 máy thật |
| Thực nghiệm judge | Một/hai worker, ba lần mỗi cấu hình, tổng 120 bài được Docker chấm AC | Có raw logs và nguồn CI |
| Báo cáo | DOCX và PDF từ cùng nội dung; render_docx.py trên Linux CI, kiểm tra ảnh từng trang; metadata có commit và SHA-256 | Xem REPORT/render-provenance.json cho đúng bản cuối |
| Đóng gói | Ba kiểm thử snapshot đã commit, loại file riêng tư và chống ghi đè đều đạt | Script đạt; tạo gói từ commit phát hành theo README |
| Docker Desktop Windows | Kiểm tra lại sau khởi động máy vẫn chưa có engine hoạt động | Chưa nghiệm thu chấm trên Windows |
| Hai máy LAN vật lý | Chưa có log của hai máy độc lập | Chưa thực hiện |
| Thông tin nhóm và Compilatio | Nhóm tự điền và kiểm tra bằng tài khoản học phần | Chưa thực hiện |

Linux CI không thay thế bằng chứng Docker Windows hoặc LAN vật lý. Lệnh chạy và kịch bản demo ở README mục 10–11 và 21. Khi nghiệm thu LAN, ghi lại máy chủ/client, thời điểm, địa chỉ truy cập, kết quả scripts.check_lan, nhận bài, chấm và phục hồi kết nối. Sau khi sửa thông tin nhóm, xuất và kiểm tra lại báo cáo trên máy dùng để nộp.
