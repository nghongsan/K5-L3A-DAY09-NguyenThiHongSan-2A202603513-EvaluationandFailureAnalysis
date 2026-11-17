# Báo cáo cá nhân — 2A202603497_NguyenThiThanhBinh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Thanh Bình.
- MSSV: 2A202603497.
- Lớp: L3A.
- Nhóm: Tourist.
- GitHub: [ThanhBinh101](https://github.com/ThanhBinh101).
- Nhánh implementation cá nhân: `03497-NguyenThiThanhBinh`, tách từ `Single`.

## 2. Phần việc phụ trách

- Triển khai ban đầu **Shape B — single agent**, thay stub bằng vòng ReAct giới hạn tám lượt tại `src/lab8/shapes/single.py`, với hỗ trợ OpenAI Codex.
- Kiểm chứng implementation bằng test public, kết quả ledger/audit, benchmark và demo; các lệnh kiểm chứng trong phiên được Codex thực hiện theo yêu cầu.
- Bổ sung UI chạy cùng claim qua workflow, single và orchestrator; thêm test backend demo, hướng dẫn thuyết trình và soạn báo cáo từ bằng chứng thực tế.
- Khi tích hợp, gỡ marker conflict trong `single.py`, giữ implementation và xử lý crash trace đã có. Workflow/orchestrator và phần hoàn thiện crash trace/test riêng của thành viên khác được giữ đúng phạm vi đóng góp, không nhận là phần tự viết mới.

## 3. Đóng góp cụ thể

### Implementation single agent

- Dùng `get_claim_view` đọc claim, trả `failed` nếu không tồn tại và `needs_info` nếu thiếu mã đơn; không tự đoán mã đơn từ ticket.
- Dùng `run_react(max_steps=8, worker=True)`. Callback `decide` nhận observation, chọn `lookup_order` để kiểm quyền sở hữu, rồi `compute_compensation` khi đơn hợp lệ. Nếu đơn không hiển thị, trả `escalated`.
- Tính quote từ dữ liệu order và policy hiện hành. Nội dung ticket, kể cả lời nhắc bỏ qua policy hoặc số ngày trễ không đúng, không được dùng để thay đổi quyền lợi.
- Chỉ gọi `durability.issue_refund` bằng code bên ngoài vòng ReAct. Host kiểm approval, trần theo đơn và idempotency; agent trong vòng lặp chỉ có quyền đọc.
- Truyền **quote đầy đủ**, giữ `proposal_amount` là quyền lợi trước khi giới hạn. Ví dụ C-014: quote 150.000đ, đã hoàn 30.000đ, host chỉ ghi thêm 120.000đ. Nếu shape tự trừ trước, host có thể trừ hai lần.
- Dùng `finish` trả kết quả từ ledger/audit thật và ghi trace ở các nhánh return. Không ghi nguyên ticket, secret, header hoặc dữ liệu khách vào trace. Đóng kết nối bằng `finally`, truyền `crash_at` cho host để kiểm phục hồi.
- Gọi MockLLM và cộng usage vào Budget. MockLLM starter không có structured tool-calling; việc chọn tool ở callback là code kiểm soát, không phải model thật tự chọn mọi bước.

### UI demo và kiểm thử bổ sung

- Thêm `src/lab8/demo/web.py` và giao diện HTML/CSS/JS tại `src/lab8/demo/ui/`, chạy local, không cần API key hoặc Node.js.
- Hiển thị ba kết quả cạnh nhau: status, quote, tiền thực ghi, model/tool calls, chi phí mô phỏng, số refund/audit và trace từng kiến trúc.
- Tách worker, thư mục tạm, SQLite và trace cho từng kiến trúc để tránh ảnh hưởng chéo. Trong chế độ retry/crash, hai lượt của cùng kiến trúc dùng lại database để kiểm chống hoàn trùng thật.
- Thêm `src/tests/test_demo_web.py`: 15 trường hợp kiểm hoàn tiền, từ chối, sai chủ đơn, approval, tiền chênh lệch, retry, crash/resume, không rò marker nhạy cảm và input không hợp lệ.
- Viết hướng dẫn demo tại `src/lab8/demo/README.md` và báo cáo nhóm tại `report/team/group_report.md`.

### Phối hợp và ranh giới đóng góp

Commit ban đầu `1ce29a9` triển khai single agent, chưa có test mới và chưa có bước flush trace ngay lúc crash. Theo báo cáo của Lưu Đăng Tuấn trên nhánh `Single`, anh Tuấn bổ sung xử lý ghi trace trước khi phát lại `InjectedCrash` và bộ `src/tests/test_single_shape.py`. Phần này được ghi nhận cho anh Tuấn; bản tích hợp giữ lại sau khi gỡ conflict. Việc mô tả cơ chế đó trong báo cáo nhằm giải thích hệ thống hiện tại, không chuyển quyền tác giả đóng góp.

Host, `durability.py`, `policy.py`, `metrics.py`, config và dữ liệu đề không bị sửa để làm đẹp kết quả.

## 4. Bằng chứng

### Nhánh, commit và file

- Nhánh đã push: `03497-NguyenThiThanhBinh`.
- Commit single ban đầu: [`1ce29a9 — feat(lab8): implement bounded single-agent claim processing`](https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents/commit/1ce29a9), thay đổi `src/lab8/shapes/single.py`.
- Phần UI/test/báo cáo được lưu tại commit `3c3f9b2` và đã merge vào main; không gán các file bổ sung cho commit single ban đầu `1ce29a9`.
- [Manifest bằng chứng](evidence_manifest.json) hiện đã tích hợp trên main, ghi hash code/report sau merge. Nhánh cá nhân ban đầu chỉ chứa implementation và báo cáo; UI được tích hợp qua nhánh local riêng.

### Kết quả đã kiểm chứng

| Kiểm tra                             | Kết quả                                     | Phạm vi                                                              |
| ------------------------------------ | ------------------------------------------- | -------------------------------------------------------------------- |
| Test riêng single ban đầu            | 62 passed                                   | Bộ public dành cho Shape B                                           |
| Test host ở thời điểm commit ban đầu | 54 passed                                   | Bộ host gốc                                                          |
| Toàn bộ test bản tích hợp có UI      | 442 passed                                  | Test chung của repo, không phải 442 test cá nhân tự viết             |
| Benchmark single                     | 70/70 trial pass                            | 14 claim public × seed 11,22,33,44,55                                |
| Pass rate / pass^5                   | 1,0 / 1,0                                   | Chỉ trên public                                                      |
| Seed min–max / variance              | 1,0–1,0 / 0,0                               | Theo benchmark đã sinh                                               |
| Cost/success                         | 29,105714 VND mô phỏng                      | Theo Budget hiện tại của single                                      |
| Crash suite chính thức               | 20/20                                       | Chủ yếu kiểm host/swarm; không gọi đây là 20 điểm crash riêng single |
| Demo C-001, seed 11                  | resolved, effect 35.000đ, 1 refund, 1 audit | 3 model calls, 3 tool calls                                          |
| Hidden                               | Chưa đo                                     | Chưa có dữ liệu/nhãn để kết luận đạt ngưỡng                          |

Nguồn: [benchmark.json](../../src/reports/benchmark.json), [crash.json](../../src/reports/crash.json) và [báo cáo nhóm](group_report.md). Run id dẫn chứng: `R-single-C-001-s11`. Trace runtime không commit theo quy định.

Các lệnh để chạy lại từ `src/`:

```bash
python3 -m pytest -q -m student -o addopts= -k 'single and not workflow and not orchestrator and not swarm'
python3 -m pytest -q tests/test_demo_web.py
python3 -m pytest -q -o addopts=
python3 -m lab8.run --shape single --claim-id C-001 --seed 11 --db data/personal_demo.sqlite
python3 -m lab8.demo.web --port 8088
```

Không dùng riêng `-k single` vì tên hàm `test_public_single_run_cases` cũng khiến test của các shape khác được chọn.

## 5. Công cụ AI đã dùng

- **Công cụ:** OpenAI Codex.
- **Mục đích:** hỗ trợ đọc yêu cầu, viết implementation single, giải thích thiết kế, chạy test/benchmark/demo, tạo nhánh và commit/push theo chỉ định; sau đó hỗ trợ UI, test demo, gỡ conflict và soạn báo cáo.
- **Cách kiểm tra đã sử dụng:** chạy test có sẵn, đối chiếu kết quả với ledger/audit bằng evaluator của lab, kiểm retry/crash trên cùng database, chạy công cụ benchmark chính thức và kiểm thao tác UI trong browser. Không chỉnh thước đo hoặc sửa tay JSON.
- **Phân biệt người thực hiện:** các lệnh và kết quả nêu trên được Codex thực thi trong phiên. Chưa có xác nhận người học đã tự chạy lại hoặc tự viết độc lập toàn bộ code; không ghi thay lời xác nhận đó.
- **Tham khảo cách trình bày:** báo cáo [Lưu Đăng Tuấn trên nhánh Single](https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents/blob/Single/report/team/2A202603454_LuuDangTuan.md). Chỉ tham khảo bố cục sáu mục và cách dẫn bằng chứng; nội dung đóng góp, môi trường, công cụ AI và commit trong báo cáo này dùng thông tin riêng đã có.

## 6. Tự đánh giá

### Kết quả và điểm mạnh của phần việc

Implementation single đã thay stub, giữ contract chung, vượt bộ public riêng và đạt 70/70 trial benchmark public. Các quyết định quan trọng nằm ở code/host: dữ liệu order/policy làm nguồn sự thật, agent chỉ đọc và ledger xác nhận effect. UI bổ sung giúp nhìn rõ quote khác tiền thực ghi như thế nào, đồng thời quan sát retry/crash mà không cần đọc toàn bộ JSON bằng tay.

### Hạn chế và bài học kỹ thuật

MockLLM và callback có kiểm soát chưa đại diện cho năng lực lập kế hoạch của model thật. Public đúng không chứng minh hidden đúng. Chi phí mô phỏng giữa các implementation chưa hoàn toàn đồng nhất: workflow đếm lời gọi host vào tool Budget, single/orchestrator không đếm bước host này. Vì vậy không quy mọi chênh lệch chi phí cho topology.

Thiết kế cho thấy idempotency phải gắn với effect trong ledger, không chỉ checkpoint; trace/handoff cần chọn field trước khi ghi hoặc chuyển, không dựa vào lời nhắc model giữ bí mật. Đây là nhận xét kỹ thuật từ code và bằng chứng, không thay cho tự thuật rằng người học đã nắm vững toàn bộ nội dung.
