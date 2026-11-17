# Báo cáo cá nhân — 2A202603493_NguyenThanhDanh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thành Danh
- MSSV: 2A202603493
- Email: 26ai.danhnt@vinuni.edu.vn
- GitHub: https://github.com/thdanhnguyen

## 2. Phần việc phụ trách

- **Vai trò:** Kiểm thử tích hợp Host (Durability, Crash/Idempotency, Policy/Approval/Per-order cap) & Thực thi bằng chứng/Benchmark cho nhánh `orchestrator`.
- **Phạm vi thực tế trong repo (nối tiếp phần code của `Hdang3825`):**
  - Thành viên `Hdang3825` đã cài đặt `src/lab8/shapes/orchestrator.py` và `src/tests/test_orchestrator_security.py` ở các commit `a734b3d` và `ba014e4`.
  - Phần việc của tôi (tác giả `thdanhnguyen`, commit `2d6348f`) tập trung vào **kiểm chứng hành vi Host Integration & Durability** của shape `orchestrator` bằng bộ test độc lập, **chạy bộ crash suite 20 điểm**, **chạy benchmark 4 shape × 5 seed**, và **viết báo cáo cá nhân**. Tôi không sửa đổi mã nguồn `src/lab8/shapes/orchestrator.py`.

## 3. Đóng góp cụ thể

- **Commit `2d6348f` (`feat: add test and run test, benchmark`, đã merge vào `main` tại `ecff509`):**
  1. **Tạo file test `src/tests/test_orchestrator_durability.py` (227 dòng, 6 test case):**
     - `test_orchestrator_idempotent_replay_keeps_single_refund`: gọi lại `orchestrator.run_claim` hai lần trên cùng claim `C-011` với hai seed khác nhau (`11`, `22`), kiểm tra vẫn chỉ có 1 dòng `refund_ledger` (`idempotency_key = "refund:C-011"`, `35000` VND) và 1 audit `refund_committed`.
     - `test_orchestrator_crash_after_effect_before_checkpoint_no_double_refund`: tiêm lỗi `crash_at="after_effect_before_checkpoint"` trên `C-012`, xác nhận `InjectedCrash` lan truyền ra ngoài (không bị nuốt), ledger đã ghi 1 dòng nhưng chưa có checkpoint; sau đó resume với `crash_at=None` trả về `resolved`, checkpoint được ghi và không tạo double-refund.
     - `test_orchestrator_other_crash_points_propagate_and_resume_cleanly`: kiểm thử 2 điểm crash `before_effect` và `after_checkpoint` trên `C-001` đều lan truyền `InjectedCrash` và resume an toàn về đúng 1 refund.
     - `test_orchestrator_host_rejections_and_per_order_cap`: kiểm thử trực tiếp qua `orchestrator.run_claim` các ca `T13` (`C-013`, đơn đã hoàn đủ → `denied`, `proposal_amount=35000`, có audit `policy_denied` với lý do `order_already_refunded`), `T14` (`C-014`, đơn đã hoàn trước `30000` → chỉ hoàn phần chênh lệch `120000` trên quote đầy đủ `150000`), và `T07` (`C-007`, `approval_expired` → `denied`, `proposal_amount=35000`, có audit `policy_denied`).
     - `test_orchestrator_blocks_mismatched_approval_claim_and_amount_conflict`: kiểm thử approval gán cho claim khác (`approval_claim_mismatch` → `denied`, có audit `policy_denied`, không ghi ledger) và xung đột số tiền khi retry sau khi entitlement thay đổi (`amount_conflict` → `failed`, giữ nguyên dòng refund cũ `35000`).
  2. **Sinh bằng chứng crash safety `src/reports/crash.json` (127 dòng):**
     - Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json`, kết quả `20/20` điểm crash đạt.
  3. **Sinh bằng chứng benchmark `src/reports/benchmark.json` (3801 dòng):**
     - Chạy `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` tại thời điểm nhánh `orchestrator` (trước khi merge `Workflow` và `Single`).
- **Tạo báo cáo cá nhân `report/team/2A202603493_NguyenThanhDanh.md`.**

## 4. Bằng chứng

- **Commit trên Git:**
  - `2d6348f` (`DanhNguyen (thdanhnguyen) <nguyendanh0922@gmail.com>`): `src/tests/test_orchestrator_durability.py`, `src/reports/crash.json`, `src/reports/benchmark.json`.
  - Merge vào `main` tại `ecff509`.
- **Kết quả lệnh kiểm thử đã chạy (trong `src/`):**
  - `python -m pytest -q`: **64 passed, 248 deselected** (bao gồm 6 test mới trong `src/tests/test_orchestrator_durability.py`).
  - `python -m pytest -q -m student -o addopts= -k orchestrator`: **62 passed, 250 deselected**.
  - `python -m lab8.crash_test --count 20 --out reports/crash.json`: **`crash_safety 20/20`**.
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` (trên nhánh `orchestrator`, nơi `workflow` và `single` lúc đó vẫn là stub `0.000`):
    - `orchestrator`: `pass_rate = 1.000` (`70/70`), `pass^5 = 1.000`, `seed_variance = 0.000000` (`1.000–1.000`), `cost_per_success_vnd = 47.85`, `mean_steps = 3.71`, `p95_steps = 4.0` (run id mẫu: `R-orchestrator-C-001-s11`).
    - `swarm` (đối chứng): `pass_rate = 0.986` (`69/70`), `pass^5 = 0.929`, `seed_variance = 0.000816`, `cost_per_success_vnd = 49.57`.

## 5. Công cụ AI đã dùng

- **Công cụ:** Trợ lý AI lập trình tích hợp trong IDE (Antigravity / Codex).
- **Mục đích sử dụng:**
  - Kiểm tra đối chiếu mã nguồn `src/lab8/shapes/orchestrator.py` (do `Hdang3825` viết ở `a734b3d`) với `docs/contracts.md`, `docs/business_rules.md`, `RUBRIC.md` và `CHECKPOINTS.md`.
  - Hỗ trợ viết 6 test case trong `src/tests/test_orchestrator_durability.py`.
  - Hỗ trợ soạn thảo và rà soát báo cáo cá nhân.
- **Cách tự kiểm tra kết quả:**
  - Đối chiếu `git show 2d6348f --stat` để chắc chắn không sửa các file bị cấm (`metrics.py`, `durability.py`, `policy.py`, `config/*.yaml`, `data/*`) và không sửa tay các file JSON trong `src/reports/`.
  - Tự chạy lại toàn bộ lệnh `pytest -q`, `pytest -q -m student -o addopts= -k orchestrator`, `python -m lab8.crash_test`, `python -m lab8.benchmark` và `python -m lab8.check_submission` để xác minh số liệu khớp với kết quả thực thi.

## 6. Tự đánh giá

- Đáp ứng yêu cầu kiểm chứng Host Integration, Crash/Idempotency (`20/20`), Benchmark trên nhánh `orchestrator` (`70/70` trial public cho `orchestrator`) và có commit kỹ thuật riêng (`2d6348f`) kèm bộ test `src/tests/test_orchestrator_durability.py`.
- Lưu ý cần làm tiếp ở bước hoàn thiện toàn nhóm trên `main`: chạy lại `lab8.benchmark` sau khi đã hợp nhất đủ `workflow`, `single`, `orchestrator` để cập nhật `src/reports/benchmark.json` cho cả 4 shape, rồi điền `TEAM.md`, `report/team/decision_adr.md`, `report/team/research_card.md`, `report/team/group_report.md` và kiểm tra `python -m lab8.check_submission` đạt `0 FAIL`.
