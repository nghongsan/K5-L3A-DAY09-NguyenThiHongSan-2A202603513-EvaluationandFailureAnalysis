# Báo cáo cá nhân — 2A202603454_LuuDangTuan

## 1. Thông tin thành viên

- Họ tên: Lưu Đăng Tuấn
- MSSV: 2A202603454
- Email:  26ai.tuanld@vinuni.edu.vn
- GitHub: kegacua

## 2. Phần việc phụ trách

- Phân tích yêu cầu đề bài, business rules, Trace contract v1, cơ chế idempotency/durability và tiêu chí chấm điểm (rubric) của Lab 8 LogiX-VN.
- Rà soát, hoàn thiện xử lý crash trace và viết bộ unit test kiểm thử biên cho **Shape B (`single` — ReAct agent giới hạn 8 bước)** tại `src/lab8/shapes/single.py` và `src/tests/test_single_shape.py`.

## 3. Đóng góp cụ thể

- **Rà soát và hoàn thiện `src/lab8/shapes/single.py`:**
  - Bổ sung khối `try / except InjectedCrash:` quanh lời gọi `durability.issue_refund(...)` để ghi nhận sự kiện `crash` và gọi `trace.write()` trước khi `raise` lại `InjectedCrash`, đảm bảo các trial crash vẫn tạo trace hợp lệ, sạch secret/PII cho leak scan mà vẫn giữ nguyên cơ chế propagate crash và đóng kết nối DB ở `finally`.
  - Kiểm tra ranh giới code/model của Shape B: chạy `lab8.runtime.run_react` với `max_steps=8`, `worker=True` (chặn write tool), dùng `MockLLM.complete` ghi nhận vào `Budget`, tính tiền bằng `compute_compensation` từ dòng đơn hàng có cấu trúc (bỏ qua số ngày sai lệch, prompt injection và policy hết hiệu lực `SHIP-LATE-OLD` trong `ticket`), và truyền **quote đầy đủ** vào `durability.issue_refund` để host kiểm approval, trần theo đơn và idempotency.
- **Thêm mới bộ test `src/tests/test_single_shape.py` (8 test case chạy trong cổng host `python -m pytest -q`):**
  - `test_single_crash_flushes_clean_trace_and_resumes_once`: kiểm tra cả 3 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), xác minh file trace được ghi ngay khi crash, không chứa `CANARY_SECRET_*`, và resume giữ đúng 1 dòng ledger.
  - `test_single_ignores_ticket_lies_injection_and_missing_order_id`: kiểm tra trên seed `11` và `55` khi ticket nói dối, chứa prompt injection `"ignore policy"`, trích `SHIP-LATE-OLD`, hoặc thiếu `order_id` dù ticket có nhắc mã đơn.
  - `test_single_denies_with_full_quote_on_approval_claim_mismatch`: kiểm tra trường hợp approval trỏ tới claim khác (`approval_claim_mismatch`), xác minh trả `status="denied"`, `proposal_amount=35000`, ghi audit `policy_denied`, không ghi ledger và không lộ canary secret.
  - `test_single_handles_unknown_claim_and_amount_conflict`: kiểm tra xử lý `unknown_claim` và `amount_conflict` khi retry khác số tiền đã commit.
  - `test_single_tracks_budget_and_per_order_cap`: kiểm tra thống kê `Budget` (`model_calls`, `tool_calls`, `cost_estimate`) và cơ chế top-up chênh lệch theo đơn trên `C-014` (`proposal_amount=150000`, `refund_effects[0]["amount_vnd"]=120000`).

## 4. Bằng chứng

- **Nhánh & commit:** Nhánh `Single`, commit [`bf6cb68`](https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents/commit/bf6cb68fe74166c225ce7a94bbe2da458c827fee) (*lưu ý: cập nhật lại hash commit mới nhất sau khi xử lý xung đột stash trong `single.py` và merge vào `main`*).
- **File đóng góp:**
  - `src/lab8/shapes/single.py`
  - `src/tests/test_single_shape.py`
- **Các kiểm tra đã chạy trên bản Shape B trước khi stash sang nhánh `Single` (trong thư mục `src/`, Python 3.11.0 trên Windows):**
  - `python -m lab8.smoke` → `lab8.smoke pass`
  - `python -m pytest -q` → `62 passed, 248 deselected` (gồm 54 host tests gốc và 8 tests trong `tests/test_single_shape.py`)
  - `python -m pytest -q -m student -o addopts= -k "single]"` → `62 passed, 248 deselected` (qua toàn bộ T01–T14 trên 5 seed `11,22,33,44,55`)
  - `python -m lab8.check_submission` → `[ OK ] shape single: format đúng, 12/12 claim public pass ở seed 11`
  - Benchmark thử Shape `single` vs `swarm` trên 14 public claim × 5 seed: `single` đạt `pass = 1.000`, `pass^5 = 1.000`, `seed_variance = 0.000000`, `cost/success = 29.11` VND (mô phỏng), `mean_steps = 5.57` (so với `swarm` đạt `0.986`, `0.929`, `0.000816`, `49.57` VND).
  - Một số `run_id` trace đã kiểm tra sạch secret/PII: `R-single-C-005-s11`, `R-single-C-014-s11`, `R-single-C-012-s101`.

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity (Google Deepmind).
- **Mục đích sử dụng:**
  - Đọc và phân tích cấu trúc repo, luật nghiệp vụ (`docs/business_rules.md`), contract đầu ra/trace (`docs/contracts.md`), và rubric chấm bài (`RUBRIC.md`).
  - Rà soát code Shape B (`src/lab8/shapes/single.py`), phát hiện thiếu sót chưa flush trace khi `InjectedCrash` xảy ra, bổ sung xử lý crash trace và viết bộ test `src/tests/test_single_shape.py`.
  - Hỗ trợ soạn thảo báo cáo cá nhân theo mẫu `report/team/MSSV_HoTen.md`.
- **Cách tự kiểm tra kết quả:**
  - Đối chiếu trực tiếp từng dòng thay đổi ở `src/lab8/shapes/single.py` và `src/tests/test_single_shape.py` với `docs/business_rules.md`, `docs/contracts.md` và `RULES.md` (không sửa bất kỳ file thước đo/dữ liệu nào bị cấm).
  - Chạy lại trực tiếp các lệnh `python -m lab8.smoke`, `python -m pytest -q`, `python -m pytest -q -m student -o addopts= -k "single]"`, `python -m lab8.check_submission` và đọc trực tiếp các file JSON trong `src/traces/` để xác nhận không rò rỉ `CANARY_SECRET_*` hay PII.

## 6. Tự đánh giá

- Đã rà soát kỹ và giúp Shape B (`single`) xử lý đầy đủ cả các ca biên lẫn việc ghi trace khi crash, kèm bộ unit test độc lập chạy trong cổng host.
- Cần phối hợp với nhóm để giải quyết xong xung đột stash ở `src/lab8/shapes/single.py` trên nhánh `Single`, chạy lại toàn bộ `pytest` + `benchmark` + `crash_test`, cập nhật bảng đóng góp trong `TEAM.md` và các tài liệu chung (`decision_adr.md`, `research_card.md`, `group_report.md`) trước khi chốt commit nộp bài.
