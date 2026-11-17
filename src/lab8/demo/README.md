# LogiX Lab — UI demo ba kiến trúc

Một UI chạy thật workflow, single agent và orchestrator trên cùng claim/seed. Không cần Node.js, API key hay dependency mới ngoài requirements.txt của lab.

## Khởi động

Từ thư mục gốc repo:

```bash
cd src
python3 -m lab8.demo.web --port 8088
```

Mở [http://127.0.0.1:8088](http://127.0.0.1:8088). Windows có thể dùng `python` thay `python3`. Dừng bằng Ctrl+C. Nếu cổng bận, dùng `--port 8089` và mở URL tương ứng.

## Kịch bản thuyết trình khoảng 5 phút

1. **Hoàn tiền bình thường:** chọn C-001, seed 11, chế độ Chạy một lần. Bấm Chạy so sánh. Cả ba resolved, quote/ledger 35.000đ, một effect và một committed audit. Chỉ ra số model/tool call và chi phí mô phỏng khác nhau.
2. **Chống tin ticket giả:** chọn C-002. Order chỉ trễ 2 ngày nên cả ba denied, không hoàn tiền, dù ticket nói 5 ngày. Chọn tab trace để giải thích nguồn dữ liệu order/policy.
3. **Không vượt approval:** chọn C-007. Quote 35.000đ nhưng host chặn. So với C-008: quote 35.000đ, thực trả chỉ 20.000đ.
4. **Không hoàn trùng:** chọn C-001, chế độ Chạy lại cùng claim. Trace có hai lần; ledger vẫn một effect, một audit.
5. **Crash và phục hồi:** chọn Crash → phục hồi. UI tự dùng C-001. Lần đầu crash sau effect/trước checkpoint; lần hai resolved. Ledger vẫn 35.000đ, không phải 70.000đ. Mở tab từng kiến trúc để xem trace cả hai lần.
6. **Quote đầy đủ:** chọn C-014. Quote 150.000đ, ledger mới 120.000đ vì trước đó đã hoàn 30.000đ. Host tự tính phần chênh lệch.

## Cách UI gọi backend

- Browser gọi GET /api/cases để tải nhãn kịch bản đã biên soạn, không tải ticket/row thô.
- POST /api/compare nhận claim_id, seed và mode (run/retry/crash).
- Server chạy ba worker Python. Mỗi worker có thư mục tạm, SQLite và trace riêng; mỗi lần so sánh bắt đầu từ dữ liệu public mới.
- Chế độ retry/crash dùng lại chính database của worker giữa hai lần, nên kiểm tra được idempotency thật. Database không dùng chung giữa kiến trúc hoặc giữa các request.
- UI nhận RunResult, kết quả kiểm bằng trial_pass và snapshot trace. Không thay kết quả bằng dữ liệu mẫu hardcode.
- Hiển thị cost/model/tool call của **lượt cuối**, không cộng hai lượt khi retry/crash. Sự kiện cho cả hai lượt nằm trong trace.
- Chỉ bind 127.0.0.1. Không phục vụ tùy ý file trong repo. Không có upload, sửa ticket, hay model/API bên ngoài.

## Giới hạn khi giải thích kết quả

MockLLM là giả lập của đề. Single chọn tool bằng callback decide trong code, không phải structured tool-calling của model thật. Quote và approval do code/host quyết định.

Nhãn “Khớp kỳ vọng public” là kiểm kết quả của một claim, không phải điểm benchmark/hidden. Chi phí theo Budget của từng shape; workflow hiện đếm lời gọi host là tool, single/orchestrator không đếm lời gọi host này. Vì vậy không quy toàn bộ chênh lệch chi phí cho topology. Steps trong benchmark là số event trace, không phải latency.

Swarm vẫn được đo trong benchmark nhóm theo yêu cầu đề nhưng không nằm trong UI ba kiến trúc.

## Kiểm thử

Từ src:

```bash
python3 -m pytest -q tests/test_demo_web.py
python3 -m pytest -q -o addopts=
```

Các test UI backend dùng worker thật để kiểm tách database, retry, crash, từ chối, quyền sở hữu và phần tiền chênh lệch. Browser đã được kiểm thao tác chạy hoàn tiền, từ chối và crash/resume.
