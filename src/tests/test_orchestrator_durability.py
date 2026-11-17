"""Test Suite — Orchestrator Host Integration, Durability & Idempotency.

Tests covering:
1. Idempotency when calling orchestrator.run_claim repeatedly on the same claim.
2. Crash injection propagation (before_effect, after_effect_before_checkpoint, after_checkpoint)
   and safe resume without double-refund or duplicate refund_committed audits.
3. Host policy enforcement through orchestrator:
   - T13: order already fully refunded -> denied with full proposal_amount & policy_denied audit.
   - T14: prior partial refund on same order -> pays only the difference while reporting full quote.
   - T07 & approval_claim_mismatch -> denied with policy_denied audit and zero ledger writes.
   - Amount conflict on retry -> failed without altering the committed refund row.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.shapes.orchestrator import run_claim
from tests.conftest import CLAIMS, WORLD


def _create_store(tmp_path: Path, name: str) -> Path:
    db_path = tmp_path / name
    init_store(db_path, WORLD, CLAIMS).close()
    return db_path


def _ledger_count(conn, claim_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    return int(row["n"])


def _policy_denied_reasons(conn, claim_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
        (claim_id,),
    ).fetchall()
    return [json.loads(row["details_json"])["reason"] for row in rows]


def test_orchestrator_idempotent_replay_keeps_single_refund(tmp_path: Path) -> None:
    """Calling orchestrator twice on the same claim (T11) must keep exactly one refund row."""
    store = _create_store(tmp_path, "idempotent.sqlite")

    first = run_claim("C-011", seed=11, store_path=str(store))
    second = run_claim("C-011", seed=22, store_path=str(store))

    assert first.status == "resolved"
    assert first.proposal_amount == 35000
    assert second.status == "resolved"
    assert second.proposal_amount == 35000
    assert len(second.refund_effects) == 1
    assert int(second.refund_effects[0]["amount_vnd"]) == 35000
    assert second.committed_audit_count == 1

    conn = connect(store)
    try:
        assert _ledger_count(conn, "C-011") == 1
        effect = get_refund(conn, "C-011")
        assert effect is not None
        assert effect["idempotency_key"] == "refund:C-011"
        assert int(effect["amount_vnd"]) == 35000
        assert committed_audit_count(conn, "C-011") == 1
    finally:
        conn.close()


def test_orchestrator_crash_after_effect_before_checkpoint_no_double_refund(tmp_path: Path) -> None:
    """Crash after writing ledger effect but before checkpoint must not double-refund on resume."""
    store = _create_store(tmp_path, "crash_after_effect.sqlite")

    with pytest.raises(InjectedCrash, match="after_effect_before_checkpoint"):
        run_claim(
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )

    conn = connect(store)
    try:
        assert _ledger_count(conn, "C-012") == 1
        assert committed_audit_count(conn, "C-012") == 1
        cp_before = conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = 'C-012' AND step = 'issue_refund'"
        ).fetchone()
        assert cp_before is None
    finally:
        conn.close()

    resumed = run_claim("C-012", seed=11, store_path=str(store), crash_at=None)
    assert resumed.status == "resolved"
    assert resumed.proposal_amount == 35000
    assert len(resumed.refund_effects) == 1
    assert int(resumed.refund_effects[0]["amount_vnd"]) == 35000
    assert resumed.committed_audit_count == 1

    conn = connect(store)
    try:
        assert _ledger_count(conn, "C-012") == 1
        assert committed_audit_count(conn, "C-012") == 1
        cp_after = conn.execute(
            "SELECT 1 FROM checkpoints WHERE claim_id = 'C-012' AND step = 'issue_refund'"
        ).fetchone()
        assert cp_after is not None
    finally:
        conn.close()


@pytest.mark.parametrize("crash_point", ["before_effect", "after_checkpoint"])
def test_orchestrator_other_crash_points_propagate_and_resume_cleanly(
    tmp_path: Path, crash_point: str
) -> None:
    """InjectedCrash must propagate at all crash points and resume cleanly to a single refund."""
    store = _create_store(tmp_path, f"crash_{crash_point}.sqlite")

    with pytest.raises(InjectedCrash, match=crash_point):
        run_claim("C-001", seed=11, store_path=str(store), crash_at=crash_point)

    conn = connect(store)
    try:
        if crash_point == "before_effect":
            assert get_refund(conn, "C-001") is None
            assert committed_audit_count(conn, "C-001") == 0
        else:
            assert _ledger_count(conn, "C-001") == 1
            assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()

    resumed = run_claim("C-001", seed=11, store_path=str(store))
    assert resumed.status == "resolved"
    assert resumed.proposal_amount == 35000
    assert len(resumed.refund_effects) == 1
    assert resumed.committed_audit_count == 1

    conn = connect(store)
    try:
        assert _ledger_count(conn, "C-001") == 1
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


def test_orchestrator_host_rejections_and_per_order_cap(tmp_path: Path) -> None:
    """Verify T13 (already refunded), T14 (difference only), and T07 (expired approval)."""
    store = _create_store(tmp_path, "host_policy.sqlite")

    # T13: O-505 already refunded 35000 -> denied with full quote & policy_denied audit
    t13 = run_claim("C-013", seed=11, store_path=str(store))
    assert t13.status == "denied"
    assert t13.proposal_amount == 35000
    assert t13.refund_effects == []
    assert t13.error_reason == "order_already_refunded"

    # T14: O-515 already refunded 30000, damage entitlement 150000 -> pays 120000 difference
    t14 = run_claim("C-014", seed=11, store_path=str(store))
    assert t14.status == "resolved"
    assert t14.proposal_amount == 150000
    assert len(t14.refund_effects) == 1
    assert int(t14.refund_effects[0]["amount_vnd"]) == 120000
    assert t14.committed_audit_count == 1

    # T07: C-007 expired approval -> denied with full quote & policy_denied audit
    t07 = run_claim("C-007", seed=11, store_path=str(store))
    assert t07.status == "denied"
    assert t07.proposal_amount == 35000
    assert t07.refund_effects == []
    assert t07.error_reason == "approval_expired"

    conn = connect(store)
    try:
        assert "order_already_refunded" in _policy_denied_reasons(conn, "C-013")
        assert "approval_expired" in _policy_denied_reasons(conn, "C-007")
    finally:
        conn.close()


def test_orchestrator_blocks_mismatched_approval_claim_and_amount_conflict(tmp_path: Path) -> None:
    """Verify approval bound to another claim (approval_claim_mismatch) and amount conflict."""
    store = _create_store(tmp_path, "mismatch_conflict.sqlite")
    conn = connect(store)
    try:
        # C-MISMATCH points to A-001 which belongs to C-001
        conn.execute(
            """
            INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
            VALUES ('C-MISMATCH', 'P-100', 'O-107', 'Trễ 4 ngày', 'CANARY_SECRET_PARENT_MISMATCH', '{}', 'A-001')
            """
        )
        conn.commit()
    finally:
        conn.close()

    mismatch = run_claim("C-MISMATCH", seed=11, store_path=str(store))
    assert mismatch.status == "denied"
    assert mismatch.proposal_amount == 35000
    assert mismatch.refund_effects == []
    assert mismatch.error_reason == "approval_claim_mismatch"

    # First commit C-001 at 35000, then simulate changed order entitlement (damage verified)
    first = run_claim("C-001", seed=11, store_path=str(store))
    assert first.status == "resolved"
    assert int(first.refund_effects[0]["amount_vnd"]) == 35000

    conn = connect(store)
    try:
        assert "approval_claim_mismatch" in _policy_denied_reasons(conn, "C-MISMATCH")
        conn.execute("UPDATE orders SET damage_verified = 1 WHERE order_id = 'O-107'")
        conn.execute("UPDATE approvals SET approved_vnd = 200000 WHERE approval_id = 'A-001'")
        conn.commit()
    finally:
        conn.close()

    conflict = run_claim("C-001", seed=11, store_path=str(store))
    assert conflict.status == "failed"
    assert conflict.error_reason == "amount_conflict"
    assert len(conflict.refund_effects) == 1
    assert int(conflict.refund_effects[0]["amount_vnd"]) == 35000
