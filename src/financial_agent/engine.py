from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Optional

from .explainer import ExplanationProvider
from .models import DecisionResult, JournalEntry
from .rules import evaluate_rules


def canonical_fingerprint(entry: JournalEntry) -> str:
    payload = {
        "id": entry.entry_id,
        "description": entry.description,
        "date": entry.date,
        "source": entry.source,
        "lines": [
            {
                "account": line.account,
                "debit": str(line.debit),
                "credit": str(line.credit),
                "memo": line.memo,
            }
            for line in entry.lines
        ],
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def decide(checks) -> str:
    errors = [
        check
        for check in checks
        if not check.passed and check.severity == "ERROR"
    ]

    warnings = [
        check
        for check in checks
        if not check.passed and check.severity == "WARNING"
    ]

    if errors:
        return "REJECT"

    if warnings:
        return "QUARANTINE"

    return "ACCEPT"


class ManualAdjustmentAgent:
    """Orchestrates deterministic validation and human-readable explanation.

    Accounting controls remain explicit deterministic rules.
    AI is an optional explanation capability and is not the source of truth.

    ``source_file`` is supplied by the application entry point when available
    so audit lineage reflects the actual input file being processed.
    """

    def __init__(
        self,
        coa,
        explanation_provider: ExplanationProvider,
        source_file: Optional[str] = None,
        tolerance: Decimal = Decimal("0.01"),
    ):
        self.coa = coa
        self.explanation_provider = explanation_provider
        self.source_file = source_file
        self.tolerance = tolerance

    def process(self, entry: JournalEntry) -> DecisionResult:
        checks = evaluate_rules(
            entry,
            self.coa,
            self.tolerance,
        )

        debit_total = sum(
            (line.debit for line in entry.lines),
            Decimal("0"),
        )

        credit_total = sum(
            (line.credit for line in entry.lines),
            Decimal("0"),
        )

        difference = debit_total - credit_total
        decision = decide(checks)

        explanation = self.explanation_provider.explain(
            entry,
            checks,
            decision,
            debit_total,
            credit_total,
        )

        source_ref = {
            "entry_id": entry.entry_id,
        }

        if self.source_file is not None:
            source_ref["file"] = self.source_file

        return DecisionResult(
            entry_id=entry.entry_id,
            decision=decision,
            fingerprint=canonical_fingerprint(entry),
            checks=checks,
            debit_total=debit_total,
            credit_total=credit_total,
            difference=difference,
            explanation=explanation,
            source_ref=source_ref,
        )