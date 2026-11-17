# Trace case: từ trace tới quyết định sai đầu tiên

Trace case trả lời hai câu hỏi: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được bước đó ở lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-014 --seed 11
python -m lab9.trace_case --shape fixed --claim C-014 --seed 11   # đối chứng
```

## Case: `seeded_regression` C-014@11 (T14: chỉ hoàn phần chênh)

Output của lệnh trên:

```
== seeded_regression C-014@11  lab8 grader: FAIL (proposal_mismatch)
   1 handoff         {"claim_id": "C-014", "contract_version": "handoff.v1", ...}
   2 investigator    {"lookup_order": {"visible": true, "order": {"order_id": "O-515", "status": "delivered_late", ...
   3 quote           {"amount_vnd": 150000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03", "DMG-04"], ...}
   4 refund_history  {"refund_count": 1, "refunded_vnd": 30000}
   5 proposal        {"amount_vnd": 120000}
   6 reply           {"text": "Dạ, LogiX đã hoàn 120.000đ cho đơn O-515."}
  refund_vnd     ledger=90000    label=120000   <-- differs
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-014@11`. Report `E-seeded_regression-20261117-561e` (eval set `561ed6c3dcb5`), item E-014 |
| Triệu chứng | Grader Lab 8 FAIL (`proposal_mismatch`). `refund_amount_correct` FAIL: ledger ghi 90.000, nhãn là 120.000. Reply nói "đã hoàn 120.000đ" trong khi ledger chỉ có 90.000, nên `reply_matches_ledger` cũng FAIL. Đọc ledger trước reply mới thấy reply nghe trôi chảy mà vẫn sai tiền. |
| Bước sai đầu tiên | **Event 5 `proposal` `{"amount_vnd": 120000}`**. Agent tự lấy quote 150.000 trừ đi 30.000 đã hoàn trước đó. |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng contract. Event 2 `investigator` đọc đúng đơn O-515 (`delivered_late`, `damage_verified`). Event 3 `quote` = 150.000 khớp entitlement DMG-04 và lấy max chứ không cộng. Event 4 `refund_history` chỉ là lệnh đọc, nên số 30.000 là đúng. Sai bắt đầu khi agent tự trừ ở event 5. Luật nghiệp vụ ghi: truyền **quote đầy đủ** cho `issue_refund`, host tự áp trần theo đơn. Vì vậy host trừ thêm 30.000 lần nữa và ghi 90.000. |
| Failure mode | **FM-05 pre_deducted**. Triệu chứng phụ ở bước reply là FM-08 (reply nói 120.000, ledger ghi 90.000). |
| Đối chứng | `fixed` C-014@11 không có event `refund_history` hay `proposal`: sau `quote` 150.000 đi thẳng tới `reply`, ledger ghi 120.000 bằng nhãn, grader Lab 8 PASS. |
| Regression test | `src/tests/test_lab9_trace_case.py`. (1) `test_lab9_trace_case_first_wrong_step_is_the_proposal`: event `proposal` đầu tiên đứng sau đúng 4 bước `handoff, investigator, quote, refund_history` và mang 120.000; `fixed` không có `proposal`. (2) `test_lab9_trace_case_graders_catch_it_on_regression_only`: `QuoteKept`, `RefundAmountCorrect`, `ReplyMatchesLedger` đều FAIL trên `seeded_regression` và PASS trên `fixed`. Đã chạy: 2/2 pass, nằm trong job CI `-k "lab9 and not advanced"`. |
| Chưa chắc chắn | Trace không cho biết *vì sao* agent tự trừ (prompt hay logic), vì MockLLM không có reasoning. Trace chỉ chứng minh agent tự trừ. Case cũng chỉ chạy một seed; các seed 22–55 của item này fail giống hệt (report có 5/5 hàng E-014 fail), nhưng đó là do variant tất định chứ không chứng minh được với LLM thật. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không viết chung chung kiểu "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được. Ở case này test nằm trong `tests/test_lab9_trace_case.py`.
