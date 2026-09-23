
import json
from decimal import Decimal
from pathlib import Path

from financial_agent.engine import ManualAdjustmentAgent
from financial_agent.explainer import RuleBasedExplanationProvider
from financial_agent.loaders import load_adjustments, load_coa


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"


def build_agent():
    coa = load_coa(DATA / "chart_of_accounts.csv")
    return ManualAdjustmentAgent(coa, RuleBasedExplanationProvider())


def test_all_provided_entries_have_expected_control_outcomes():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    agent = build_agent()

    expected = {
        "JE-001": "ACCEPT",
        "JE-002": "REJECT",
        "JE-003": "ACCEPT",
        "JE-004": "ACCEPT",
        "JE-005": "REJECT",
        "JE-006": "ACCEPT",
        "JE-007": "ACCEPT",
        "JE-008": "QUARANTINE",
        "JE-009": "ACCEPT",
        "JE-010": "ACCEPT",
    }
    actual = {entry.entry_id: agent.process(entry).decision for entry in entries}
    assert actual == expected


def test_unbalanced_entry_is_rejected_without_auto_correction():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    result = build_agent().process(next(e for e in entries if e.entry_id == "JE-002"))
    assert result.decision == "REJECT"
    assert result.difference == Decimal("3500")
    assert "DEBIT_CREDIT_MISMATCH" in {c.reason_code for c in result.checks}
    assert result.debit_total == Decimal("28500")
    assert result.credit_total == Decimal("25000")


def test_unknown_coa_account_is_rejected():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    result = build_agent().process(next(e for e in entries if e.entry_id == "JE-005"))
    assert result.decision == "REJECT"
    check = next(c for c in result.checks if c.name == "account_existence")
    assert check.reason_code == "ACCOUNT_NOT_IN_COA"
    assert check.details["accounts"] == ["6315"]


def test_intercompany_self_reference_is_quarantined():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    result = build_agent().process(next(e for e in entries if e.entry_id == "JE-008"))
    assert result.decision == "QUARANTINE"
    check = next(c for c in result.checks if c.name == "intercompany_self_reference")
    assert check.reason_code == "INTERCOMPANY_SELF_REFERENCE"


def test_fingerprint_is_stable_for_same_entry():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    agent = build_agent()
    first = agent.process(entries[0])
    second = agent.process(entries[0])
    assert first.fingerprint == second.fingerprint


def test_balance_tolerance_is_configurable():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    entry = next(e for e in entries if e.entry_id == "JE-002")
    from decimal import Decimal
    from financial_agent.engine import ManualAdjustmentAgent
    agent = ManualAdjustmentAgent(
        load_coa(DATA / "chart_of_accounts.csv"),
        RuleBasedExplanationProvider(),
        tolerance=Decimal("4000"),
    )
    result = agent.process(entry)
    assert result.decision == "ACCEPT"


def test_audit_event_id_is_stable_for_same_decision():
    _, _, entries = load_adjustments(DATA / "manual_adjustments.json")
    agent = build_agent()
    from financial_agent.audit import audit_event_id
    first = audit_event_id(agent.process(entries[0]))
    second = audit_event_id(agent.process(entries[0]))
    assert first == second
    assert len(first) == 64
