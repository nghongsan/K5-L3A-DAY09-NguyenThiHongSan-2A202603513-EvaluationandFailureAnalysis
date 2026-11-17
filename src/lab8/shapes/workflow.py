"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    try:
        conn = connect(store_path)
    except Exception as exc:  # noqa: BLE001 — contract: run_claim never raises
        return _failed_without_store(claim_id, seed, exc)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    except InjectedCrash:
        raise  # T12: the crash must surface; the trace was already flushed.
    except Exception as exc:  # noqa: BLE001 — bad row / DB error -> failed + trace, never a raw exception
        trace = Trace(make_run_id(SHAPE, claim_id, seed))
        trace.add("error", {"type": type(exc).__name__})
        try:
            return finish(
                conn,
                shape=SHAPE,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=Budget(),
                trace=trace,
                error_reason=f"internal_error:{type(exc).__name__}",
            )
        except Exception:  # noqa: BLE001 — ledger unreadable too
            return _failed_without_store(claim_id, seed, exc)
    finally:
        conn.close()


def _failed_without_store(claim_id: str, seed: int, exc: Exception) -> RunResult:
    """Last-resort result when the store itself cannot be read. Still writes a trace."""
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    trace.add("error", {"type": type(exc).__name__})
    return RunResult(
        run_id=trace.run_id,
        claim_id=claim_id,
        shape=SHAPE,
        seed=seed,
        status="failed",
        proposal_amount=0,
        refund_effects=[],
        committed_audit_count=0,
        model_calls=0,
        tool_calls=0,
        input_tokens=0,
        output_tokens=0,
        cost_estimate=0.0,
        trace_path=trace.write(),
        error_reason=f"internal_error:{type(exc).__name__}",
    )


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        # Model only drafts the reply; the prompt carries the decision, never PII or the ticket.
        complete(budget, seed=seed, purpose="draft", prompt=f"status={status} proposal={proposal}")
        trace.add("decision", {"status": status, "proposal_amount": proposal, "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    # 1. Claim through the allowlisted view. Ticket text is never parsed for facts.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("claim", {"found": False})
        return done("failed", 0, "unknown_claim")
    # Whitespace-only counts as missing. A non-empty id is used verbatim (no case/homoglyph folding),
    # so a look-alike id fails lookup and escalates instead of matching someone else's order.
    has_order_id = bool((claim["order_id"] or "").strip())
    trace.add("claim", {"found": True, "has_order_id": has_order_id})

    # 2. No order_id on the claim row -> ask for it. Never guess it from the ticket.
    if not has_order_id:
        return done("needs_info", 0, "missing_order_id")

    # 3. Ownership / existence check. Only the reason goes to the trace.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
    trace.add("lookup_order", {"visible": order_view["visible"], "reason": order_view["reason"]})
    if not order_view["visible"]:
        return done("escalated", 0, order_view["reason"])

    # 4. Quote from the order row and current policies only.
    order = order_view["order"]
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order)
    proposal = int(quote["amount_vnd"])
    trace.add(
        "quote",
        {
            "amount_vnd": proposal,
            "reason": quote["reason"],
            "clause_ids": quote["clause_ids"],
            "delay_days": order["delay_days"],
            "order_status": order["status"],
        },
    )

    # 5. Nothing owed -> denied, no host write.
    if proposal <= 0:
        return done("denied", 0, quote["reason"])

    # 6. Host gate: approval, per-order cap, idempotency. Pass the FULL quote and crash_at.
    budget.add_tool(tool_cost())
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})

    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])

    # 7. Committed (or idempotent replay of the same amount).
    return done("resolved", proposal, None)
