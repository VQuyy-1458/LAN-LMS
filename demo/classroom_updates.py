"""Reusable lesson/assignment content; changes are scoped to the authored classrooms."""
from datetime import timedelta
from sqlalchemy import select
from server.app.models import CalendarEvents, Assignments


def submission_text(key, number, name, title):
    header=f"{title}\nMã sinh viên: {number}\nHọ và tên: {name}\n\n"
    return header+(
        "1. Phân tích độ phức tạp\nQuét n phần tử tính tổng cần O(n) thời gian và O(1) bộ nhớ phụ. "
        "Sắp xếp thường dùng O(n log n); tìm một giá trị trên dãy tăng bằng nhị phân cần O(log n). "
        "Với q truy vấn, cách quét toàn dãy cho từng truy vấn là O(nq).\n\n"
        "2. Kiểu dữ liệu\nTổng 100000 số có độ lớn 10^9 có thể đạt 10^14 nên cần long long trong C/C++, long trong Java. "
        "Khởi tạo cực trị bằng phần tử đầu để xử lý dãy toàn âm.\n\n"
        "3. Stack kiểm tra ngoặc\nGặp ngoặc mở thì đưa vào stack. Ngoặc đóng phải khớp phần tử trên đỉnh. "
        "Kết thúc chuỗi, stack phải rỗng. Chuỗi ([)] là phản ví dụ cho cách chỉ đếm từng loại ngoặc.\n\n"
        "4. Trường hợp kiểm tra\nDãy một phần tử; toàn số âm; các phần tử bằng nhau; số lớn; không tìm thấy khóa; "
        "chuỗi rỗng; ngoặc đóng đầu tiên; ngoặc lồng sâu. Đối chiếu thuật toán nhanh với vét cạn trên dữ liệu nhỏ.\n"
    )


def enrich(db,course,teacher,content,anchor,now,save):
    for week,title in enumerate(content["lessons"]):
        name=f"Thực hành tuần {week+1}: {title}"
        if not db.scalar(select(CalendarEvents.id).where(CalendarEvents.course_id==course.id,CalendarEvents.title==name)):
            start=(anchor+timedelta(days=(week-2)*7+2)).timestamp()
            db.add(CalendarEvents(course_id=course.id,created_by=teacher.user_id,title=name,event_type="lesson",
                description="Thực hành tại phòng máy. Chuẩn bị nội dung chuyên đề, nộp báo cáo và điểm danh bằng mã QR của buổi học.",starts_at=start,ends_at=start+7200))
    for index,(title,days,text) in enumerate([
        ("Hướng dẫn báo cáo thực hành",1,"Báo cáo gồm thiết kế, cách chạy, dữ liệu kiểm tra và nhận xét kết quả. Nộp file PDF hoặc ZIP trong mục Bài tập."),
        ("Trao đổi bài tập giữa kỳ",8,"Tổng hợp câu hỏi về bài tập và các tình huống lỗi trước buổi trao đổi. Kiểm tra lịch giữa kỳ trong mục Thi lập trình."),
        ("Ôn tập cuối kỳ",22,"Ôn tập các chuyên đề đã học. Kiểm tra tài khoản, ngôn ngữ biên dịch và quy định giữ màn hình thi trước kỳ thi cuối kỳ.")]):
        if not db.scalar(select(CalendarEvents.id).where(CalendarEvents.course_id==course.id,CalendarEvents.title==title)):
            start=now+days*86400
            db.add(CalendarEvents(course_id=course.id,created_by=teacher.user_id,title=title,description=text,event_type="announcement",starts_at=start,ends_at=start+3600))
    topics=([
        ("BT04 - Hàm và đệ quy","Cài đặt hàm tính giai thừa và gcd; phân tích điều kiện dừng và test biên. Nộp source cùng báo cáo."),
        ("BT05 - Mảng và tìm kiếm","Tìm cực trị và vị trí phần tử trong mảng; kiểm tra mảng một phần tử, trùng và toàn số âm."),
        ("BT06 - Chuỗi và file dữ liệu","Đọc một dòng văn bản, đếm từ và thống kê ký tự. Nộp source, file input/output và README.")]
        if content["key"]=="programming" else [
        ("BT04 - Tìm kiếm nhị phân","Tìm vị trí đầu và cuối trên dãy đã sắp; phân tích không tìm thấy và phần tử trùng."),
        ("BT05 - Đồ thị và BFS","Dùng danh sách kề và BFS tìm đường đi ngắn nhất; kiểm tra đỉnh cô lập, cạnh lặp và s=t."),
        ("BT06 - Thuật toán tham lam","Chứng minh cách chọn hoạt động kết thúc sớm và so sánh với các cách chọn khác.")])
    for index,(title,text) in enumerate(topics):
        if not db.scalar(select(Assignments.id).where(Assignments.course_id==course.id,Assignments.title==title)):
            handout=(title+"\n\n"+text+"\n\nNộp file/ZIP tối đa 20 MiB. Ghi mã sinh viên trong tên file và README.\nThang điểm: đáp ứng yêu cầu 4; giải thích 2; kiểm thử 2; hướng dẫn chạy 2.\n").encode("utf-8")
            db.add(Assignments(course_id=course.id,created_by=teacher.id,title=title,description=text,
                due_at=now+(index+1)*7*86400,allow_resubmit=True,attachment_path=save("assignment_handouts",handout),attachment_filename=f"BT{index+4:02d}.txt"))
