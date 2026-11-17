# Team

## Thông tin nhóm

- Tên nhóm: Tourist
- Lớp: L3A
- Repo nhóm: `K5-L3A-Day8-Tourist-From-Workflows-to-Agents` (tên repo hiện tại)
- URL repo, nhánh nộp, commit chốt: https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents · main · code ceca05b3681429f7c7fa7843db215610c63019c7

## Thành viên

| STT | Họ tên                | MSSV        | Email                        | GitHub                         | Vai trò                                 |
| --: | --------------------- | ----------- | ---------------------------- | ------------------------------ | --------------------------------------- |
|   1 | Nguyễn Thị Thanh Bình | 2A202603497 | Chưa cung cấp                | ThanhBinh101                   | Single ban đầu; UI demo/test/report     |
|   2 | Lưu Đăng Tuấn         | 2A202603454 | 26ai.tuanld@vinuni.edu.vn    | kegacua                        | Crash trace và test single              |
|   3 | Nguyễn Thị Hồng San   | 2A202603513 | 26ai.sannth@vinuni.edu.vn    | Nhánh 03513-NguyenThiHongSan   | Workflow và test biên                   |
|   4 | Nguyễn Thành Danh     | 2A202603493 | Theo báo cáo cá nhân         | Nhánh 03493-NguyenThanhDanh    | Orchestrator durability, benchmark      |
|   5 | Võ Lê Hải Đăng        | 2A202603577 | 910volehaidang2019@gmail.com | Hdang3825                      | Orchestrator và security tests          |
|   6 | Nguyễn Thị Thanh Thúy | 2A202603523 | 26ai.thuyntt@vinuni.edu.vn   | Nhánh 03523-NguyenThiThanhThuy | Phương án ba shape, ADR/research/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người                 | Vai                                          | Commit                          | Test đã thêm hoặc sửa                                                                            |
| --------------------- | -------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------ |
| Nguyễn Thị Thanh Bình | Single ban đầu; UI/test demo có hỗ trợ Codex | `1ce29a9`, `3c3f9b2`, `92a0753` | `src/tests/test_demo_web.py` (15 trường hợp; cần người học tự review theo khai báo AI)           |
| Lưu Đăng Tuấn         | Crash trace và test single                   | `bf6cb68`                       | `src/tests/test_single_shape.py`                                                                 |
| Nguyễn Thị Hồng San   | Workflow và kiểm thử biên                    | `aae7ba2`, `2a26331`, `0314734` | `src/tests/test_workflow_shape.py` (107 test)                                                    |
| Nguyễn Thành Danh     | Orchestrator durability/benchmark            | `2d6348f`, `e77ad2b`            | `src/tests/test_orchestrator_durability.py`                                                      |
| Võ Lê Hải Đăng        | Orchestrator/security                        | `a734b3d`, `13ae289`            | `src/tests/test_orchestrator_security.py`                                                        |
| Nguyễn Thị Thanh Thúy | Phương án ba shape; ADR/research/report      | `a1cf839`, `bd3941c`, `4bab90a` | Không thêm/sửa test; đã dùng test có sẵn theo báo cáo cá nhân — cần bổ sung nếu tiêu chí yêu cầu |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## 2A202603513_NguyenThiHongSan

### Phần việc phụ trách

- Shape A — workflow (`src/lab8/shapes/workflow.py`) và các phần CP3–CP4 của shape này: crash, ledger, approval, secret.

### Đóng góp cụ thể

- `aae7ba2`: viết shape workflow (CP2).
- `2a26331`: làm cứng workflow (không ném exception, `order_id` trắng → `needs_info`), thêm `reports/crash.json` (20/20).
- `0314734`: thêm `src/tests/test_workflow_shape.py`, 107 test trong cổng host.

### Bằng chứng

- Ma trận student workflow: 62 passed. Cổng host: 161 passed. Crash suite: 20/20.
- Benchmark public 5 seed: pass 1.000, pass^5 1.000, cost/success 35.30 VND (mô phỏng).
- Báo cáo chi tiết: [report/team/2A202603513_NguyenThiHongSan.md](report/team/2A202603513_NguyenThiHongSan.md).

## Hidden self-check — student_drop (16/11/2026)

Bộ dữ liệu do người học cung cấp từ `Downloads/student_drop/` đã được sao chép vào `src/student_drop/` theo hướng dẫn CP5. Hai file dữ liệu nằm trong `.gitignore`, không đưa lên Git. Kết quả do công cụ chính thức sinh tại [src/reports/hidden_selfcheck.json](src/reports/hidden_selfcheck.json); không sửa tay JSON và không tạo nhãn giả.

- Phiên bản code đã chạy: `2724b162aab601da86e167c3d20b72ed9d6d986d` (main).
- Dữ liệu: 40 claim không nhãn, world state đi kèm; không claim nào có field expected.
- Seed: 11, 22, 33, 44, 55. Mỗi shape 200 trial; tổng 600 trial.
- Mỗi trial dùng SQLite mới theo benchmark; lượt chạy này không inject crash hoặc kiểm retry trên cùng database.

| Shape | Trial chạy xong | Lỗi thực thi | Trace hợp lệ | Cảnh báo leak_suspect | Tổng chi phí mô phỏng (VND) |
|---|---:|---:|---:|---:|---:|
| workflow | 200/200 | 0 | 200/200 | 0 | 7252.60 |
| single | 200/200 | 0 | 200/200 | 0 | 6064.50 |
| orchestrator | 200/200 | 0 | 200/200 | 0 | 9966.00 |

Phân bố status của **mỗi shape**: 90 resolved, 95 denied, 5 needs_info, 10 escalated. Đây là hành vi chương trình quan sát được, không phải số câu đúng hoặc sai. Tổng chi phí gồm các lượt chạy, không phải cost/success vì chưa có nhãn xác định success.

**Giới hạn kết luận:** pass_rate, pass^5, seed_variance và cost_per_success đều là null trong report vì không có nhãn. Không gọi kết quả này là “hidden pass 100%”, không xác nhận đã đạt ngưỡng hidden ≥ 0.75. Scanner self-check chỉ tìm các marker canary được công cụ hỗ trợ và kiểm trace contract, không chứng minh mọi loại PII đều không rò. Độ đúng số tiền/approval và điểm hidden chính thức phải do grader có nhãn của giảng viên đánh giá. Crash suite 20/20 trước đó là bằng chứng riêng trên fixture public/host, không phải kết quả crash của bộ student_drop này.

Lệnh tái lập, chạy từ `src/`:

```bash
python3 -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --seeds 11,22,33,44,55 --out reports/hidden_selfcheck.json
```

Dấu vân tay dữ liệu đã dùng (SHA-256, không công khai nội dung dữ liệu):

- `hidden_claims.jsonl`: `030b53baec31566da8b6a1606a74ac3e09ffd07a0e82c6f7c1f842bef22d2c84`.
- `hidden_world_state.json`: `c2162fb78501da9f407ee9563cf140291c56ad5d7b55ec7ed444371af8eaa236`.

Thực hiện bằng công cụ lab với hỗ trợ Codex theo yêu cầu; không sửa code shape, policy, durability, metrics, config hoặc dữ liệu đề trong lượt self-check này.
