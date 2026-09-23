# AI Agentic Financial Reporting — Take-Home Prototype

## Scope

This repository implements **one assignment slice end-to-end**:

> **Manual adjustments agent** — validate journal entries, detect balance violations, identify invalid COA references and suspicious intercompany self-reference, then accept, reject, or quarantine each entry with an auditable plain-English explanation.

The assignment explicitly asks for one thoughtful slice rather than shallowly implementing all four statements. The architecture document covers the broader platform design; the runnable prototype stays deliberately narrow.

**Only the manual-adjustment validation slice is implemented and runnable in this repository. The broader financial-reporting architecture is a production design proposal, not an implementation claim.**

## Why this boundary

Financial arithmetic and control decisions are deterministic and remain in code. An LLM is optional and limited to explanation wording. It cannot create an account mapping, repair a journal entry, override a validation result, or post an adjustment.

This is intentional: the assignment evaluates knowing when **not** to use an LLM.

## Repository layout

```text
data/                    supplied mock inputs, unchanged
src/financial_agent/     prototype
tests/                   automated tests
output/                  generated results and audit artifacts
ARCHITECTURE.md          broader production architecture
REFLECTION.md            one-page reflection
CLARIFYING_QUESTIONS.md  pre-start questions