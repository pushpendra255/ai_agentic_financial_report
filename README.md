# AI Agentic Financial Reporting —

## Overview

This repo contains my implementation of the **Manual Adjustments Agent** slice from the assignment.

The agent takes the supplied manual journal adjustments, validates them against the chart of accounts, checks whether the entry is balanced, looks for invalid account references and suspicious intercompany self-reference, and then marks each entry as:

- `ACCEPT`
- `REJECT`
- `QUARANTINE`

For every entry, it also produces a plain-English explanation and audit information.

I kept the implementation focused on this one slice rather than trying to build all four financial statements within the assignment time.

## Setup

Python 3.10+ is required.

### Windows PowerShell

Create and activate a virtual environment:

    python -m venv .venv
    .venv\Scripts\Activate.ps1

Install the project and test dependencies:

    pip install -e ".[dev]"

## Run

Run the tests:

    python -m pytest -q

Run the prototype:

    python -m financial_agent.main

The application reads the files from `data/` and writes the results to `output/`.

The generated files are:

    output/
    ├── adjustment_results.json
    ├── audit_log.jsonl
    └── input_diagnostics.json

The normal run does not need an API key.

## What the prototype checks

For each manual adjustment, the validation includes:

1. Journal-entry structure and required fields
2. Debit and credit totals
3. Negative or invalid amounts
4. Referenced COA accounts
5. Whether the account can be posted to
6. Balance difference within the configured tolerance
7. Suspicious intercompany self-reference

A validation error results in `REJECT`.

A warning that needs review results in `QUARANTINE`.

An entry that passes the checks is marked `ACCEPT`.

The prototype does not automatically change accounting amounts or invent missing account mappings.

## Optional LLM explanations

The default explanation path is deterministic.

There is also an optional LLM path for improving the wording of explanations. The LLM is not used to make the accounting decision.

Set the following values in `.env`:

    OPENAI_API_KEY=
    OPENAI_MODEL=

Then run:

    python -m financial_agent.main --llm-explanations

The LLM is only given the validation result and related information needed to explain it. It cannot override the result.

## Output

### `adjustment_results.json`

Contains the result for each journal entry, including:

- entry ID
- debit and credit totals
- validation results
- decision
- explanation
- source reference
- audit identifiers

### `audit_log.jsonl`

Contains the audit events generated during processing.

### `input_diagnostics.json`

Contains observations from the supplied input data, such as duplicate accounts, orphan accounts, missing FX data and other data-quality issues.

The supplied input files are kept unchanged.

## Tests

The tests cover the main validation cases, including balanced and unbalanced entries, invalid COA references, posting-account checks, intercompany checks and input diagnostics.

Run:

    python -m pytest -q

## Repository structure

    data/                    supplied mock input files
    src/financial_agent/     application code
    tests/                   automated tests
    output/                  generated results and audit files
    ARCHITECTURE.md          architecture and production design
    REFLECTION.md            assignment reflection
    CLARIFYING_QUESTIONS.md  pre-start questions

## Scope of this submission

Only the Manual Adjustments Agent is implemented as a runnable prototype.

The `ARCHITECTURE.md` document describes how the larger reporting platform could handle:

- COA mapping
- FX translation
- intercompany elimination
- financial statement generation
- reconciliation
- release controls
- audit and statement-level lineage

Those parts are design considerations in this submission rather than implemented features.

## AI assistance

AI tools were used during development for code scaffolding, test ideas, documentation help and reviewing edge cases.

The accounting validation itself is implemented with deterministic rules. The LLM is optional and is limited to explanation wording.
