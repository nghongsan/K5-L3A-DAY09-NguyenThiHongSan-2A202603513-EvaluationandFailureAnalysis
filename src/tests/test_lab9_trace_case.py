"""Regression test from docs/trace_case.md: seeded_regression C-014@11 (FM-05 pre_deducted).

First wrong step: event 5 `proposal` 120000 -- the agent subtracts the prior 30000 refund itself,
then the host caps per order and subtracts it again, so the ledger holds 90000 instead of 120000
while the reply still says 120000. Run: python -m pytest -q -m student -o addopts= -k trace_case
"""
import pytest

pytestmark = pytest.mark.student


def _ctx(case):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="trace_case", inputs={}, metadata=None, expected_output=case["label"],
                            output=case["trial"], duration=0.0, _span_tree=None, attributes={}, metrics={})


@pytest.fixture(scope="module")
def cases():
    from lab9.trace_case import investigate

    return {shape: investigate(shape, "C-014", 11) for shape in ("seeded_regression", "fixed")}


def test_lab9_trace_case_first_wrong_step_is_the_proposal(cases):
    kinds = [e["kind"] for e in cases["seeded_regression"]["trial"]["events"]]
    first = kinds.index("proposal")
    assert kinds[:first] == ["handoff", "investigator", "quote", "refund_history"]
    assert cases["seeded_regression"]["trial"]["events"][first]["payload"]["amount_vnd"] == 120000
    assert "proposal" not in [e["kind"] for e in cases["fixed"]["trial"]["events"]]


def test_lab9_trace_case_graders_catch_it_on_regression_only(cases):
    from lab9.graders import QuoteKept, RefundAmountCorrect, ReplyMatchesLedger

    bad, good = _ctx(cases["seeded_regression"]), _ctx(cases["fixed"])
    for grader in (QuoteKept(), RefundAmountCorrect(), ReplyMatchesLedger()):
        assert grader.evaluate(bad).value is False, type(grader).__name__
        assert grader.evaluate(good).value is True, type(grader).__name__
