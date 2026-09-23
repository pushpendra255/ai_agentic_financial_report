
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import DecisionResult


def audit_event_id(result: DecisionResult) -> str:
    """Stable audit-event identity for the same validated source decision."""
    payload = {
        "fingerprint": result.fingerprint,
        "decision": result.decision,
        "checks": [
            {"name": c.name, "passed": c.passed, "reason_code": c.reason_code, "severity": c.severity}
            for c in result.checks
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_result(result: DecisionResult) -> dict:
    return {
        "audit_event_id": audit_event_id(result),
        "entry_id": result.entry_id,
        "decision": result.decision,
        "fingerprint": result.fingerprint,
        "debit_total": str(result.debit_total),
        "credit_total": str(result.credit_total),
        "difference": str(result.difference),
        "checks": [
            {
                "name": c.name,
                "passed": c.passed,
                "severity": c.severity,
                "reason_code": c.reason_code,
                "details": c.details,
            }
            for c in result.checks
        ],
        "explanation": result.explanation,
        "source_ref": result.source_ref,
    }


def write_audit_artifacts(results: list[DecisionResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = [serialize_result(r) for r in results]
    (output_dir / "adjustment_results.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "prototype": "manual_adjustments_agent",
                "results": payload,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with (output_dir / "audit_log.jsonl").open("w", encoding="utf-8") as fh:
        for result in payload:
            fh.write(json.dumps(result, sort_keys=True) + "\n")
