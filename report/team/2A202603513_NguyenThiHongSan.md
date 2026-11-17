# Báo cáo cá nhân — 2A202603513_NguyenThiHongSan

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Hồng San
- MSSV: 2A202603513
- Email: 26ai.sannth@vinuni.edu.vn
- GitHub: nhánh `03513-NguyenThiHongSan` — https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents/tree/03513-NguyenThiHongSan

## 2. Phần việc phụ trách

Shape A — **workflow** (`src/lab8/shapes/workflow.py`): luồng xử lý claim tất định, không để model quyết số tiền hay ghi refund. Kèm theo phần CP3–CP4 của shape này (crash, ledger, approval, secret) và bộ test riêng `src/tests/test_workflow_shape.py`.

## 3. Đóng góp cụ thể

**Commit chính**

| Commit | Nội dung |
| --- | --- |
| `aae7ba2` | CP2: viết shape workflow thay stub |
| `2a26331` | CP3/CP4: làm cứng workflow (không ném exception, `order_id` trắng → `needs_info`), thêm `reports/crash.json` |
| `0314734` | Thêm `tests/test_workflow_shape.py` (107 test, chạy trong cổng host) |

**Luồng workflow**

1. Đọc claim qua `get_claim_view` (allowlist), không `SELECT *`. Không có claim → `failed`.
2. `order_id` rỗng hoặc chỉ có khoảng trắng → `needs_info`, không ghi ledger, không đoán mã đơn từ ticket.
3. `lookup_order` theo principal của claim. Không thấy đơn / không sở hữu → `escalated`, trace chỉ ghi `reason`.
4. Tính tiền bằng `compute_compensation` từ dòng order và policy hiện hành. Ticket không được dùng làm nguồn dữ kiện.
5. Quote = 0 → `denied`, không gọi `issue_refund`.
6. Quote > 0 → `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`. Host kiểm approval, trừ phần đã hoàn của đơn, giữ idempotency. `ok` → `resolved`, `conflict` → `failed`, còn lại → `denied`; `proposal_amount` luôn là quote đầy đủ.
7. MockLLM chỉ soạn câu trả lời, prompt chỉ có `status` và số tiền.

**Quyết định kỹ thuật**

- *Truyền quote đầy đủ*, không tự trừ phần đã hoàn: host đã trừ theo đơn, shape trừ thêm thì T14 sai.
- *Không tự từ chối khi quote > 0*: phải để host từ chối thì mới có audit `policy_denied`.
- *Không bắt `InjectedCrash`*, nhưng ghi trace trước khi để lỗi đi tiếp, để T12 thấy crash thật và trace không bị thiếu.
- *Bắt mọi exception khác* và trả `failed` có trace: contract cấm `run_claim` ném lỗi; dòng dữ liệu hỏng hay DB lỗi không được làm trial thành `exception:<lỗi>`.
- *Không chuẩn hoá mã đơn* (hoa/thường, homoglyph): mã giống nhưng khác ký tự phải tra không ra và `escalated`, không được khớp nhầm sang đơn khác.
- *Trace chỉ ghi field đã chọn* (`has_order_id`, `visible/reason`, `amount_vnd`, `clause_ids`, `delay_days`, `order_status`), không ghi claim row hay order row.

## 4. Bằng chứng

| Kiểm tra | Lệnh | Kết quả |
| --- | --- | --- |
| Ma trận student T01–T14 | `python -m pytest -q -m student -o addopts= -k workflow` | 62 passed |
| Cổng host (gồm test mới) | `python -m pytest -q` | 161 passed, 0 failed |
| Test riêng workflow | `python -m pytest -q tests/test_workflow_shape.py` | 107 passed |
| Crash suite | `python -m lab8.crash_test --count 20 --out reports/crash.json` | `crash_safety 20/20` |
| Benchmark public, 5 seed | `python -m lab8.benchmark --shapes workflow --cases data/public_claims.jsonl --seeds 11,22,33,44,55 ...` | pass 1.000, pass^5 1.000, variance 0, min/max 1.000/1.000, cost/success 35.30 VND (mô phỏng), steps 4.43 |
| check_submission | `python -m lab8.check_submission` | `shape workflow: format đúng, 12/12 claim public pass ở seed 11` |

Run id dẫn chứng: `R-workflow-C-012-s11` (crash `after_effect_before_checkpoint` rồi resume → 1 dòng ledger 35.000, key `refund:C-012`, 1 audit `refund_committed`), `R-workflow-C-014-s11` (proposal 150.000, ledger 120.000), `R-workflow-C-002-s55` (ticket ghi trễ 5 ngày, order 2 ngày → `denied`, chỗ swarm fail).

`tests/test_workflow_shape.py` gồm:

- 4 kiểu approval hỏng (thiếu, của claim khác, bị thu hồi, hết hạn) → `denied`, `proposal_amount` 35.000, không ledger, có `policy_denied` đúng lý do; T07, T08, T13, T14 đúng nhãn.
- 7 claim có tiền × 3 điểm crash, chạy lại 2 lần → đúng 1 dòng ledger, đúng số tiền, 1 audit.
- 14 claim × 5 seed: trace đúng contract, trace / stdout / `RunResult` không chứa `CANARY_*`, `Bearer`, `parent_secret`, `raw_headers` hay 40 chuỗi PII của order.
- Edge case: `order_id` trắng, mã đơn homoglyph, ticket chèn lệnh, dữ liệu sai kiểu, store không đọc được, claim không tồn tại.

Đã kiểm bộ test bắt được lỗi thật bằng cách cố ý làm hỏng code: ghi nguyên claim row vào trace → 70 test fail; bỏ `crash_at` → 21 fail; shape tự từ chối khi quote > 0 → 29 fail.

## 5. Công cụ AI đã dùng

- **Claude Code** (trong VS Code): đọc contract và host code, viết bản đầu của `workflow.py`, rà lỗ hổng, viết `tests/test_workflow_shape.py`, soạn nháp báo cáo này.
- Cách tự kiểm: chạy lại ma trận student, cổng host, crash suite, benchmark và `check_submission` sau mỗi thay đổi (số liệu ở mục 4); thử workflow với dữ liệu bất thường (homoglyph, injection, `order_id` trắng, dữ liệu sai kiểu); cố ý làm hỏng code để chắc test đỏ khi có lỗi; đọc lại diff trước khi commit.

## 6. Tự đánh giá

- Đạt: workflow qua toàn bộ T01–T14 trên 5 seed, an toàn khi crash, không lộ secret, có bộ test riêng chạy trong cổng host.
- Rút ra: tiền phải do code tính và host ghi; checkpoint đơn lẻ không thay được ledger có idempotency key (`python -m lab8.demo.buggy_workflow` ra 2 dòng refund); trace là ranh giới bảo mật nên chỉ ghi field đã chọn.
