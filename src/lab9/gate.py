"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item


def _bad_number(v) -> bool:
    return isinstance(v, float) and (math.isnan(v) or math.isinf(v))


def _graded(spec: dict, base: dict) -> list[str]:
    """Spec metrics scored per row in the baseline. A PR row missing one of them lost a grader."""
    base_keys = set().union(*(r.keys() for r in base.get("rows") or [{}]))
    return [m["id"] for m in spec.get("metrics", []) if m["id"] in base_keys]


# Lab 8's trial_pass checks the ledger amount, foreign ledger rows and forbidden substrings itself,
# so a row that passes it cannot fail these graders. A row that does was edited after grading.
_IMPLIED_BY_PASS = {"refund_amount_correct": True, "approval_bypass": False, "secret_leak": False}


def _row_problems(rep: dict, who: str, graded: list[str]) -> list[str]:
    out: list[str] = []
    holes, typed, contra = [], [], []
    for r in rep.get("rows") or []:
        rid = (r.get("item_id"), r.get("seed"))
        for m in graded:
            v = r.get(m)
            if v is None:
                holes.append((*rid, m))
            elif not isinstance(v, (bool, int)) or (not isinstance(v, bool) and v not in (0, 1)):
                typed.append((*rid, m, v))
        if r.get("pass_rate") is True:
            contra += [(*rid, m) for m, want in _IMPLIED_BY_PASS.items() if m in r and r[m] is not None and bool(r[m]) != want]
    if holes:
        out.append(f"{who}: {len(holes)} graded value(s) missing, e.g. {holes[0]} "
                   f"(a grader that did not score must not drop out of the mean)")
    if typed:
        out.append(f"{who}: {len(typed)} graded value(s) are not pass/fail, e.g. {typed[0]}")
    if contra:
        out.append(f"{who}: {len(contra)} row(s) pass Lab 8's grader yet fail a check it implies, e.g. {contra[0]}")
    return out


def new_failing_items(pr: dict, base: dict, metric: str, slice_name: str | None = None) -> list[str]:
    """Items the baseline got right on EVERY seed that the PR gets wrong on at least one seed.
    A bug moved onto other items keeps every average equal; this does not."""
    a, b = per_item(pr, metric, slice_name), per_item(base, metric, slice_name)
    return sorted(k for k, v in b.items() if v == 1.0 and k in a and a[k] < 1.0)


def new_failing_rows(pr: dict, base: dict, metric: str, slice_name: str | None = None) -> list[tuple]:
    """(item, seed) rows the baseline got right that the PR gets wrong. Valid because the harness is
    seeded and deterministic (A/A delta = 0): same seed + unchanged behaviour = same trace. A bug that
    moves from one seed to another keeps every per-item mean equal; this does not."""
    def ok(rep):
        return {(r.get("item_id"), r.get("seed")): bool(r[metric]) for r in rep.get("rows") or []
                if r.get(metric) is not None and (slice_name is None or slice_name in (r.get("slices") or []))}
    a, b = ok(pr), ok(base)
    return sorted(k for k, v in b.items() if v and a.get(k) is False)


