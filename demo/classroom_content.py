"""Original Vietnamese teaching notes and assessment briefs for the sample courses."""
COURSES = [
    {
        "key": "network", "code": "LTM-2026-01", "name": "Lập trình mạng",
        "summary": "Nghiên cứu mô hình Client/Server, socket TCP/UDP, HTTP và WebSocket. Học phần kết hợp lý thuyết, thực hành tại phòng máy, bài tập và đánh giá lập trình.",
        "lessons": ["Mô hình Client/Server và địa chỉ mạng", "Socket TCP, framing và xử lý ngắt kết nối", "UDP, timeout và truyền lại", "HTTP: request, response và mã trạng thái", "WebSocket và cập nhật thời gian thực", "Tích hợp, kiểm thử tải và triển khai LAN"],
        "sections": [
            ("Mục tiêu và cách học", [
                "Sau khóa học, sinh viên phân biệt TCP/UDP, xây dựng dịch vụ nhiều client, mô tả giao thức ứng dụng và kiểm tra lỗi mất kết nối.",
                "Mỗi buổi: đọc tài liệu, điểm danh QR, thực hành theo cặp, gửi bài tập file và luyện code. Các bài code mô phỏng xử lý dữ liệu mạng; chương trình nộp không cần tự tạo socket.",
                "Đánh giá: chuyên cần 10%, bài tập 10%, trung bình các bài giữa kỳ 10%, cuối kỳ 70%. Đề test chỉ luyện tập. Teacher có thể cấu hình lại trước khi dùng cho lớp thật.",
                "Bài làm C17/C++17/Java 17 phải theo đúng input/output. Java dùng public class Main, không khai báo package. Chỉ AC toàn bộ testcase được tính là giải đúng."]),
            ("TCP và giao thức đóng khung", [
                "TCP cung cấp luồng byte có thứ tự; một lần send không tương ứng một lần recv. Client phải có bộ đệm và quy tắc xác định ranh giới bản tin.",
                "Ví dụ giao thức length-prefix: 5:hello3:LAN. Đọc phần độ dài đến dấu :, chờ đủ payload rồi giữ phần thừa cho khung kế tiếp. Khung thiếu phải chờ thêm hoặc báo lỗi khi kết nối đóng.",
                "Quy định giới hạn độ dài bản tin trước khi cấp phát bộ nhớ. Mọi bản tin nên có loại thao tác, request_id và dữ liệu. Response phải phân biệt lỗi giao thức với lỗi nghiệp vụ.",
                "Thực hành: gửi một khung thành ba đoạn; gửi hai khung trong một lần; ngắt kết nối giữa payload. Máy chủ phải tránh treo và không ghép nhầm bản tin."]),
            ("UDP, timeout và tính lặp an toàn", [
                "UDP giữ ranh giới datagram nhưng không đảm bảo đến nơi, thứ tự hay tránh trùng. Dùng sequence number và ACK nếu ứng dụng cần theo dõi việc nhận.",
                "Timeout quá ngắn gây gửi lại nhiều; quá dài làm người dùng chờ. Thử giới hạn số lần gửi lại, tăng thời gian chờ và trả trạng thái cuối rõ ràng.",
                "Gửi lại không đồng nghĩa thực hiện lại nghiệp vụ. Ví dụ nộp bài dùng Idempotency-Key để cùng một yêu cầu chỉ tạo một submission dù response bị mất.",
                "Bài tập suy nghĩ: server đã lưu bài nhưng client mất kết nối trước khi nhận HTTP 202. Client phải truy vấn hoặc retry cùng key thay vì tạo bài nộp mới vô hạn."]),
            ("HTTP và WebSocket trong LAN-LMS", [
                "HTTP phù hợp các thao tác có kết quả rõ như đăng nhập, tải tài liệu và gửi source. API chấp nhận bài vào hàng đợi rồi trả 202 cùng submission_id; không giữ request chờ compiler.",
                "WebSocket giữ kết nối để báo submission.updated, attendance.updated và thay đổi phiên thi. Cookie, Origin và quyền khóa học vẫn phải được kiểm tra.",
                "WebSocket có thể mất sự kiện khi ngắt mạng. Sau reconnect, client gọi REST lấy trạng thái hiện tại; dữ liệu trong SQLite là nguồn quyết định.",
                "Mở DevTools/Network: quan sát request nộp source, response 202, frame WebSocket, chuỗi Pending -> Compiling -> Running -> AC/WA. Không gửi testcase ẩn hoặc Docker socket tới trình duyệt."]),
            ("Kiểm thử và triển khai", [
                "Kiểm thử ít nhất: hai client đồng thời, source không biên dịch, vòng lặp vô hạn, output sai, mất mạng rồi nộp lại, hết giờ và nộp sớm.",
                "Một máy chủ giữ API, SQLite và private storage; Nginx phục vụ cùng origin. Các máy sinh viên cùng LAN chỉ cần trình duyệt và dùng IP máy chủ mới.",
                "Docker sandbox giới hạn CPU, RAM, tiến trình và tắt mạng. Không chạy source sinh viên trực tiếp trên máy chủ. Theo dõi hàng đợi và trạng thái worker trước giờ thi.",
                "Khi chuyển phòng: xuất gói khóa, dừng nhận bài trên máy cũ, chạy máy mới rồi nhập gói. Kiểm tra roster, file, giờ thi, điểm và thử một bài AC thật trước khi dùng."]),
            ("Bài thực hành tổng hợp", [
                "Xây dựng TCP server nhận bản tin có độ dài; dùng hai client gửi đồng thời. Mỗi response chứa request_id, trạng thái và thời gian xử lý.",
                "Tự thiết kế sơ đồ luồng, định dạng message, timeout và cách phát hiện client ngắt kết nối. Không dùng sleep cố định để giả lập việc đồng bộ.",
                "Nộp ZIP: source/, README.txt, protocol.txt, test-log.txt và ảnh kết quả. README phải có lệnh chạy server/client, IP/cổng, dependency và các tình huống lỗi đã thử.",
                "Rubric 10 điểm: đúng giao thức 3; nhiều client 2; xử lý lỗi 2; kiểm thử có bằng chứng 2; hướng dẫn tái lập 1. Không ghi số liệu chưa đo."]),
        ],
        "assignments": [
            ("BT01 - Đặc tả giao thức TCP", "Soạn protocol.txt cho dịch vụ cộng hai số dùng TCP. Quy định framing, request_id, lỗi dữ liệu và ví dụ trao đổi. Nộp ZIP chứa đặc tả và README chạy thử.", -2),
            ("BT02 - Quan sát HTTP và WebSocket", "Ghi lại một lượt nộp code và một lần điểm danh QR. Giải thích HTTP 202, submission_id, WebSocket event và thao tác khôi phục sau mất mạng. Nộp PDF hoặc ZIP ảnh kèm phân tích.", 3),
            ("BT03 - TCP server nhiều client", "Xây dựng server xử lý tối thiểu hai client đồng thời. Thử bản tin chia nhỏ, ghép nhiều khung, timeout và ngắt kết nối. Nộp source và hướng dẫn theo rubric tài liệu.", 10),
        ],
    },
    {
        "key": "algorithms", "code": "CTDL-2026-01", "name": "Cấu trúc dữ liệu và Giải thuật",
        "summary": "Phát triển tư duy thuật toán qua mảng, chuỗi, stack, tìm kiếm, prefix sum, đồ thị và tham lam. Thực hành C/C++/Java, phân tích độ phức tạp và kiểm thử chương trình.",
        "lessons": ["Độ phức tạp, kiểu dữ liệu và nhập/xuất", "Mảng, sắp xếp và tìm kiếm nhị phân", "Chuỗi và cấu trúc stack", "Prefix sum và đọc/ghi file", "Đồ thị: BFS và đường đi", "Thuật toán tham lam và ôn tập tổng hợp"],
        "sections": [
            ("Mục tiêu và quy tắc nộp bài", [
                "Chọn cấu trúc dữ liệu phù hợp, phân tích độ phức tạp, xử lý trường hợp biên và cài đặt bằng C17/C++17 hoặc Java 17.",
                "Đọc kỹ ràng buộc trước khi chọn kiểu dữ liệu. Tổng 100000 số có độ lớn 10^9 cần số nguyên 64 bit: long long trong C/C++, long trong Java.",
                "Output phải theo định dạng đề, không in lời nhắc như Nhap n. Không đọc dữ liệu từ đường dẫn riêng trên máy cá nhân.",
                "Mỗi câu có ví dụ công khai và testcase ẩn. AC mới được tính là một câu đúng; điểm thi theo bảng quy đổi teacher đặt. Chuyên cần/bài tập/giữa kỳ/cuối kỳ mặc định 10/10/10/70."]),
            ("Mảng, sắp xếp và tìm kiếm", [
                "Quét dãy một lần để tính tổng, cực trị hoặc thống kê. Khởi tạo giá trị lớn nhất bằng phần tử đầu tiên thay vì 0 khi dãy có thể toàn âm.",
                "Sắp xếp O(n log n) rồi loại trùng. Kiểm tra n=1, các số đều bằng nhau, dãy đã sắp, dãy ngược và giá trị biên.",
                "Tìm kiếm nhị phân yêu cầu dãy có thứ tự. Muốn vị trí đầu tiên của x cần tìm phần tử đầu >=x rồi kiểm tra bằng x.",
                "Với n=100000, q=100000, quét toàn dãy cho từng truy vấn có thể cần 10^10 phép so sánh. Sắp xếp một lần và tìm nhị phân giảm đáng kể công việc."]),
            ("Chuỗi, stack và bất biến", [
                "Xử lý chuỗi cả dòng cần getline/fgets/BufferedReader thay vì chỉ đọc một từ. Phải xem đề có cho phép dòng rỗng hay dấu cách không.",
                "Kiểm tra đối xứng: chuẩn hóa theo đúng đề rồi dùng hai con trỏ hoặc đảo chuỗi. Không tự bỏ ký tự nếu đề không yêu cầu.",
                "Ngoặc lồng nhau dùng stack. Gặp ngoặc mở thì đẩy vào; gặp ngoặc đóng phải khớp đỉnh stack; cuối cùng stack rỗng.",
                "Bất biến: stack chứa các ngoặc mở chưa được đóng của tiền tố đã đọc. Chuỗi ([)] sai dù tổng từng loại ngoặc cân bằng."]),
            ("Prefix sum và file input/output", [
                "Đặt S[0]=0, S[i]=S[i-1]+a[i]. Tổng đoạn [L,R] bằng S[R]-S[L-1], trả lời O(1) sau tiền xử lý O(n).",
                "Kiểm tra L=1, L=R, R=n và số âm. Mảng S cần kiểu 64 bit ngay từ phép cộng, không ép kiểu sau khi đã tràn.",
                "Đề A07 dùng DATA.INP và RESULT.OUT. C/C++ có thể freopen hai file; Java dùng FileInputStream và PrintWriter. Tên file phân biệt hoa/thường trong Docker Linux.",
                "Không hardcode dữ liệu ví dụ. Bộ chấm tạo file trong thư mục làm việc và kiểm tra nội dung file output; in ra console không thay thế file output của đề."]),
            ("BFS, gộp đoạn và tham lam", [
                "BFS dùng queue và khoảng cách khởi tạo -1. Đánh dấu khi đưa vào queue để mỗi đỉnh chỉ xử lý một lần. Đồ thị không trọng số cho khoảng cách ngắn nhất theo số cạnh.",
                "Gộp đoạn: sắp theo đầu trái, so với đoạn cuối đã gộp. Đề quy định đoạn đóng có chung đầu mút được gộp; hai đoạn cách nhau một đơn vị không tự gộp.",
                "Chọn nhiều hoạt động nhất: sắp theo thời gian kết thúc, chọn hoạt động bắt đầu không sớm hơn mốc kết thúc hiện tại. Không chọn theo thời điểm bắt đầu sớm nhất.",
                "Khi chứng minh tham lam, giải thích vì sao lựa chọn kết thúc sớm để lại nhiều thời gian nhất cho phần còn lại; kiểm tra phản ví dụ của những quy tắc khác."]),
            ("Quy trình tự kiểm tra", [
                "Bước 1: viết lại input/output bằng lời của mình. Bước 2: liệt kê biên. Bước 3: chọn thuật toán và ước lượng thời gian/bộ nhớ. Bước 4: cài đặt và thử dữ liệu nhỏ.",
                "So sánh thuật toán nhanh với lời giải vét cạn trên nhiều bộ dữ liệu nhỏ để tìm sai lệch. Giữ seed ngẫu nhiên để tái lập lỗi.",
                "WA: kiểm tra logic và định dạng; CE: đọc lỗi biên dịch; RTE: kiểm tra chỉ số và chia 0; TLE: xem độ phức tạp; MLE: xem cấu trúc lưu trữ.",
                "Nộp bài tập file kèm phân tích độ phức tạp, ít nhất 5 test tự soạn và giải thích 2 trường hợp biên. Không coi việc chạy đúng ví dụ là đã đúng toàn bộ bài."]),
        ],
        "assignments": [
            ("BT01 - Phân tích độ phức tạp", "Phân tích thời gian/bộ nhớ của quét mảng, sắp xếp và tìm nhị phân. Cho ví dụ khiến thuật toán O(nq) không phù hợp. Nộp báo cáo PDF hoặc DOCX.", -2),
            ("BT02 - Stack và chuỗi", "Cài đặt kiểm tra ngoặc, tự thiết kế tối thiểu 8 testcase gồm chuỗi rỗng, sai loại ngoặc và lồng sâu. Nộp ZIP gồm source, test và README.", 3),
            ("BT03 - Prefix sum và BFS", "Giải thích bất biến prefix sum và BFS, triển khai hai bài, phân tích độ phức tạp. Nộp ZIP kèm test biên và hướng dẫn biên dịch C/C++/Java.", 10),
        ],
    },
]
