
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class COAAccount:
    account_code: str
    account_name: str
    account_type: str
    parent_code: str | None
    statement: str
    cf_category: str | None
    normal_balance: str | None


@dataclass(frozen=True)
class JournalLine:
    account: str
    debit: Decimal
    credit: Decimal
    memo: str = ""


@dataclass(frozen=True)
class JournalEntry:
    entry_id: str
    description: str
    date: str
    source: str
    lines: tuple[JournalLine, ...]


@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str
    reason_code: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResult:
    entry_id: str
    decision: str
    fingerprint: str
    checks: list[CheckResult]
    debit_total: Decimal
    credit_total: Decimal
    difference: Decimal
    explanation: str
    source_ref: dict[str, Any]
