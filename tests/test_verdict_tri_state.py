"""
Test suite validating that System Verdict and Diagnostic Matrix evaluate correctly:
- FAILED for explicit policy violations (POLICY_VIOLATION -> FLAGGED / FAILED)
- WARNING for advisory heuristic observations (HEURISTIC_OBSERVATION -> PATTERN NOTED / WARNING)
- PASSED for compliant executions (No fault -> OK / PASSED)
"""

import json
import pytest
from epi_core.fault_analyzer import FaultAnalyzer
from epi_core.policy import EPIPolicy, PolicyRule


def _make_step(index, kind, content, timestamp="2025-01-01T00:00:00"):
    return json.dumps({"index": index, "kind": kind, "content": content, "timestamp": timestamp})


def simulate_ui_verdict(analysis):
    """Replicates the exact front-end verdict logic in app.js."""
    if not analysis:
        return "UNKNOWN", {}

    pf = analysis.primary_fault
    all_flags = ([pf] if pf else []) + analysis.secondary_flags

    # Verdict
    if analysis.fault_detected:
        is_pv = pf and (pf.fault_type == "POLICY_VIOLATION" or pf.category == "policy_violation")
        system_verdict = "FAILED" if is_pv else "WARNING"
    else:
        system_verdict = "PASSED"

    # Matrix logic
    checks = [
        {"label": "P1: Error_Continuation",  "key": "ERROR_CONTINUATION"},
        {"label": "P2: Constraint_Violation", "key": "CONSTRAINT_VIOLATION"},
        {"label": "P3: Sequence_Violation",   "key": "SEQUENCE_VIOLATION"},
        {"label": "P4: Context_Drop",         "key": "CONTEXT_DROP"},
    ]

    def matches_key(f, key):
        if not f: return False
        ft = f.fault_type or ""
        cat = f.category or ""
        rid = f.rule_id or ""
        pt = getattr(f, "policy_type", "") or ""
        if ft == key or cat == key or rid == key or pt == key: return True
        if key == "ERROR_CONTINUATION" and (rid == "P1" or ft == "ERROR_CONTINUATION"): return True
        if key == "CONSTRAINT_VIOLATION" and (rid == "P2" or ft == "CONSTRAINT_VIOLATION" or pt == "constraint_guard"): return True
        if key == "SEQUENCE_VIOLATION" and (rid == "P3" or ft == "SEQUENCE_VIOLATION" or pt == "sequence_guard"): return True
        if key == "CONTEXT_DROP" and (rid == "P4" or ft == "CONTEXT_DROP"): return True
        return False

    matrix = {}
    for ch in checks:
        flagged = any(matches_key(f, ch["key"]) for f in all_flags)
        is_heuristic = any(matches_key(f, ch["key"]) and (f.category == "heuristic_observation" or f.fault_type != "POLICY_VIOLATION") for f in all_flags)
        label = "PATTERN NOTED" if (flagged and is_heuristic) else ("FLAGGED" if flagged else "OK")
        matrix[ch["key"]] = label

    return system_verdict, matrix


class TestTriStateVerdictLogic:

    def test_case_1_clean_run_returns_passed(self):
        steps = "\n".join([
            _make_step(0, "session.start", {"workflow": "clean"}),
            _make_step(1, "tool.call", {"tool": "ping"}),
            _make_step(2, "tool.response", {"status": "pong"}),
            _make_step(3, "session.end", {"success": True}),
        ])
        analyzer = FaultAnalyzer()
        analysis = analyzer.analyze(steps)

        verdict, matrix = simulate_ui_verdict(analysis)
        assert verdict == "PASSED"
        assert matrix["ERROR_CONTINUATION"] == "OK"
        assert matrix["CONSTRAINT_VIOLATION"] == "OK"
        assert matrix["SEQUENCE_VIOLATION"] == "OK"
        assert matrix["CONTEXT_DROP"] == "OK"

    def test_case_2_heuristic_observation_returns_warning(self):
        steps = "\n".join([
            _make_step(0, "session.start", {"workflow": "heuristic"}),
            _make_step(1, "llm.request", {"messages": []}),
            _make_step(2, "llm.error", {"error": "Rate limit"}),
            _make_step(3, "llm.request", {"messages": [{"role": "user", "content": "Continue"}]}),
            _make_step(4, "session.end", {"success": True}),
        ])
        analyzer = FaultAnalyzer()
        analysis = analyzer.analyze(steps)

        verdict, matrix = simulate_ui_verdict(analysis)
        assert verdict == "WARNING"
        assert matrix["ERROR_CONTINUATION"] == "PATTERN NOTED"

    def test_case_3_formal_policy_violation_returns_failed(self):
        policy = EPIPolicy(
            system_name="test",
            system_version="1.0",
            policy_version="2025-01-01",
            rules=[
                PolicyRule(
                    id="R001",
                    name="Require Identity Verification",
                    description="Require identity verification prior to processing refunds.",
                    severity="critical",
                    type="sequence_guard",
                    must_call="verify_identity",
                    required_before="refund",
                )
            ]
        )
        steps = "\n".join([
            _make_step(0, "session.start",   {"workflow": "refund_flow"}),
            _make_step(1, "llm.request",     {"messages": [{"role": "user", "content": "Process refund"}]}),
            _make_step(2, "tool.call",       {"tool": "process_refund", "amount": 200}),
            _make_step(3, "session.end",     {"success": True}),
        ])
        analyzer = FaultAnalyzer(policy=policy)
        analysis = analyzer.analyze(steps)

        verdict, matrix = simulate_ui_verdict(analysis)
        print("DEBUG MATRIX:", matrix)
        assert verdict == "FAILED"
        assert matrix["SEQUENCE_VIOLATION"] == "FLAGGED"
