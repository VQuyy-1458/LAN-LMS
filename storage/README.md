# Private storage

- course_materials: tài liệu.
- submissions: bài tập file.
- code_submissions: source code.
- test_cases: input và expected output.
- temporary: dữ liệu tạm.

Tên lưu UUID; DB chỉ giữ metadata/path tương đối. Không public serve thư mục này. Download qua API có phân quyền. Nội dung bị Git ignore; chỉ giữ README và .gitkeep. Không giải nén ZIP hoặc thực thi file upload.

API và worker cần cùng STORAGE_ROOT. Backup/restore cả DB và thư mục này bằng script trong README gốc, có checksum và yêu cầu đích mới. Không đẩy dữ liệu sinh viên hoặc backup lên Git.
