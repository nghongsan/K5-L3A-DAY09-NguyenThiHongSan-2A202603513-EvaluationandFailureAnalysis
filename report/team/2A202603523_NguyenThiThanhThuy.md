# Báo cáo cá nhân — Nguyễn Thị Thanh Thúy

File được đặt theo quy tắc `MSSV_HoTen.md`.

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Thanh Thúy
- MSSV: 2A202603523
- Email: 26ai.thuyntt@vinuni.edu.vn
- GitHub: https://github.com/ThanhBinh101/K5-L3A-Day8-Tourist-From-Workflows-to-Agents/tree/03523-NguyenThiThanhThuy

## 2. Phần việc phụ trách

Phụ trách hoàn thiện ba shape nhóm viết và kiểm chứng các mốc CP3–CP5: `workflow`, `single`, `orchestrator`; chạy crash/retry, handoff safety, benchmark public và tổng hợp báo cáo. Vai trò được ghi theo yêu cầu của thành viên trong phiên này.

## 3. Đóng góp cụ thể

Đã commit implementation và reports tại `a1cf839`, cập nhật ADR tại `bd3941c`; cập nhật email/GitHub trong báo cáo cá nhân sẽ được commit cùng đợt push này. Không thêm/sửa test; đã chạy test hiện có: student matrix 248 passed, host suite 54 passed. Quyết định kỹ thuật: truyền quote đầy đủ cho host, chuyển tiếp crash injection, dùng handoff read-only đã sanitize và chọn workflow theo benchmark public vì cùng pass rate nhưng cost thấp nhất.

## 4. Bằng chứng

`src/reports/crash.json` (`20/20`); `src/reports/benchmark.json`; run id mẫu `R-workflow-C-001-s11`; kiểm thử `tests/test_public_matrix.py` (248 passed), host suite (54 passed) và `python -m lab8.check_submission` (0 FAIL, 0 WARN sau khi cập nhật `TEAM.md`).

## 5. Công cụ AI đã dùng

Đã dùng AI assistant using Copilot SDK in VS Code để hỗ trợ đọc contract, triển khai code, chạy kiểm tra và tổng hợp report. Không dùng API/model thật cho lab. Kết quả được tự kiểm bằng student matrix, host suite, smoke, crash suite và benchmark do lab sinh; các lệnh và kết quả được ghi trong báo cáo nhóm. Xem [RULES.md](../../RULES.md).

## 6. Tự đánh giá

Hoàn thành triển khai và kiểm tra trên phạm vi public; các shape nhóm viết đạt 100% trên benchmark 14 claim × 5 seed, crash suite đạt 20/20, host suite và student matrix đều xanh. Hạn chế còn lại là chưa chạy hidden grader và chưa xác nhận số liệu trên model production; chi phí là mô phỏng, latency `unavailable`.
