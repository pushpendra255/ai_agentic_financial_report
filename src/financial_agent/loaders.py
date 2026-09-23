
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

from .models import COAAccount, JournalEntry, JournalLine


def _decimal(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def load_coa(path: Path) -> dict[str, COAAccount]:
    accounts: dict[str, COAAccount] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            code = str(row["account_code"]).strip()
            parent = str(row.get("parent_code", "")).strip()
            accounts[code] = COAAccount(
                account_code=code,
                account_name=str(row["account_name"]).strip(),
                account_type=str(row["account_type"]).strip(),
                parent_code=parent or None,
                statement=str(row["statement"]).strip(),
                cf_category=(str(row.get("cf_category", "")).strip() or None),
                normal_balance=(str(row.get("normal_balance", "")).strip() or None),
            )
    return accounts


def load_adjustments(path: Path) -> tuple[str, str, tuple[JournalEntry, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    period = str(payload["period"])
    functional_currency = str(payload["functional_currency"])
    entries = []
    for raw in payload["entries"]:
        lines = tuple(
            JournalLine(
                account=str(line["account"]).strip(),
                debit=_decimal(line.get("debit", 0)),
                credit=_decimal(line.get("credit", 0)),
                memo=str(line.get("memo", "")).strip(),
            )
            for line in raw.get("lines", [])
        )
        entries.append(
            JournalEntry(
                entry_id=str(raw["id"]).strip(),
                description=str(raw["description"]).strip(),
                date=str(raw["date"]).strip(),
                source=str(raw.get("source", "")).strip(),
                lines=lines,
            )
        )
    return period, functional_currency, tuple(entries)
