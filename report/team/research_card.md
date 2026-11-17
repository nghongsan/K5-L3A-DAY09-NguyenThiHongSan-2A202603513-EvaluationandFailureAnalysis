# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Mert Cemri et al. (2025), “Why Do Multi-Agent LLM Systems Fail?”, arXiv:2503.13657v3, https://arxiv.org/abs/2503.13657; nghiên cứu phân tích bộ trace MAS được gán nhãn (MAST-Data), không phải benchmark LogiX-VN. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Paper xây taxonomy MAST gồm 14 failure mode trong ba nhóm: system design issues, inter-agent misalignment và task verification; taxonomy được phát triển từ 150 trace, với kappa liên người gán nhãn 0.88. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Nguồn phân tích hơn 1.600 trace từ 7 framework MAS, nhiều model/task; kết quả không trực tiếp chứng minh một shape nào tốt hơn trên claims LogiX-VN. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | So swarm với workflow trên public set: workflow sẽ tránh lỗi kiểm chứng T02/seed 55; dự đoán pass rate tăng khoảng 1/70 trial (0.014), đồng thời cost/success giảm. Đây là giả thuyết cho bộ public nhỏ. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ MockLLM, tools, 14 public claims, seeds 11/22/33/44/55, world/policy, bảng giá và evaluator cố định; thay shape workflow ↔ swarm. Shape cũng thay control flow nên đây không phải phép cô lập topology thuần túy. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến là không đối chiếu claim với order nguồn sự thật (tương tự nhóm task verification trong MAST); đo status mismatch, pass rate/pass^5, seed variance và cost/success. Không gán nhãn MAST chính thức cho trace của lab. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json`; ví dụ `R-workflow-C-001-s11`, `R-swarm-C-002-s55`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng trên bộ public này. Workflow 70/70 (pass 1.000, pass^5 1.000, cost/success 35.30 VND); swarm 69/70 (pass 0.986, pass^5 0.929, cost/success 49.57 VND). Trial swarm fail là C-002 seed 55 (ticket nói trễ 5 ngày, order ghi 2 ngày); workflow không fail. Đây là so sánh shape, không chứng minh nguyên nhân phổ quát.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
