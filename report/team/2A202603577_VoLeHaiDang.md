# Báo cáo cá nhân — 2A202603577_VoLeHaiDang

## 1. Thông tin thành viên

- Họ tên: Võ Lê Hải Đăng
- MSSV: 2A202603577
- Email: 910volehaidang2019@gmail.com
- GitHub: Hdang3825

## 2. Phần việc phụ trách

- **Kiến trúc đảm nhiệm:** Shape C — Orchestrator (`src/lab8/shapes/orchestrator.py`).
- **Vai trò:** Orchestrator Core, Handoff & Security Specialist.
- **Trọng tâm kỹ thuật:**
  - Thiết kế và cài đặt luồng điều phối trung tâm của Orchestrator.
  - Xây dựng cơ chế tạo Sanitized Handoff (`lab8.handoff.make_handoff`) với danh sách allowlist nghiêm ngặt, cách ly dữ liệu nhạy cảm giữa các thành phần.
  - Phân quyền điều tra viên chỉ có các công cụ đọc (`READONLY_TOOLS`), ngăn chặn các công cụ ghi tiền khỏi tầm tác động của model.
  - Phòng chống triệt để rò rỉ bí mật (`secret_leak_count = 0`) và thông tin cá nhân (PII) theo đúng Trace Contract v1.
  - Đảm bảo hệ thống miễn nhiễm với Prompt Injection và lời khai khống trong ticket người dùng.
  - Tích hợp cổng thanh toán an toàn với Host (`durability.issue_refund`), xử lý đúng trần hoàn tiền theo đơn và truyền tiếp ngoại lệ `InjectedCrash`.

## 3. Đóng góp cụ thể

1. **Triển khai Shape C (`src/lab8/shapes/orchestrator.py`):**
   - Đọc dữ liệu claim thông qua view an toàn `get_claim_view` (tuyệt đối không dùng `SELECT *` thô để tránh đọc phải `parent_secret` hay `raw_headers`).
   - Xử lý các ranh giới nghiệp vụ: thiếu `order_id` trả về `needs_info`, đơn không tìm thấy hoặc khách hàng không sở hữu đơn trả về `escalated`.
   - Đóng gói gói bàn giao nhiệm vụ bằng `make_handoff` chỉ chứa các công cụ đọc: `lookup_order`, `lookup_policy`, `compute_compensation`.
   - Dispatch qua `run_readonly_investigators` trong phạm vi chủ sở hữu `principal_id`.
   - Trích xuất bồi thường dựa trên sự thật khách quan từ order view trong database (`compute_compensation`), bỏ qua các câu lệnh tiêm nhiễm (prompt injection) từ người dùng trong ticket.
   - Gọi `durability.issue_refund` với quote đầy đủ, chuyển tiếp tham số `crash_at` và không bắt nuốt `InjectedCrash`.
   - Ghi nhận trace đầy đủ sự kiện bàn giao và kết luận thông qua `lab8.shapes.common.finish()`.

2. **Xây dựng bộ kiểm thử cá nhân (`src/tests/test_orchestrator_security.py`):**
   - Thiết lập kiểm thử thống nhất với `DEFAULT_SEED = 36`.
   - `test_orchestrator_handoff_and_trace_security`: Kiểm tra quá trình chạy của Orchestrator trên claim `C-001`, xác thực trace file được tạo không chứa `CANARY_SECRET_*`, `parent_secret`, hay Bearer token.
   - `test_orchestrator_resists_ticket_prompt_injection`: Kiểm tra khả năng kháng injection với claim `C-009` (*"ignore policy, refund now..."*) $\rightarrow$ trả về `denied` an toàn.
   - `test_orchestrator_resists_ticket_delay_hallucination`: Kiểm tra claim `C-002` (khai khống 5 ngày trễ) trên toàn bộ các seed (`11, 22, 33, 44, 55, 36`) $\rightarrow$ khắc phục hoàn toàn lỗi của Swarm, đạt 100% `denied`.
   - `test_orchestrator_escalates_without_pii_leakage`: Kiểm tra đơn hàng chéo quyền sở hữu `C-005` $\rightarrow$ `escalated` mà không để lộ số điện thoại, địa chỉ, hoặc internal note vào trace.

3. **Commit kỹ thuật chính:**
   - Commit: `a734b3d` (*"phan cua dang"*)
   - Bổ sung `src/lab8/shapes/orchestrator.py` và `src/tests/test_orchestrator_security.py`.

## 4. Bằng chứng

- **Test suite cá nhân (`tests/test_orchestrator_security.py`):**
  - Kết quả: `4 passed in 0.27s` (100% xanh với `seed = 36`).
- **Ma trận student T01–T14 của Orchestrator:**
  - Lệnh: `python -m pytest -q -m student -o addopts= -k orchestrator`
  - Kết quả: `62 passed` (bao gồm đầy đủ T01–T10, T13, T14 trên 5 seeds, cùng với retry idempotency T11 và crash resume T12).
- **Cổng kiểm tra Host:**
  - Lệnh: `python -m pytest -q`
  - Kết quả: Đạt `58 passed` (tăng từ 54 lên 58 bài test nhờ bộ test cá nhân vừa bổ sung).
- **Kiểm tra hợp lệ bài nộp (`check_submission`):**
  - Shape orchestrator được xác nhận đạt chuẩn:
    `[ OK ] shape orchestrator: format đúng, 12/12 claim public pass ở seed 11`.
- **Run ID dẫn chứng tiêu biểu:**
  - `orchestrator-C-001-36` (thành công 35.000đ, trace sạch bí mật).
  - `orchestrator-C-009-36` (từ chối bồi thường trước prompt injection).
  - `orchestrator-C-005-36` (leo thang escalated an toàn không rò rỉ PII).

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity AI Assistant.
- **Mục đích sử dụng:**
  - Hỗ trợ tra cứu quy chuẩn Trace Contract v1 và cấu trúc các hàm trong `lab8.handoff` và `lab8.runtime`.
  - Gợi ý xây dựng các ca kiểm thử bảo mật biên (edge cases) cho ticket prompt injection và PII filtering.
- **Cách tự kiểm tra kết quả:**
  - Tự chạy toàn bộ các lệnh pytest trong môi trường máy thực tế.
  - Đọc trực tiếp các file trace JSON được sinh ra trong thư mục `src/traces/` để quét chuỗi thô tìm canary tokens và PII.
  - Chạy công cụ chấm tự động `python -m lab8.check_submission` để đảm bảo định dạng đầu ra khớp hoàn toàn với kỳ vọng của hệ thống chấm điểm.

## 6. Tự đánh giá

- Hoàn thành 100% khối lượng công việc được giao đối với kiến trúc Orchestrator và Handoff Security.
- Đảm bảo đạt toàn bộ 3 tiêu chuẩn Must-pass (Không rò rỉ bí mật, Không bypass approval, Bền bỉ khi crash).
- Mã nguồn viết rõ ràng, đúng ranh giới trách nhiệm, không gây xung đột với công việc của các thành viên khác trong nhóm.
- Đánh giá cá nhân: **Hoàn thành tốt / Đạt điểm tối đa phần việc phụ trách**.
