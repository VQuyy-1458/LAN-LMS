# Kiến trúc và giao tiếp LAN-LMS

## Thành phần

Một máy chủ giữ API, SQLite và private storage. Nginx là public origin duy nhất; Next.js phục vụ UI. Uvicorn chạy một process với I/O bất đồng bộ và thread pool cho endpoint đồng bộ. Các worker là tiến trình riêng, không chặn request lúc compiler/test chạy. Không expose Docker socket cho browser/API.

```mermaid
sequenceDiagram
    participant S as Student Browser
    participant N as Nginx
    participant A as FastAPI
    participant D as SQLite
    participant W as Judge Worker
    participant C as Docker Sandbox
    S->>N: POST source + cookie/CSRF/key
    N->>A: REST request
    A->>D: BEGIN IMMEDIATE; submission + job + key
    D-->>A: COMMIT
    A-->>S: 202 Pending + submission id
    W->>D: Claim + attempt token + lease
    W->>C: Compile once; fresh container per test
    W->>D: Conditional result + outbox COMMIT
    A->>D: Read durable outbox
    A-->>S: WebSocket submission.updated
    S->>A: GET /submissions/id after reconnect
    A-->>S: Authoritative snapshot
```

## Kết nối và trạng thái

HTTP là request/response; download có Content-Disposition attachment. WS upgrade qua Nginx và giữ cookie/Origin xác thực; heartbeat/ACK phát hiện mất kết nối, đóng queue chậm. Browser không gửi lệnh chấm hoặc đổi điểm qua WS. WebSocket chỉ báo thay đổi; REST trả snapshot sau reconnect. Một API process là ràng buộc triển khai, không chạy --workers 2.

## Đồng thời và độ bền

SQLite WAL/FK/busy_timeout, mỗi request có Session riêng. Transaction ghi ngắn bằng BEGIN IMMEDIATE tuần tự hóa tranh chấp; idempotency và resource commit cùng nhau. Không giữ DB lock trong lúc biên dịch/chạy test. Worker claim job nguyên tử, lease 60 giây/renew 10 giây, retry tối đa 3; attempt token và lease chặn kết quả từ worker cũ. Điều này đảm bảo một kết quả cuối được chấp nhận, không đảm bảo chương trình chỉ được thực thi đúng một lần khi worker chết.

Private source được ghi trước khi metadata commit; rollback dọn file mới. API chỉ trả 202 sau khi lưu source và job. Sự kiện nằm cùng transaction kết quả để worker không cần gọi API qua cổng công khai. Queue/outbox lưu DB; WS là delivery best effort, REST vẫn đúng khi mất event.

## Sandbox

Compiler và chương trình đều chạy nonroot trong Docker Linux, network none/read-only/cap-drop/no-new-privileges/resource limits. Compiler được mount source read-only và artifacts riêng; mỗi test chỉ mount artifacts read-only và input, không có expected output/DB/secret. Supervisor trả output giới hạn cho host so sánh. Source/test path do server tạo, không nhận đường dẫn từ browser.

## Giới hạn và bằng chứng

Docker/SQLite là các thành phần được kế thừa, không phải thuật toán nhóm tự phát minh. Novelty ở mức tích hợp và đánh giá 1/2 worker, xem experiments/RESULTS.md. Các test tự động chứng minh nhiều request mô phỏng; không tương đương hai máy vật lý LAN. HTTP LAN và QR có giới hạn mô tả tại README.