def _report_problems(rep: dict, who: str) -> list[str]:
    """Self-consistency of one report: manifest vs rows, duplicates, NaN, grader crashes."""
    out: list[str] = []
    man = rep.get("manifest") or {}
    rows = rep.get("rows") or []
    for k, v in (rep.get("metrics") or {}).items():
        if _bad_number(v):
            out.append(f"{who}: metric {k} is {v} (a crashed grader is not a score)")
    if rep.get("evaluator_failures"):
        out.append(f"{who}: {len(rep['evaluator_failures'])} evaluator failure(s), e.g. {rep['evaluator_failures'][0]}")
    seeds = man.get("seeds") or []
    if len(set(seeds)) != len(seeds):
        out.append(f"{who}: duplicate seeds in manifest {seeds}")
    want = int(man.get("items") or 0) * len(seeds)
    if len(rows) != want:
        out.append(f"{who}: {len(rows)} rows, manifest says {man.get('items')} items x {len(seeds)} seeds = {want}")
    pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
    if len(set(pairs)) != len(pairs):
        out.append(f"{who}: {len(pairs) - len(set(pairs))} duplicated (item, seed) row(s)")
    stray = sorted({r.get("seed") for r in rows} - set(seeds))
    if stray:
        out.append(f"{who}: rows with seeds {stray} not in the manifest")
    return out


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    """Same eval-set version => every threshold may only get stricter."""
    out: list[str] = []
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        if spec.get("eval_set") != base_spec.get("eval_set"):
            return []                                        # truly a new eval set: new baseline, new thresholds
        # Renaming the version while grading the same items is a loophole, not a new eval set.
        out.append(f"ratchet: eval_set_version {base_spec.get('eval_set_version')} -> "
                   f"{spec.get('eval_set_version')} but eval_set is still {spec.get('eval_set')}")

    def cmp(kind: str, key: str, old: dict, new: dict | None) -> None:
        if new is None:
            out.append(f"ratchet: {kind} {key} removed")
            return
        if old.get("blocking") and not new.get("blocking"):
            out.append(f"ratchet: {kind} {key} no longer blocking")
        ot, nt = old.get("threshold", old), new.get("threshold", new)
        for b in ("max", "max_increase", "max_new_failing_items", "max_new_failing_rows"):
            if b in ot and (b not in nt or nt[b] > ot[b]):
                out.append(f"ratchet: {kind} {key} {b} {ot[b]} -> {nt.get(b, 'removed')}")
        if "min" in ot and ("min" not in nt or nt["min"] < ot["min"]):
            out.append(f"ratchet: {kind} {key} min {ot['min']} -> {nt.get('min', 'removed')}")
        if ot.get("no_significant_drop") and not nt.get("no_significant_drop"):
            out.append(f"ratchet: {kind} {key} dropped no_significant_drop")

    new_m = {m["id"]: m for m in spec.get("metrics", [])}
    for m in base_spec.get("metrics", []):
        cmp("metric", m["id"], m, new_m.get(m["id"]))
    new_s = {(s["name"], s["metric"]): s for s in spec.get("slices") or []}
    for s in base_spec.get("slices") or []:
        cmp("slice", f"{s['name']}/{s['metric']}", s, new_s.get((s["name"], s["metric"])))
    if not set(base_spec.get("seeds") or []) <= set(spec.get("seeds") or []):
        out.append(f"ratchet: seeds {base_spec.get('seeds')} -> {spec.get('seeds')}")
    for k in ("eval_set", "labels", "adversarial_pack"):
        if base_spec.get(k) != spec.get(k):
            out.append(f"ratchet: {k} {base_spec.get(k)} -> {spec.get(k)} on the same eval-set version")
    ob, nb = base_spec.get("bootstrap") or {}, spec.get("bootstrap") or {}
    if nb.get("confidence", 0.95) < ob.get("confidence", 0.95) or nb.get("n_resamples", 1000) < ob.get("n_resamples", 1000):
        out.append("ratchet: bootstrap confidence / n_resamples lowered")
    for k in ("rng", "method"):                               # shopping for a lucky CI
        if k in ob and nb.get(k) != ob[k]:
            out.append(f"ratchet: bootstrap {k} {ob[k]} -> {nb.get(k)}")
    if not set(base_spec.get("pass_k") or []) <= set(spec.get("pass_k") or []):
        out.append(f"ratchet: pass_k {base_spec.get('pass_k')} -> {spec.get('pass_k')}")
    return out


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = _report_problems(pr, "PR") + _report_problems(base, "baseline")
    if base_spec is not None:
        problems += _ratchet(spec, base_spec)
    pm, bm = pr.get("manifest") or {}, base.get("manifest") or {}
    if pm.get("items") != bm.get("items") or sorted(pm.get("seeds") or []) != sorted(bm.get("seeds") or []):
        problems.append(f"manifest differs from baseline: items {pm.get('items')} vs {bm.get('items')}, "
                        f"seeds {pm.get('seeds')} vs {bm.get('seeds')}")
    pr_pairs = {(r.get("item_id"), r.get("seed")) for r in pr.get("rows") or []}
    base_pairs = {(r.get("item_id"), r.get("seed")) for r in base.get("rows") or []}
    if pr_pairs != base_pairs:
        problems.append(f"(item, seed) set differs from baseline: {len(base_pairs - pr_pairs)} missing, "
                        f"{len(pr_pairs - base_pairs)} extra")
    graded = _graded(spec, base)
    for who, rep in (("PR", pr), ("baseline", base)):
        problems += _row_problems(rep, who, graded)
    base_tags = {r.get("item_id"): sorted(r.get("slices") or []) for r in base.get("rows") or []}
    retagged = sorted({r.get("item_id") for r in pr.get("rows") or []
                       if r.get("item_id") in base_tags and sorted(r.get("slices") or []) != base_tags[r.get("item_id")]})
    if retagged:
        problems.append(f"slice tags differ from baseline on {retagged[:5]}")
    # Reported metrics must be what the rows say: a hand-edited number is not evidence.
    if pr.get("rows") and not any(p.startswith("PR:") for p in problems):
        ids = [m for m in graded if m in pr["rows"][0]]
        has_cost = all("cost" in r for r in pr["rows"])
        rows = pr["rows"] if has_cost else [{**r, "cost": 0.0} for r in pr["rows"]]
        again = aggregate(rows, ids, k_values=spec.get("pass_k", []))
        if not has_cost:
            again.pop("cost_per_success", None)
        for k, v in (pr.get("metrics") or {}).items():
            w = again.get(k)
            if isinstance(v, (int, float)) and isinstance(w, (int, float)) and abs(v - w) > 5e-4:
                problems.append(f"PR: metric {k}={v} but its rows give {w}")
            elif k in again and (v is None) != (w is None):
                problems.append(f"PR: metric {k}={v} but its rows give {w}")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked: list[str] = []
    lines: list[str] = []
    bs = spec.get("bootstrap", {})
    for sl in spec.get("slices") or []:
        name, metric = sl["name"], sl["metric"]
        sid = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, slice_name=name), per_item(base, metric, slice_name=name)
        verdict, note = "ok", ""
        if not a:
            verdict, val = "missing", None
        else:
            val = round(sum(a.values()) / len(a), 4)
            if "min" in sl and val < sl["min"]:
                verdict = "fail"
            if "max" in sl and val > sl["max"]:
                verdict = "fail"
            if sl.get("no_significant_drop"):
                keys = sorted(set(a) & set(b))
                if keys:
                    d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                       n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}] n={len(keys)}"
                    if hi < 0:
                        verdict = "fail"
            if "max_new_failing_items" in sl:
                new = new_failing_items(pr, base, metric, name)
                note += f" new-fail {len(new)}"
                if len(new) > sl["max_new_failing_items"]:
                    verdict = "fail"
            if "max_new_failing_rows" in sl:
                rows = new_failing_rows(pr, base, metric, name)
                note += f" new-fail-rows {len(rows)}"
                if len(rows) > sl["max_new_failing_rows"]:
                    verdict = "fail"
        if verdict != "ok" and sl.get("blocking"):
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if sl.get("blocking") else "warn")
        th = {k: sl[k] for k in ("min", "max", "no_significant_drop", "max_new_failing_items", "max_new_failing_rows") if k in sl}
        lines.append(f"  {sid:<34} {val!s:<8} {json.dumps(th):<40} {note:<34} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if "max_new_failing_items" in th and val is not None:
            new = new_failing_items(pr, base, mid)
            note += f" new-fail {len(new)}{' ' + ','.join(new[:4]) if new else ''}"
            if len(new) > th["max_new_failing_items"]:
                verdict = "fail"
        if "max_new_failing_rows" in th and val is not None:
            rows = new_failing_rows(pr, base, mid)
            note += f" new-fail-rows {len(rows)}"
            if len(rows) > th["max_new_failing_rows"]:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
