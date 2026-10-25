# Báo cáo LAN-LMS

NhomXX_LANLMS_Report.docx là bản chỉnh sửa được; PDF để đọc. Thay XX, điền nhóm, giảng viên, thành viên và tỷ lệ đóng góp trước khi nộp. Nguồn nội dung là REPORT_SOURCE.md và script scripts/build_report.py; số liệu ở experiments/results, sơ đồ/biểu đồ ở statics.

Báo cáo theo technical paper trong Instruction.md: Abstract, Keywords, Introduction, Related Work, Problem Definition, Approach, Architecture, Network Design, Implementation, Experimental Setup, Results, Discussion, Contributions, Limitations, Future Work, Conclusion, References và Appendix.

CI Linux không thay cho Windows hoặc LAN vật lý. Compilatio và các bước hành chính cần xác nhận bằng bằng chứng thật. Khi sửa DOCX, xuất/render kiểm tra bảng, hình và ngắt trang trước khi nộp. Cập nhật PDF và commit bản cuối rồi mới đóng gói.

Bản PDF phát hành được xuất bằng LibreOffice trên GitHub Actions Linux theo lựa chọn của người dùng. REPORT/render-provenance.json liên kết đúng commit, run và SHA-256 của DOCX; ảnh trang được kiểm tra trước phát hành. Font thay thế trên Linux có thể khác Word trên máy nộp, nên cần kiểm tra lại sau khi sửa thông tin nhóm. Workflow chạy bước report khi thông điệp commit có [report].
