
import csv
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"


def test_known_input_defects_are_present_and_not_sanitized():
    with (DATA / "trial_balance.csv").open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    with (DATA / "chart_of_accounts.csv").open(encoding="utf-8-sig") as fh:
        coa = {r["account_code"] for r in csv.DictReader(fh)}

    # 1110 repeats by currency; 6310 is the duplicate same-currency posting code.
    same_currency_6310 = [
        r for r in rows if r["account_code"] == "6310" and r["currency"] == "USD"
    ]
    assert len(same_currency_6310) == 2
    assert "9999" not in coa
    assert any(r["account_code"] == "9999" for r in rows)


from financial_agent.diagnostics import inspect_inputs


def test_diagnostics_detect_fx_gap_and_prior_period_difference():
    report = inspect_inputs(DATA)
    assert "GBP" in report["missing_period_end_fx_currencies"]
    assert "9999" in report["tb_accounts_not_in_coa"]
    assert "6905" in report["prior_only_accounts"]


def test_diagnostics_report_is_json_serializable():
    import json
    from financial_agent.diagnostics import inspect_inputs
    report = inspect_inputs(DATA)
    json.dumps(report)
    assert report["tb_raw_difference"] != "0"
