
from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path


def inspect_inputs(data_dir: Path) -> dict:
    def read_csv(name):
        with (data_dir / name).open(encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))

    coa_rows = read_csv("chart_of_accounts.csv")
    tb_rows = read_csv("trial_balance.csv")
    prior_rows = read_csv("prior_period_tb.csv")
    fx_rows = read_csv("fx_rates.csv")

    coa_codes = {r["account_code"] for r in coa_rows}
    tb_debit = sum(Decimal(r["debit"]) for r in tb_rows)
    tb_credit = sum(Decimal(r["credit"]) for r in tb_rows)

    same_currency_counts = Counter((r["account_code"], r["currency"]) for r in tb_rows)
    duplicate_same_currency = {
        f"{code}/{currency}": count
        for (code, currency), count in same_currency_counts.items()
        if count > 1
    }

    period_end = {r["currency"] for r in fx_rows if r["rate_type"] == "period_end"}
    currencies = {r["currency"] for r in tb_rows}
    missing_period_end_rates = sorted(currencies - period_end)

    tbd = [r["account_code"] for r in coa_rows if r["cf_category"] == "TBD"]
    headers = {r["account_code"] for r in coa_rows if r["account_type"] == "Header"}
    parents = {r["parent_code"] for r in coa_rows if r["parent_code"]}
    leafless_headers = sorted(headers - {p for p in parents if p})

    prior_codes = {r["account_code"] for r in prior_rows}
    current_codes = {r["account_code"] for r in tb_rows}

    return {
        "tb_raw_debit": str(tb_debit),
        "tb_raw_credit": str(tb_credit),
        "tb_raw_difference": str(tb_debit - tb_credit),
        "tb_accounts_not_in_coa": sorted({r["account_code"] for r in tb_rows} - coa_codes),
        "duplicate_same_currency_rows": duplicate_same_currency,
        "missing_period_end_fx_currencies": missing_period_end_rates,
        "coa_ambiguous_cf_categories": tbd,
        "leafless_headers": leafless_headers,
        "prior_only_accounts": sorted(prior_codes - current_codes),
        "current_only_accounts": sorted(current_codes - prior_codes),
    }
