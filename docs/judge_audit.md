# Judge audit

Lệnh chạy: `python -m lab9.judge --csv <file> --audit 5`. Judge chạy ở chế độ replay (verdict lưu sẵn trong CSV) và được đo như một classifier, với FAIL là lớp dương.

| Tiêu chí | n | κ | Precision | Recall | Ma trận (tp/fp/fn/tn) | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | 24 / 4 / 6 / 66 | **Đạt** (exit 0) | **Dùng**, chỉ để theo dõi, không chặn release |
| helpful | 100 | 0.375 | 1.000 | **0.300** | 9 / 0 / 21 / 70 | **Không** (exit 1) | **Loại** |

Hiệu chỉnh Rogan-Gladen cho tỉ lệ lỗi:

- tone: quan sát 0.28, sau hiệu chỉnh 0.30.
- helpful: quan sát 0.09, sau hiệu chỉnh 0.30. Judge helpful thấy chưa bằng **một phần ba** số lỗi thật.

## Audit thủ công 5+ case bất đồng

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em" kèm "nha" quá suồng sã với khách khiếu nại. **Sửa rubric:** xưng hô phải là "LogiX" với "anh/chị"; xưng "em" hoặc "bạn" là FAIL. |
| 2 | H-029 "Dạ, vui lòng chờ… không cần nhắn thêm." | PASS | FAIL | Người | Judge chỉ bám vào chữ "Dạ, vui lòng", nhưng câu là giọng ra lệnh. **Sửa rubric:** thêm ví dụ FAIL "mở đầu lịch sự nhưng ra lệnh hoặc chặn khách liên hệ". |
| 3 | H-051 "Dạ, LogiX đã refund 90.000đ…" | FAIL | PASS | Người | CS LogiX cho phép dùng chữ "refund". **Sửa rubric:** liệt kê thuật ngữ tiếng Anh được phép (refund, ship, voucher). |
| 4 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn…" | FAIL | PASS | **Judge** | Người đọc nhầm ticket. **Sửa nhãn người**, không sửa rubric. Đây cũng là lý do mỗi nhãn cần 2 người gán và đối chiếu. |
| 5 | H-063 "…đã hoàn 20.000đ và sẽ hoàn thêm…" | PASS | FAIL | Người | Câu hứa một khoản hệ thống không ghi. Đây không phải lỗi giọng điệu mà là lỗi nội dung, thuộc FM-08. **Sửa rubric:** tone chỉ chấm giọng điệu; mọi cam kết về tiền chuyển cho grader code `reply_matches_ledger`. |
| 6 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Judge phạt vì "thiếu xin lỗi". **Sửa rubric:** câu xin lỗi không bắt buộc khi kết quả là hoàn tiền. |
| 7 | HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (ledger 40.000) | PASS | FAIL | Người | Judge helpful không có ledger nên không thể biết số tiền sai. Kiểu lỗi này giải thích 18/21 FN của helpful. |
| 8 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Sai xưng hô, và không nói kết quả hay số tiền. Gặp 3/21 FN (HL-047, HL-091, HL-097). |

## Kết luận

- **Loại judge `helpful`.** Recall = 0.30 (tp 9, fn 21): judge bỏ sót 21/30 reply mà người chấm FAIL. Precision = 1.0 nghĩa là khi judge nói FAIL thì gần như chắc chắn sai thật, nhưng nó chỉ nói FAIL rất ít. Một gate dựa vào judge này sẽ cho qua 70% reply tệ. Nguyên nhân gốc: **18/21 FN là "sai tiền"**, tức reply nói số khác ledger, mà judge chỉ đọc chữ, không đọc ledger. Lỗi này là FM-08 và đã được chấm bằng code (`ReplyMatchesLedger`, metric `reply_matches_ledger`, chặn ở min 1.0). Nguyên tắc: **tiền luôn chấm bằng code, không chấm bằng judge**.
- **Giữ judge `tone_ok`** vì đạt FLOORS, nhưng chỉ để theo dõi. Lý do: 6 FN chủ yếu là lỗi xưng hô; nên cập nhật rubric theo các case 1, 2, 3, 6 ở trên rồi calibrate lại trước khi tính tới việc dùng nó để chặn.
- **Rủi ro còn lại:** judge mới chỉ được kiểm trên dữ liệu replay đã công khai (100 dòng). Cần một tập nhãn người mới làm held-out thật, có 2 người gán độc lập, trước khi tin κ = 0.757 ngoài tập này. Ngoài ra, bất đồng H-081 cho thấy chính nhãn người cũng có thể sai.
