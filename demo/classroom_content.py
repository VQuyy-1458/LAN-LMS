"""Original teaching notes for programming and algorithms classrooms."""
COURSES = [
    {
        "key": "programming", "code": "LT-2026-01", "name": "Lập trình C, C++ và Java",
        "summary": "Nền tảng C17, C++17 và Java 17: nhập xuất, kiểu dữ liệu, điều kiện, vòng lặp, hàm, mảng và chuỗi. Thực hành giải bài theo input/output và kiểm thử chương trình.",
        "lessons": ["Môi trường biên dịch và nhập xuất", "Kiểu dữ liệu và cấu trúc điều kiện", "Vòng lặp và số học", "Hàm và phân rã bài toán", "Mảng và chuỗi", "Đọc ghi file và ôn tập tổng hợp"],
        "sections": [
            ("Biên dịch và nộp bài", [
                "Chọn đúng ngôn ngữ: C17, C++17 hoặc Java 17. Java dùng public class Main, không khai báo package. Đọc stdin và ghi stdout trừ khi đề yêu cầu file.",
                "C dùng scanf/printf; C++ dùng cin/cout; Java dùng BufferedReader hoặc Scanner. Không in lời nhắc nhập dữ liệu. AC mới được tính một câu đúng; điểm theo bảng quy đổi giảng viên cấu hình."]),
            ("Kiểu dữ liệu và điều kiện", [
                "Dùng long long trong C/C++ hoặc long trong Java khi tổng vượt miền số nguyên 32 bit. Kiểm tra biên bằng nhau, số âm và số không.",
                "Viết if/else rõ ràng, không dùng phép gán thay so sánh. Kiểm tra mẫu số trước phép chia; chú ý chia nguyên và thứ tự ưu tiên toán tử."]),
            ("Vòng lặp và số học", [
                "Dùng for khi biết số lần lặp, while khi dừng theo điều kiện. Xác định bất biến và cập nhật biến điều khiển để tránh vòng lặp vô hạn.",
                "Kiểm tra số nguyên tố bằng thử ước tới căn bậc hai; tìm ước chung lớn nhất bằng Euclid. Tách chữ số bằng chia và lấy dư; xử lý riêng số 0."]),
            ("Hàm và kiểm thử", [
                "Mỗi hàm thực hiện một nhiệm vụ rõ ràng. Xác định đầu vào, đầu ra và điều kiện hợp lệ. Tránh thay đổi biến toàn cục khi không cần thiết.",
                "Tự thiết kế test nhỏ, giá trị biên và phần tử trùng. CE là lỗi biên dịch, WA là sai kết quả, RTE là lỗi khi chạy, TLE là quá thời gian."]),
            ("Mảng và chuỗi", [
                "Chỉ số bắt đầu từ 0; không truy cập ngoài mảng. Khởi tạo cực trị bằng phần tử đầu để xử lý dãy toàn âm.",
                "Đọc cả dòng bằng fgets, getline hoặc BufferedReader. Giữ dấu cách và xử lý chữ hoa thường theo đúng yêu cầu đề. Không tự chuẩn hóa dữ liệu khi đề không cho phép."]),
            ("File và đánh giá", [
                "Đề yêu cầu file thì dùng đúng tên phân biệt hoa thường; không dùng đường dẫn tuyệt đối. Bài thông thường vẫn dùng stdin/stdout.",
                "Bài tập file nộp source, README và ít nhất 5 test. Trọng số chuyên cần/bài tập/giữa kỳ/cuối kỳ mặc định 10/10/10/70, giảng viên được cấu hình."]),
        ],
        "assignments": [
            ("BT01 - Nhập xuất và kiểu dữ liệu", "Tính tổng, hiệu, tích hai số nguyên bằng C, C++ hoặc Java. Giải thích lựa chọn kiểu dữ liệu; kiểm tra số âm, 0 và số lớn. Nộp ZIP gồm source, README và 5 testcase.", -2),
            ("BT02 - Điều kiện và vòng lặp", "Kiểm tra số nguyên tố, tính tổng chữ số và tìm ước chung lớn nhất. Trình bày thuật toán; kiểm tra 0, 1 và hai số bằng nhau. Nộp source và báo cáo PDF.", 3),
            ("BT03 - Hàm, mảng và chuỗi", "Tách chương trình thành hàm xử lý mảng và chuỗi: cực trị, tần suất, chuỗi đối xứng. Nộp ZIP kèm hướng dẫn biên dịch và bộ test biên.", 10),
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
