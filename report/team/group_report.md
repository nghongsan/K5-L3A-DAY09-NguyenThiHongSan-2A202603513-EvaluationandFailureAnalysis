# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm và phiên bản

- Nhóm: Tourist; danh sách thành viên và bằng chứng đóng góp xem TEAM.md.
- Lớp: L3A. Danh sách sáu thành viên và bằng chứng đóng góp đã được tổng hợp trong TEAM.md từ báo cáo và commit của từng nhánh; những mục chưa có bằng chứng vẫn được ghi rõ.
- Bản nền đã tích hợp workflow/orchestrator: `ceca05b3681429f7c7fa7843db215610c63019c7` trên nhánh `main`.
- Commit code tích hợp đã kiểm: `ceca05b3681429f7c7fa7843db215610c63019c7`. Commit kế tiếp cập nhật tài liệu sau merge. [Manifest](evidence_manifest.json) ghi SHA-256 code và report đã đo.

## 2. Mục tiêu và phương pháp

Xử lý yêu cầu hoàn phí vận chuyển bằng workflow, single agent và orchestrator, đồng thời dùng swarm tham chiếu làm đối chứng. Mỗi shape trả cùng RunResult; code tính tiền, host kiểm approval/quyền sở hữu/trần theo đơn/idempotency. Mục tiêu là chọn mức tự chủ đủ dùng dựa trên số đo, không mặc định nhiều agent tốt hơn.

Benchmark giữ cùng 14 claim public, 5 seed 11/22/33/44/55, MockLLM, policy và bảng giá. Mỗi trial dùng SQLite mới để tránh hiệu ứng từ trial trước. Tổng 4 × 14 × 5 = 280 trial. UI so sánh đúng ba kiến trúc theo yêu cầu demo; swarm chỉ xuất hiện trong benchmark.

## 3. Giải pháp và ranh giới trách nhiệm

| Kiến trúc | Cách xử lý | Ranh giới |
|---|---|---|
| Workflow | Checklist Python: claim → đơn → quote → host; MockLLM soạn phản hồi | Đường đi cố định, không lấy số tiền từ ticket |
| Single | run_react tối đa 8 lượt, decide chọn tool đọc dựa trên observation | worker=True chặn tool ghi; sau vòng lặp code mới gọi host |
| Orchestrator | make_handoff tạo gói cho investigator đọc order/policy và tính quote | Handoff theo allowlist; investigator không có quyền ghi tiền |
| Swarm tham chiếu | Thêm peer/model call, có điểm yếu tin ticket ở một seed | Giữ nguyên để quan sát variance, không sửa cho đẹp kết quả |

MockLLM không cung cấp structured tool-calling của model thật. Trong single, callback decide chọn tool bằng code và gọi MockLLM để mô phỏng usage. Điều này giới hạn kết luận về khả năng suy luận tự chủ.

**Tiền và approval.** compute_compensation tính quote từ order và policy hiện hành. Shape truyền **quote đầy đủ** vào issue_refund; host tự trừ khoản đã hoàn, giới hạn approval và paid_vnd. Ví dụ C-014: quote 150.000đ, đã trả 30.000đ, effect mới 120.000đ. Tự trừ trước sẽ khiến host trừ hai lần. Quote > 0 nhưng approval hỏng vẫn đi qua host để tạo audit policy_denied.

**Durability.** Mỗi claim dùng khóa refund:claim_id. Truyền crash_at vào host, ghi trace crash rồi phát lại InjectedCrash để test thấy crash thật. finally đóng kết nối. Khi resume, ledger là nguồn xác nhận effect đã ghi; checkpoint riêng lẻ không đủ chống trả trùng.

**Trace và handoff.** Không ghi ticket/parent_secret/header/SĐT/địa chỉ/tên hàng/ghi chú nội bộ. Trace dùng dữ liệu đã chọn: tool, quote, decision; orchestrator thêm handoff được lọc và kết quả order view trong allowlist. Không coi LLM tóm tắt là công cụ xóa secret.

**UI demo.** Python HTTP server phục vụ HTML/CSS/JS trên 127.0.0.1:8088. Mỗi kiến trúc chạy trong subprocess có thư mục tạm, SQLite và trace riêng. Retry/crash dùng cùng SQLite trong hai lượt của cùng kiến trúc; mỗi request so sánh mới lại bắt đầu từ dữ liệu public. UI hiển thị result/trace thật và kiểm bằng trial_pass, không hardcode kết quả. Chi phí/model/tool calls trên thẻ thuộc lượt cuối. Không cần API key, Node.js hay dịch vụ bên ngoài.

## 4. Kết quả thực nghiệm

Nguồn số liệu: [benchmark.json](../../src/reports/benchmark.json), do lab8.benchmark sinh; không sửa JSON bằng tay.

