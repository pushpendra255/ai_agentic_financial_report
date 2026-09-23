
from __future__ import annotations

from decimal import Decimal

from .models import CheckResult, DecisionResult, JournalEntry


class ExplanationProvider:
    """Interface for human-readable decision explanations."""

    def explain(
        self,
        entry: JournalEntry,
        checks: list[CheckResult],
        decision: str,
        debit_total: Decimal,
        credit_total: Decimal,
    ) -> str:
        raise NotImplementedError


class RuleBasedExplanationProvider(ExplanationProvider):
    """Deterministic fallback that requires no external model or network."""

    def explain(
        self,
        entry: JournalEntry,
        checks: list[CheckResult],
        decision: str,
        debit_total: Decimal,
        credit_total: Decimal,
    ) -> str:
        failed = [c for c in checks if not c.passed]
        if not failed:
            return (
                f"{entry.entry_id} is accepted because all deterministic validation "
                f"checks passed and debits equal credits at the configured tolerance."
            )

        messages = []
        for check in failed:
            if check.reason_code == "DEBIT_CREDIT_MISMATCH":
                diff = check.details["difference"]
                messages.append(
                    f"debits are {check.details['debit_total']} while credits are "
                    f"{check.details['credit_total']} (difference {diff})"
                )
            elif check.reason_code == "ACCOUNT_NOT_IN_COA":
                messages.append(
                    "the entry references account(s) not present in the supplied chart of accounts: "
                    + ", ".join(check.details["accounts"])
                )
            elif check.reason_code == "INTERCOMPANY_SELF_REFERENCE":
                messages.append(
                    "the same intercompany account is used on both the debit and credit sides; "
                    "the entry requires finance review rather than automatic posting"
                )
            elif check.reason_code == "HEADER_ACCOUNT_NOT_POSTABLE":
                messages.append(
                    "the entry posts directly to a COA header account: "
                    + ", ".join(check.details["accounts"])
                )
            else:
                messages.append(check.reason_code or check.name)

        prefix = (
            f"{entry.entry_id} is rejected because "
            if decision == "REJECT"
            else f"{entry.entry_id} is quarantined for human review because "
        )
        return prefix + "; ".join(messages) + "."


class OpenAIExplanationProvider(ExplanationProvider):
    """Optional LLM adapter. Deterministic validation remains authoritative.

    The adapter is intentionally optional so the prototype remains runnable
    without credentials. The LLM receives only validation facts and cannot
    change the decision.
    """

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def explain(
        self,
        entry: JournalEntry,
        checks: list[CheckResult],
        decision: str,
        debit_total: Decimal,
        credit_total: Decimal,
    ) -> str:
        facts = {
            "entry_id": entry.entry_id,
            "description": entry.description,
            "decision": decision,
            "debit_total": str(debit_total),
            "credit_total": str(credit_total),
            "failed_checks": [
                {
                    "name": c.name,
                    "reason_code": c.reason_code,
                    "details": c.details,
                }
                for c in checks if not c.passed
            ],
        }
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "Explain the supplied accounting validation result to a finance user "
                "in plain English. Do not invent facts, do not change the decision, "
                "and do not propose an accounting correction."
            ),
            input=str(facts),
        )
        return response.output_text.strip()
