"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations


from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import dispatch, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.trace import Trace


def run_claim(claim_id: str, *, seed: int, store_path: str,
              crash_at: str | None = None) -> RunResult:
    conn = connect(store_path)
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))

    def done(status, proposal=0, reason=None):
        trace.add("decision", {"status": status, "reason": reason})
        return finish(conn, shape="single", claim_id=claim_id, seed=seed,
                      status=status, proposal_amount=proposal, budget=budget,
                      trace=trace, error_reason=reason)

    def read(name, args):
        result = dispatch(conn, budget, name, args, worker=True)
        # Never trace raw claims: ticket text can contain PII or secrets.
        trace.add("tool", {"name": name})
        return result

    try:
        claim = read("get_claim_view", {"claim_id": claim_id})
        if not claim.get("found"):
            return done("failed", reason="unknown_claim")
        if not claim.get("order_id"):
            return done("needs_info", reason="missing_order_id")

        # The MockLLM supplies simulated model usage, not a structured tool plan.
        # decide implements a bounded, evidence-based read plan around it.
        state = {}

        def decide(observation):
            complete(budget, seed=seed, purpose="decide",
                     prompt="Choose next read tool; stage=" + str(len(state)))
            name = observation.get("last_tool")
            if name:
                state[name] = observation["last_result"]
                trace.add("tool", {"name": name})
            if "lookup_order" not in state:
                return {"tool": "lookup_order", "args": {
                    "order_id": claim["order_id"], "principal_id": claim["principal_id"]}}
            view = state["lookup_order"]
            if not view.get("visible"):
                return {"final": {"status": "escalated", "reason": view.get("reason")}}
            if "compute_compensation" not in state:
                return {"tool": "compute_compensation", "args": {"order": view["order"]}}
            return {"final": {"quote": state["compute_compensation"]}}

        loop = run_react(conn, budget, observation={"claim": {"claim_id": claim_id}},
                         decide=decide, max_steps=8, worker=True)
        trace.add("react", {"stopped": loop["stopped"]})
        final = loop["final"]
        if "quote" not in final:
            return done(final.get("status", "failed"),
                        reason=final.get("reason") or final.get("error_reason"))
        quote = final["quote"]

        proposal = int(quote["amount_vnd"])
        trace.add("quote", quote)
        if proposal <= 0:
            return done("denied", reason=quote.get("reason"))
        # Full quote: the host alone subtracts previous refunds and checks approval.
        # Flush the trace before re-raising InjectedCrash so crashed trials stay auditable.
        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise
        if not outcome["ok"]:
            return done("failed" if outcome["conflict"] else "denied",
                        proposal, outcome["reason"])
        return done("resolved", proposal)
    finally:
        conn.close()
