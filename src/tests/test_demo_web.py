"""The demo must exercise real shapes and isolate their financial state."""
import json

import pytest

from lab8.demo.web import compare, validate


@pytest.mark.parametrize('claim,mode,status,amount', [
    ('C-001', 'run', 'resolved', 35000),
    ('C-001', 'retry', 'resolved', 35000),
    ('C-001', 'crash', 'resolved', 35000),
    ('C-002', 'run', 'denied', 0),
    ('C-005', 'run', 'escalated', 0),
    ('C-007', 'run', 'denied', 0),
    ('C-014', 'run', 'resolved', 120000),
])
def test_comparison_preserves_host_rules_and_isolates_shapes(tmp_path, monkeypatch, claim, mode, status, amount):
    monkeypatch.chdir(tmp_path)
    report = compare({'claim_id': claim, 'mode': mode, 'seed': 11})
    assert {r['shape'] for r in report['rows']} == {'workflow', 'single', 'orchestrator'}
    for row in report['rows']:
        assert row['passed'], row['check_reason']
        result = row['result']
        assert result['status'] == status
        assert sum(e['amount_vnd'] for e in result['refund_effects']) == amount
        assert len(result['refund_effects']) == (1 if amount else 0)
        assert result['committed_audit_count'] == (1 if amount else 0)
        assert len(row['attempts']) == (1 if mode == 'run' else 2)
        if mode == 'crash':
            assert row['attempts'][0]['status'] == 'crashed'
            assert row['attempts'][1]['status'] == 'resolved'
    blob = json.dumps(report)
    for forbidden in ('CANARY_SECRET_', 'CANARY_INTERNAL_', 'parent_secret', 'raw_headers', '0901111222'):
        assert forbidden not in blob
    assert not list(tmp_path.iterdir()), 'Workers must not leave databases/traces in caller cwd'


@pytest.mark.parametrize('payload', [None, {}, {'seed': True}, {'seed': -1},
                                      {'seed': 1.5}, {'claim_id': '../../private'},
                                      {'mode': 'write'}, {'mode': 'crash', 'claim_id': 'C-005'}])
def test_demo_rejects_invalid_input(payload):
    if payload == {}:
        assert validate(payload) == {'claim_id': 'C-001', 'mode': 'run', 'seed': 11}
    else:
        with pytest.raises(ValueError):
            validate(payload)
