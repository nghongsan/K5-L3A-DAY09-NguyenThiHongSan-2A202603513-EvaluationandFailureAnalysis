# Lab 9: Evaluation & Failure Analysis (cá nhân)

Core M0–M4, Advanced M5–M6 và Expert M7 đều đã xong. Chi tiết trong `docs/eval_card.md`, `docs/PRD_v1.1.md`, `docs/failure_taxonomy.md`, `docs/trace_case.md` và `docs/judge_audit.md`.

## Gate v1: `seeded_regression` bị chặn (exit 1)
```
gate: PR E-seeded_regression-20261117-6337 vs main E-swarm-20261117-6337 · eval set 6337ef3bce51
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  quote_kept             0.8571   {"min": 1.0}                                                          warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_matches_ledger   0.7857   {"min": 1.0}                                                          BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_matches_ledger
```
`fixed` cho `exit 0 — merge`. M3 `python -m lab9.mutation --detect` cho phát hiện 100%, báo nhầm 0%.

## Scorecard v2 (`python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json`)
```
  fixed                expect merge got merge ok          
  honest_refactor      expect merge got merge ok          
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_matches_ledger, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct, slice:adversarial/pass_rate, slice:adversarial/refund_amount_correct, slice:denial/pass_rate
  slice_regression     expect block got block ok          refund_amount_correct, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct
  flaky_regression     expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct
mutation score 3/3 · false alarms 0
```

## A/A (`python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110`)
```
metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
quote_kept                    1.0        1.0  +0.0000
reply_matches_ledger          1.0        1.0  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```

## Trap (`python -m lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml`)
```
trap evaluator_errors_as_nan  blocked  python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap dropped_failing_rows     blocked  python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap cherry_picked_seeds      blocked  python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap loosened_spec            blocked  python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
exit 0 — the gate blocked every public trap (the instructor runs more)
```

Gate chạy trên từng file trap; cả 4 đều exit 1:
```
$ python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY PR: 27 graded value(s) missing, e.g. ('E-014', 11, 'refund_amount_correct') (a grader that did not score must not drop out of the mean)
exit 1 — blocked: integrity
$ python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY PR: 131 rows, manifest says 28 items x 5 seeds = 140
  INTEGRITY (item, seed) set differs from baseline: 9 missing, 0 extra
exit 1 — blocked: integrity
$ python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  INTEGRITY manifest differs from baseline: items 28 vs 28, seeds [22, 44] vs [11, 22, 33, 44, 55]
  INTEGRITY (item, seed) set differs from baseline: 84 missing, 0 extra
exit 1 — blocked: integrity
$ python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
  INTEGRITY ratchet: metric db_fact_kept min 0.95 -> 0.65
  INTEGRITY ratchet: metric refund_amount_correct min 0.9 -> 0.6
  INTEGRITY ratchet: metric refund_amount_correct dropped no_significant_drop
  INTEGRITY ratchet: metric pass_rate min 0.85 -> 0.55
  INTEGRITY ratchet: metric pass_rate dropped no_significant_drop
  INTEGRITY ratchet: metric pass_hat_5 min 0.8 -> 0.5
  INTEGRITY ratchet: metric quote_kept min 1.0 -> 0.7
  INTEGRITY ratchet: metric reply_matches_ledger min 1.0 -> 0.7
  INTEGRITY ratchet: slice money_movement/pass_rate removed
  INTEGRITY ratchet: slice money_movement/refund_amount_correct removed
  INTEGRITY ratchet: slice adversarial/pass_rate removed
  INTEGRITY ratchet: slice adversarial/refund_amount_correct removed
  INTEGRITY ratchet: slice denial/pass_rate removed
exit 1 — blocked: integrity
```

## Bonus: grader port sang Inspect AI (`python -m lab9.bonus_inspect`)
```
$ python -m lab9.bonus_inspect
shape                verdicts  agree  graders: approval_bypass, refund_amount_correct, reply_matches_ledger
swarm                     210    210  flagged by both: approval_bypass=0, refund_amount_correct=1, reply_matches_ledger=0
fixed                     210    210  flagged by both: approval_bypass=0, refund_amount_correct=0, reply_matches_ledger=0
seeded_regression         210    210  flagged by both: approval_bypass=0, refund_amount_correct=10, reply_matches_ledger=15
bonus_sibling_refund      210    210  flagged by both: approval_bypass=20, refund_amount_correct=20, reply_matches_ledger=0
exit 0 — Inspect AI and pydantic-evals agree on every verdict

$ python -m lab9.bonus_inspect --spec config/metric_spec_v2.yaml --shapes swarm,seeded_regression,slice_regression,flaky_regression,bonus_sibling_refund
shape                verdicts  agree  graders: approval_bypass, refund_amount_correct, reply_matches_ledger
swarm                     420    420  flagged by both: approval_bypass=0, refund_amount_correct=3, reply_matches_ledger=0
seeded_regression         420    420  flagged by both: approval_bypass=0, refund_amount_correct=30, reply_matches_ledger=40
slice_regression          420    420  flagged by both: approval_bypass=0, refund_amount_correct=9, reply_matches_ledger=0
flaky_regression          420    420  flagged by both: approval_bypass=0, refund_amount_correct=5, reply_matches_ledger=0
bonus_sibling_refund      420    420  flagged by both: approval_bypass=55, refund_amount_correct=55, reply_matches_ledger=0
exit 0 — Inspect AI and pydantic-evals agree on every verdict
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