| Shape | Trial pass | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
|---|---:|---:|---:|---|---:|---:|---|
| workflow | 70/70 | 1.0000 | 1.0000 | 1.0000–1.0000 | 0.000000 | 35.3000 | 4.4286 / 5 |
| single | 70/70 | 1.0000 | 1.0000 | 1.0000–1.0000 | 0.000000 | 29.1057 | 5.5714 / 6 |
| orchestrator | 70/70 | 1.0000 | 1.0000 | 1.0000–1.0000 | 0.000000 | 47.8529 | 3.7143 / 4 |
| swarm | 69/70 | 0.9857 | 0.9286 | 0.9286–1.0000 | 0.000816 | 49.5670 | 2.8000 / 3 |

- Crash suite chính thức: **20/20**, nguồn [crash.json](../../src/reports/crash.json). Suite này kiểm host và swarm tham chiếu; không mô tả nó là 20 điểm crash riêng cho từng shape.
- Toàn bộ test: **442 passed** với `python3 -m pytest -q -o addopts=`. Gồm test host, ma trận student, test nhóm hiện có và 15 test mới cho backend demo/input. Test demo chạy thật các shape ở retry, crash, approval, scope và phần tiền chênh lệch.
- Kiểm browser: C-001 trả 35.000đ trên cả ba shape; crash rồi resume vẫn một effect/một audit; C-002 kiểm từ chối khi ticket khác order.
- Swarm sai C-002 seed 55: order trễ 2 ngày nhưng tin ticket nói 5 ngày. Test student coi đây là lỗi tham chiếu đã biết; việc pytest xanh không đồng nghĩa swarm đạt benchmark 100%.
- Chưa được cung cấp student_drop/nhãn hidden: **chưa kết luận đạt hidden ≥ 0,75**.

**Diễn giải lựa chọn.** Giữ shape workflow từ ADR đã merge vì đây là mức tự chủ thấp nhất vẫn đạt 70/70 public trial. Single có chi phí được ghi nhận thấp nhất hiện tại (29,1057 VND/success), nhưng không thay đổi lựa chọn nhóm chỉ dựa trên chỉ số này: workflow hiện đếm issue_refund là tool, single/orchestrator không đếm bước host đó vào Budget, prompt và tool đọc cũng khác nhau. Cần chuẩn hóa accounting trước khi kết luận về ảnh hưởng topology. Workflow không được mô tả là rẻ nhất trong snapshot sau merge; chưa có bằng chứng hidden để chốt khả năng tổng quát.

## 5. Khó khăn và cách xử lý

Khi bắt đầu, single.py chứa cả hai phần conflict `Updated upstream`/`Stashed changes`, gây lỗi cú pháp. Giữ phần implementation single đã có, bỏ stub và marker; không thay host hay thước đo. Sau đó chạy lại toàn bộ test và benchmark.

Để tránh demo trả trùng do chia sẻ state giữa ba card, mỗi shape chạy trong worker/thư mục riêng. Muốn chứng minh retry/crash an toàn thì dùng lại database giữa hai lượt trong worker, thay vì tạo mới database rồi tuyên bố chống trùng. Browser chỉ nhận nhãn kịch bản đã biên soạn và trace đã lọc, không tải row thô.

## 6. Đóng góp và công cụ hỗ trợ

Lịch sử repo có các phần workflow/orchestrator đã tích hợp; báo cáo giữ nguyên các phần đó và không nhận là vừa viết mới. Phiên này gỡ conflict single, thêm server/UI so sánh, test backend demo, chạy lại bằng chứng và soạn báo cáo với hỗ trợ Codex. TEAM.md đã tổng hợp sáu thành viên từ báo cáo/commit của các nhánh; các mục thiếu bằng chứng, bao gồm test riêng chưa bổ sung của Thanh Thúy, vẫn được ghi rõ thay vì tự điền giả.

## 7. Hạn chế, tái lập và hướng cải thiện

MockLLM là mô phỏng, chi phí không phải hóa đơn API, latency unavailable. Steps là số event trace, phụ thuộc mức logging, không phải thời gian hay số bước suy luận thống nhất. Public nhỏ và đã biết nhãn; chưa chứng minh tổng quát trên hidden hoặc dữ liệu thực. UI local không phải dịch vụ production hay nơi xử lý dữ liệu khách thật.

Chạy lại từ src:

```bash
python3 -m pytest -q -o addopts=
python3 -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python3 -m lab8.crash_test --count 20 --out reports/crash.json
python3 -m lab8.demo.web --port 8088
```

Hướng tiếp theo: chuẩn hóa accounting, tự kiểm student_drop khi được cấp, rà lại TEAM và báo cáo cá nhân, nhất là tiêu chí mỗi thành viên có test riêng; chạy check_submission trên bản chốt. UI/báo cáo hoàn thành không đồng nghĩa toàn bộ checklist nộp bài đã đủ.

## 8. Tài liệu tham khảo và hướng dẫn demo

- [Luật nghiệp vụ](../../docs/business_rules.md), [contract](../../docs/contracts.md), [metrics](../../docs/metrics.md) và [luật sử dụng AI](../../RULES.md) của starter.
- [Kịch bản trình bày và cách chạy UI](../../src/lab8/demo/README.md).
- [Manifest phiên bản đã đo](evidence_manifest.json).
