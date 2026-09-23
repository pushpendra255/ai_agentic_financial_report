from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .audit import write_audit_artifacts
from .diagnostics import inspect_inputs
from .engine import ManualAdjustmentAgent
from .explainer import OpenAIExplanationProvider, RuleBasedExplanationProvider
from .loaders import load_adjustments, load_coa


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the provided manual-adjustment batch."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing the assignment input files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where validation and audit artifacts are written.",
    )
    parser.add_argument(
        "--llm-explanations",
        action="store_true",
        help=(
            "Use the optional OpenAI adapter for wording only. "
            "Validation remains deterministic."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    adjustments_file = args.data_dir / "manual_adjustments.json"
    coa_file = args.data_dir / "chart_of_accounts.csv"

    coa = load_coa(coa_file)
    period, functional_currency, entries = load_adjustments(adjustments_file)

    diagnostics = inspect_inputs(args.data_dir)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    (args.output_dir / "input_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2),
        encoding="utf-8",
    )

    provider = RuleBasedExplanationProvider()

    if args.llm_explanations:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")

        if not api_key or not model:
            raise SystemExit(
                "LLM explanations requested but OPENAI_API_KEY "
                "and OPENAI_MODEL are not set."
            )

        from openai import OpenAI

        provider = OpenAIExplanationProvider(
            OpenAI(api_key=api_key),
            model,
        )

    agent = ManualAdjustmentAgent(
        coa=coa,
        explanation_provider=provider,
        source_file=str(adjustments_file),
    )

    results = [agent.process(entry) for entry in entries]

    write_audit_artifacts(results, args.output_dir)

    print(
        f"Period: {period} | "
        f"Functional currency: {functional_currency}"
    )

    for result in results:
        print(
            f"{result.entry_id:>6}  "
            f"{result.decision:<10} "
            f"debit={result.debit_total} "
            f"credit={result.credit_total} "
            f"diff={result.difference}"
        )

    print(f"\nWrote artifacts to {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())