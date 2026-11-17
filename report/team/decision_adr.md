# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: ceca05b3681429f7c7fa7843db215610c63019c7 (bản code đã tích hợp; commit kế tiếp cập nhật tài liệu)
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (70 public trials)
- Cost per success (mô phỏng, VND): 35.30
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 trên kiểm tra public; hidden grader chưa chạy

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Giữ lựa chọn workflow từ ADR của nhánh nhóm vì nghiệp vụ có luật cố định, workflow đạt 70/70 public trial, pass^5=1 và variance=0 với mức tự chủ thấp nhất. Benchmark sau merge ghi nhận cost/success: workflow 35.30, single 29.11, orchestrator 47.85, swarm 49.57 VND mô phỏng. Workflow không phải implementation rẻ nhất trong snapshot này; cách đếm lời gọi host và prompt giữa các shape cũng chưa đồng nhất. Quyết định ưu tiên mức tự chủ tối thiểu, không dựa vào tuyên bố workflow rẻ nhất. Chưa có kết quả hidden hoặc production.

## Có đáng đổi lấy multi-agent không

Trên public set, workflow không thua pass rate so với single hoặc orchestrator và có mức tự chủ thấp; vì vậy chưa có lý do đổi sang multi-agent chỉ để tăng số agent. Sẽ xem xét lại nếu hidden benchmark cùng grader cho thấy workflow dưới ngưỡng pass 0.75, vi phạm must-pass, hoặc một shape khác cải thiện độ đúng đáng kể mà không làm cost/variance tăng quá mức. Nhu cầu tác vụ song song và độ trễ thực tế cũng có thể đổi quyết định, nhưng latency hiện không đo được.

## Trace và bằng chứng

Trace ghi các event tối thiểu như claim tồn tại/có order id, kết quả lookup (visible/reason), quote, handoff đã sanitize, quyết định và vị trí crash. Không ghi ticket thô, parent secret, raw headers, SĐT, địa chỉ, ghi chú nội bộ hay tên hàng; orchestrator chỉ handoff field allowlist và cấp tool đọc. Trace được ghi trong `src/traces/` theo run id và được kiểm tra bởi public benchmark/test. Chưa có kết quả hidden grader; không tuyên bố an toàn hidden dựa trên public scanner.

## Giới hạn

MockLLM không phải model sản xuất, giá là mô phỏng và latency là `unavailable`. Benchmark hiện chỉ có 14 public claim × 5 seed, không có `student_drop/` hoặc hidden grade. Kết luận có thể đổi khi chạy hidden 40 × 5, khi có phân phối claim khác, hoặc khi latency/chi phí model thật được đo; không sửa JSON cho đủ ngưỡng.
