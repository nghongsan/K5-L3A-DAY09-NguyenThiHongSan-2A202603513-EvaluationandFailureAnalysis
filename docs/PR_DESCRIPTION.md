# Lab 9: Evaluation & Failure Analysis (cá nhân)

Core M0–M4, Advanced M5–M6 và Expert M7 đều đã xong. Chi tiết trong `docs/eval_card.md`, `docs/PRD_v1.1.md`, `docs/failure_taxonomy.md`, `docs/trace_case.md` và `docs/judge_audit.md`.

## Gate v1: `seeded_regression` bị chặn (exit 1)
```
gate: PR E-seeded_regression-20261117-561e vs main E-swarm-20261117-561e · eval set 561ed6c3dcb5
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
`fixed` cho `exit 0 — merge`. M3 `--detect` cho phát hiện 100%, báo nhầm 0%.

## Scorecard v2 (`python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json`)
```
  fixed                expect merge got merge ok          
  honest_refactor      expect merge got merge ok          
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_matches_ledger, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct, slice:adversarial/pass_rate, slice:adversarial/refund_amount_correct, slice:denial/pass_rate
  slice_regression     expect block got block ok          refund_amount_correct, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct
  flaky_regression     expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, slice:money_movement/pass_rate, slice:money_movement/refund_amount_correct
mutation score 3/3 · false alarms 0
```

## A/A (`--aa 66,77,88,99,110`)
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

## Trap (`python -m lab9.traps ...`): cả 4 đều bị chặn, gate trả exit 1 với từng file
```
trap evaluator_errors_as_nan  blocked  python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap dropped_failing_rows     blocked  python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap cherry_picked_seeds      blocked  python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
trap loosened_spec            blocked  python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
exit 0 — the gate blocked every public trap (the instructor runs more)
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
