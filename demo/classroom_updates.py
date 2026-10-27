"""Reusable lesson/assignment content; changes are scoped to the authored classrooms."""
from datetime import timedelta
from sqlalchemy import select
from server.app.models import CalendarEvents, Assignments


def submission_text(key, number, name, title):
    header=f"{title}\nMã sinh viên: {number}\nHọ và tên: {name}\n\n"
    if key=="network":
        return header+(
            "1. Định dạng giao thức\nMỗi bản tin gồm độ dài payload viết thập phân, dấu ':' và payload UTF-8. "
            "Độ dài tính theo byte. Payload request: request_id|ADD|a|b. Response: request_id|OK|sum hoặc request_id|ERROR|code.\n\n"
            "2. Luồng xử lý\nServer giữ bộ đệm riêng cho mỗi client. Đọc đến dấu ':', kiểm tra độ dài không quá 65536, "
            "chờ đủ payload rồi phân tích. Phần thừa giữ lại cho bản tin kế tiếp. recv trả 0 nghĩa là client đã đóng kết nối.\n\n"
            "3. Xử lý lỗi\nTừ chối độ dài âm, ký tự không phải số, số ngoài miền hỗ trợ và thiếu trường. "
            "Timeout đóng kết nối sau khi gửi lỗi nếu vẫn có thể phản hồi. Request trùng id được trả kết quả cũ.\n\n"
            "4. Kế hoạch kiểm thử\nMột khung chia thành ba lần gửi; hai khung ghép trong một lần gửi; client đóng giữa payload; "
            "hai client gửi đồng thời; gửi lại request sau timeout. Ghi log request_id, thời điểm nhận và trạng thái cuối để đối chiếu.\n"
        )
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
        ("BT04 - UDP và cơ chế gửi lại","Thiết kế request_id, ACK, timeout và giới hạn số lần gửi lại cho client UDP. Nộp source, định dạng bản tin và ít nhất 5 tình huống kiểm tra."),
        ("BT05 - HTTP API và xử lý đồng thời","Xây dựng API nhận bài, trả mã yêu cầu và truy vấn trạng thái. Giải thích vì sao tác vụ nặng nên tách khỏi request; nộp sơ đồ luồng và source."),
        ("BT06 - Tích hợp hệ thống Client/Server","Tích hợp hai client với máy chủ trong LAN. Báo cáo giao thức, xử lý lỗi, log trao đổi và hướng dẫn tái lập trên máy khác.")]
        if content["key"]=="network" else [
        ("BT04 - Tìm kiếm nhị phân","Giải truy vấn vị trí đầu tiên và cuối cùng trên dãy đã sắp. Phân tích trường hợp không tìm thấy và phần tử trùng; nộp source và bộ test."),
        ("BT05 - Đồ thị và BFS","Xây dựng danh sách kề và BFS tìm số cạnh ngắn nhất. Kiểm tra đỉnh cô lập, cạnh lặp, s=t và đồ thị không liên thông."),
        ("BT06 - Thuật toán tham lam","Trình bày chứng minh chọn hoạt động kết thúc sớm. Cài đặt chương trình và tự thiết kế phản ví dụ cho cách chọn theo thời điểm bắt đầu.")])
    for index,(title,text) in enumerate(topics):
        if not db.scalar(select(Assignments.id).where(Assignments.course_id==course.id,Assignments.title==title)):
            handout=(title+"\n\n"+text+"\n\nNộp file/ZIP tối đa 20 MiB. Ghi mã sinh viên trong tên file và README.\nThang điểm: đáp ứng yêu cầu 4; giải thích 2; kiểm thử 2; hướng dẫn chạy 2.\n").encode("utf-8")
            db.add(Assignments(course_id=course.id,created_by=teacher.id,title=title,description=text,
                due_at=now+(index+1)*7*86400,allow_resubmit=True,attachment_path=save("assignment_handouts",handout),attachment_filename=f"BT{index+4:02d}.txt"))
