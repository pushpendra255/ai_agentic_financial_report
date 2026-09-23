
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .models import COAAccount, JournalEntry, CheckResult


ZERO = Decimal("0")
TOLERANCE = Decimal("0.01")


def schema_check(entry: JournalEntry) -> CheckResult:
    if not entry.entry_id:
        return CheckResult("schema", False, "ERROR", "MISSING_ENTRY_ID")
    if not entry.lines:
        return CheckResult("schema", False, "ERROR", "NO_LINES")
    for index, line in enumerate(entry.lines, start=1):
        if line.debit < ZERO or line.credit < ZERO:
            return CheckResult(
                "schema", False, "ERROR", "NEGATIVE_AMOUNT",
                {"line": index, "debit": str(line.debit), "credit": str(line.credit)}
            )
        if line.debit > ZERO and line.credit > ZERO:
            return CheckResult(
                "schema", False, "ERROR", "LINE_HAS_BOTH_DEBIT_AND_CREDIT",
                {"line": index}
            )
    return CheckResult("schema", True, "INFO")


def accounts_exist_check(entry: JournalEntry, coa: dict[str, COAAccount]) -> CheckResult:
    missing = sorted({line.account for line in entry.lines if line.account not in coa})
    if missing:
        return CheckResult(
            "account_existence", False, "ERROR", "ACCOUNT_NOT_IN_COA",
            {"accounts": missing}
        )
    return CheckResult("account_existence", True, "INFO")


def posting_account_check(entry: JournalEntry, coa: dict[str, COAAccount]) -> CheckResult:
    headers = sorted({
        line.account for line in entry.lines
        if line.account in coa and coa[line.account].account_type.lower() == "header"
    })
    if headers:
        return CheckResult(
            "posting_account", False, "ERROR", "HEADER_ACCOUNT_NOT_POSTABLE",
            {"accounts": headers}
        )
    return CheckResult("posting_account", True, "INFO")


def balance_check(entry: JournalEntry, tolerance: Decimal = TOLERANCE) -> CheckResult:
    debit = sum((line.debit for line in entry.lines), ZERO)
    credit = sum((line.credit for line in entry.lines), ZERO)
    difference = debit - credit
    passed = abs(difference) <= tolerance
    return CheckResult(
        "balance",
        passed,
        "INFO" if passed else "ERROR",
        None if passed else "DEBIT_CREDIT_MISMATCH",
        {
            "debit_total": str(debit),
            "credit_total": str(credit),
            "difference": str(difference),
            "tolerance": str(tolerance),
        },
    )


def intercompany_self_reference_check(
    entry: JournalEntry, coa: dict[str, COAAccount]
) -> CheckResult:
    # Data-driven: do not hardcode a particular account code.
    ic_accounts = {
        line.account
        for line in entry.lines
        if line.account in coa
        and "intercompany" in coa[line.account].account_name.lower()
    }
    if not ic_accounts:
        return CheckResult("intercompany_self_reference", True, "INFO")

    for account in ic_accounts:
        has_debit = any(line.account == account and line.debit > ZERO for line in entry.lines)
        has_credit = any(line.account == account and line.credit > ZERO for line in entry.lines)
        if has_debit and has_credit:
            return CheckResult(
                "intercompany_self_reference",
                False,
                "WARNING",
                "INTERCOMPANY_SELF_REFERENCE",
                {"accounts": sorted(ic_accounts)},
            )
    return CheckResult("intercompany_self_reference", True, "INFO")


def evaluate_rules(entry: JournalEntry, coa: dict[str, COAAccount], tolerance: Decimal = TOLERANCE) -> list[CheckResult]:
    checks = [schema_check(entry)]
    checks.append(accounts_exist_check(entry, coa))
    checks.append(posting_account_check(entry, coa))
    checks.append(balance_check(entry, tolerance))
    checks.append(intercompany_self_reference_check(entry, coa))
    return checks
