# Import CSV

Header student_id,full_name,date_of_birth,class_name,email; email tùy chọn. UTF-8/BOM, 2 MiB/2.000 dòng. DOB DDMMYYYY đọc dạng chuỗi, không mất số 0 đầu. Chỉ teacher quản lý course được preview/confirm.

Preview hết hạn 15 phút, lưu phía server và scope teacher/course. File lỗi/trùng/xung đột hồ sơ bị từ chối toàn bộ. UI hiển thị số tài khoản mới/cũ và báo lỗi theo dòng; tải được CSV lỗi không có mật khẩu. Confirm có key, kiểm tra lại dưới khóa ghi và commit users/profile/enrollment/key cùng transaction. Retry cùng key/body trả resource cũ; khác body 409; preview hết hạn/đã confirm khác key 409.

Tài khoản mới username=student_id, password=DOB, hash Argon2id và bắt buộc đổi. Không ghi đè password/hồ sơ cũ; trùng enrollment không tạo bản ghi nữa. Không đưa DOB/password vào danh sách lớp/export điểm. CSV mẫu ở client/public/samples/students.csv chỉ chứa dữ liệu giả. Test tại tests/integration/test_day25.py và test_completion.py.
