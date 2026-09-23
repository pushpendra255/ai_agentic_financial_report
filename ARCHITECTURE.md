# Architecture — AI Agentic Financial Reporting

## 1. Objective

The target system is an AI-native financial reporting platform that ingests trial balances and related accounting inputs from ERP systems such as SAP or NetSuite, applies controlled accounting transformations, and produces auditable financial statements.

The system must handle the reality of financial data rather than assuming clean inputs.

Relevant inputs include:

- Trial balance
- Chart of accounts
- Manual adjustments
- Prior-period trial balance
- FX rates
- Entity and period configuration

The target reporting scope includes:

- Balance Sheet
- Profit & Loss
- Cash Flow
- Statement of Changes in Equity

The supplied assignment data intentionally contains defects such as:

- inconsistent or incomplete COA mappings
- duplicate accounts
- orphan accounts
- unbalanced trial-balance data
- invalid manual adjustments
- intercompany edge cases
- missing FX rates
- prior-period account differences

The system therefore needs deterministic controls, bounded AI usage, human review and complete audit lineage.

---

## 2. Implementation Boundary

This repository intentionally implements **one assignment slice**:

> **Manual Adjustments Agent**

The implemented prototype validates supplied manual journal entries and produces:

- validation results
- debit and credit totals
- difference
- deterministic decision
- plain-English explanation
- source reference
- stable source fingerprint
- stable audit-event ID

The implemented decisions are:

- `ACCEPT`
- `REJECT`
- `QUARANTINE`

The broader architecture described in the remaining sections is a **production design proposal**.

Components such as:

- full COA mapping
- FX translation
- intercompany elimination
- statement generation
- statement-level reconciliation
- complete statement-cell lineage

are **not claimed to be implemented by this repository**.

This separation is intentional. The assignment asks for one thoughtful end-to-end slice rather than a shallow implementation of every financial statement.

---

## 3. Problem Decomposition

A production financial reporting platform can be decomposed into the following controlled stages:

### 3.1 Input ingestion and schema validation

- ingest ERP exports and supporting files
- validate required fields
- preserve original raw inputs
- identify duplicate or malformed records

### 3.2 Currency and FX controls

- identify functional and reporting currencies
- validate period-end FX rates
- detect missing or conflicting rates
- apply only approved translation policy

### 3.3 COA normalization and mapping

- normalize source account identifiers
- map ERP accounts to reporting accounts
- detect ambiguous mappings
- assign confidence
- route uncertain mappings to human review

### 3.4 Manual adjustment validation

- validate journal-entry structure
- validate account references
- validate posting eligibility
- validate debit/credit equality
- detect suspicious intercompany patterns
- route failures to rejection or human review

### 3.5 Consolidation and intercompany processing

- identify intercompany relationships
- match reciprocal balances
- apply approved elimination rules
- preserve elimination lineage

### 3.6 Statement generation

- aggregate normalized balances
- apply statement presentation rules
- generate Balance Sheet, P&L, Cash Flow and SOCIE outputs

### 3.7 Reconciliation and verification

- verify accounting equations
- compare current and prior periods
- identify unexplained movements
- verify statement-level controls

### 3.8 Release gate

- block unresolved critical failures
- require required human approvals
- record release decision
- publish only a validated reporting snapshot

### 3.9 Audit and lineage

- preserve source references
- preserve transformation history
- preserve configuration versions
- preserve validation and approval events

---

## 4. Agent Topology

The production design uses a compact orchestrated workflow rather than a large multi-agent swarm.

```text
                    ERP / Files / Manual Inputs
                              |
                              v
                   +-------------------------+
                   | Ingestion + Schema      |
                   | Validation              |
                   +------------+------------+
                              |
              +----------------+----------------+
              |                |                |
              v                v                v
       +-------------+  +-------------+  +-------------+
       | FX Control  |  | COA Mapping |  | Adjustment  |
       |             |  | + HITL      |  | Validator   |
       +------+------+  +------+------+  +------+------+
              |                |                |
              +----------------+----------------+
                              |
                              v
                   +-------------------------+
                   | Consolidation /         |
                   | Intercompany            |
                   +------------+------------+
                              |
                              v
                   +-------------------------+
                   | Statement Builder       |
                   +------------+------------+
                              |
                              v
                   +-------------------------+
                   | Verification /          |
                   | Reconciliation          |
                   +------------+------------+
                              |
                              v
                   +-------------------------+
                   | Release Gate             |
                   +------------+------------+
                              |
                    +-------------+--------------+
                    |                            |
                    v                            v
           Financial Statements          Audit / Lineage
```

The important design choice is that each stage has a clear responsibility and deterministic boundary.

AI components assist with interpretation and explanation but do not become an uncontrolled source of accounting truth.

---

## 5. Deterministic Code vs LLM Reasoning

### 5.1 Deterministic responsibilities

The following responsibilities should remain deterministic:

- schema validation
- decimal arithmetic
- debit/credit calculation
- journal balancing
- COA account existence checks
- posting eligibility checks
- FX rate validation
- currency translation
- duplicate/source identity
- intercompany control rules
- aggregation
- reconciliation
- release gates
- audit-event identifiers
- lineage persistence
- idempotency

These controls affect financial results and therefore should be reproducible and testable.

### 5.2 Appropriate LLM responsibilities

An LLM can assist with:

- plain-English explanations of validation failures
- reviewer-facing summaries
- semantic assistance during COA mapping
- candidate mapping suggestions with evidence and confidence
- reconciliation summaries
- quarantine summaries
- natural-language explanations for human reviewers

The LLM must not be authoritative for accounting facts.

It must not:

- invent account mappings
- invent FX rates
- alter accounting amounts
- silently repair an unbalanced entry
- override deterministic validation
- decide that a failed accounting control can be ignored
- post financial adjustments

---

## 6. Implemented Prototype — Manual Adjustments Agent

The repository implements the manual-adjustment slice end-to-end.

### 6.1 Processing flow

```text
manual_adjustments.json
          |
          v
     Load Journal Entry
          |
          v
     Deterministic Rules
          |
     +----+----+----+----+
     |    |    |    |    |
     v    v    v    v    v
   Schema COA Post Balance IC Check
          |
          v
     Decision Engine
          |
     +-----+------+------+
     |            |      |
     v            v      v
  ACCEPT       REJECT  QUARANTINE
     |            |      |
     +------------+------+
                  |
                  v
        Plain-English Explanation
                  |
                  v
        Fingerprint + Audit Event
                  |
                  v
             Output Artifacts
```

### 6.2 Implemented validation rules

The prototype checks:

1. Journal-entry schema validity
2. Presence of journal-entry lines
3. Valid debit/credit values
4. Invalid negative amounts
5. Invalid simultaneous debit and credit on a single line
6. COA account existence
7. Posting-account eligibility
8. Debit and credit equality within tolerance
9. Suspicious intercompany self-reference

### 6.3 Decision policy

The decision is derived from validation severity:

```text
Any ERROR
    |
    v
 REJECT

No ERROR + WARNING
    |
    v
QUARANTINE

No ERROR + No WARNING
    |
    v
 ACCEPT
```

The decision engine does not use journal-entry IDs or other hardcoded seeded cases to determine outcomes.

---

## 7. Why the Prototype Does Not Auto-Correct Accounting Errors

An unbalanced journal entry is not a language problem.

For example:

```text
Debit  = 28,500
Credit = 25,000

Difference = 3,500
```

The system knows that the entry is invalid under the implemented balancing rule.

It does **not** know what the missing 3,500 should represent.

Automatically inventing a correction would create an accounting fact that was not present in the source data.

Therefore:

- deterministic validation identifies the defect
- the system rejects or quarantines it
- a human or approved downstream accounting workflow determines the correction
- the corrected entry must pass the validation pipeline again

This keeps accounting judgment outside the LLM.

---

## 8. Production Failure Modes

### 8.1 Hallucinated COA mappings

An LLM may produce a plausible account mapping that is semantically reasonable but incorrect according to company policy.

Controls:

- deterministic mapping rules
- mapping evidence
- confidence threshold
- versioned mapping configuration
- human approval for ambiguous mappings

The LLM can suggest candidates but cannot silently activate a new mapping.

### 8.2 Debit/credit imbalance

A journal entry may contain:

```text
Total Debits != Total Credits
```

Controls:

- deterministic Decimal arithmetic
- explicit tolerance
- blocking validation failure
- no automatic amount invention

### 8.3 Unmapped account

A source account may not exist in the configured COA.

Controls:

- deterministic existence check
- quarantine or rejection according to policy
- human mapping workflow
- re-validation after an approved mapping

### 8.4 Missing FX rate

A required currency may not have a valid period-end rate.

Controls:

- explicit FX completeness check
- no invented rate
- policy-defined fallback only when approved
- otherwise block or quarantine the affected processing scope

### 8.5 Circular or suspicious intercompany entries

Intercompany transactions may contain reciprocal entries or malformed self-references.

Controls:

- explicit intercompany rules
- matching and elimination workflow
- suspicious cases routed to human review
- complete source lineage

### 8.6 Source trial balance imbalance

The supplied trial balance may be out of balance after FX rounding or other source issues.

Controls:

- preserve the original source
- calculate and report the reconciliation difference
- do not silently force the statements to balance
- block release when the configured release policy requires reconciliation to pass

---

## 9. Validation and Self-Correction Loop

The production workflow should follow a controlled validation and self-correction loop:

```text
Validate
   |
   v
Deterministic failure?
   |
   +---- No ----> Continue
   |
   +---- Yes
           |
           v
Can an approved policy resolve the issue
without inventing accounting facts?
           |
      +----+----+
      |         |
     Yes        No
      |         |
      v         v
Apply approved  Reject /
deterministic   Quarantine
transform           |
      |             v
      |        Human review
      |             |
      +-------------+
             |
             v
        Re-run all
        validations
             |
             v
        Release only
        when gates pass

## 10. Audit Traceability

Auditability must exist at two levels.

### 10.1 Implemented prototype lineage

The implemented manual-adjustment prototype records:

```text
Journal Entry
     |
     +--> Source File
     |
     +--> Entry ID
     |
     +--> Validation Checks
     |
     +--> Decision
     |
     +--> Canonical Fingerprint
     |
     +--> Audit Event ID
     |
     +--> Explanation
```

This is the lineage actually produced by the repository.

### 10.2 Production statement lineage

For a production financial statement, the target lineage is:

```text
Statement Cell
     |
     v
Statement Line
     |
     v
Normalized Reporting Account
     |
     v
Source Record IDs
     |
     v
Source File / Input Version
     |
     +--> Currency
     |
     +--> FX Rate / FX Version
     |
     +--> Adjustment Events
     |
     +--> Mapping Version
     |
     +--> Approval Events
```

An auditor should therefore be able to start at a reported statement value and drill down to the exact source records and transformations that produced it.

Production implementation should use:

- immutable raw-input snapshots
- content hashes
- versioned configuration
- stable event IDs
- append-only audit events
- explicit approval records

The prototype demonstrates the core principle with deterministic fingerprints, audit-event IDs and source references without claiming to implement the complete production statement-lineage system.

---

## 11. Idempotency

Financial workflows must be safe to retry.

The prototype creates a canonical fingerprint from the journal-entry source content using SHA-256.

The audit-event identity is derived from:

```text
source fingerprint
+
decision
+
validation results
```

This provides a stable identity for the same processed source content.

The prototype also rewrites output artifacts on each run instead of appending duplicate audit events.

A production system should persist idempotency keys transactionally and ensure that retries cannot create duplicate postings, approvals or release events.

---

## 12. Human-in-the-Loop Workflow

Human review is a first-class workflow state rather than an exception hidden inside an LLM prompt.

A production workflow can use:

```text
RECEIVED
   |
   v
VALIDATED
   |
   +----> ACCEPTED
   |
   +----> QUARANTINED
              |
              v
         HUMAN REVIEW
            /       \
           v         v
      APPROVED    REJECTED
           |
           v
        RELEASE
```

The reviewer should see:

- original source data
- failed validation checks
- calculated values
- relevant COA context
- explanation
- policy that caused the review
- previous approval/rejection events
- lineage references

For the implemented prototype, suspicious intercompany self-reference is quarantined for human review rather than automatically accepted or corrected.

---

## 13. Supplied Data Observations

The supplied mock data intentionally contains issues that should not be sanitized before processing.

Relevant observations include:

- multi-currency trial-balance data
- duplicate account information
- an orphan account not present in the COA
- missing FX information
- ambiguous cash-flow categories
- a COA node without children
- prior-period account differences
- an unbalanced manual adjustment
- a manual adjustment referencing an account absent from the COA
- an intercompany self-reference pattern

The prototype uses the supplied manual-adjustment defects as its focused slice.

It does not modify the source files to make them clean before validation.

---

## 14. Scaling Considerations

The prototype is intentionally small, but production scale introduces several concerns.

### 14.1 Data volume

Thousands or millions of accounting rows require:

- partitioned processing
- durable storage
- efficient aggregation
- streaming or batch strategies where appropriate

### 14.2 Multi-entity processing

Consolidation requires:

- entity-specific configuration
- functional currencies
- reporting currencies
- intercompany relationships
- elimination rules

### 14.3 Configuration versioning

COA mappings, accounting policies and FX configuration can change over time.

Every reporting run therefore needs explicit versions of the configuration used.

### 14.4 Workflow state

Human review and approval cannot depend on in-memory state.

Production requires durable workflow state and recoverable job execution.

### 14.5 Observability

Production monitoring should capture:

- processing status
- validation failures
- quarantine volume
- review latency
- reconciliation differences
- FX failures
- mapping changes
- release-gate failures

### 14.6 Audit retention

Audit records must be retained according to the applicable organizational and regulatory requirements and must remain linked to the exact reporting snapshot.

---

## 15. Release Gate

Financial statements should not be released merely because a statement can be generated.

A production release gate should evaluate:

- input completeness
- schema validation
- COA mapping completeness
- FX completeness
- adjustment validation
- intercompany processing
- reconciliation results
- required human approvals
- unresolved critical exceptions
- lineage completeness

Conceptually:

```text
All required controls pass?
        |
   +----+----+
   |         |
  Yes        No
   |         |
   v         v
RELEASE    BLOCK
```

The release gate is deterministic and policy-driven.

An LLM should not be allowed to override it.

---

## 16. Why This Topology

The objective is not to maximize the number of agents.

A large agent swarm would increase:

- nondeterminism
- debugging complexity
- audit difficulty
- state-management overhead
- opportunities for hallucinated accounting decisions

A compact orchestrated workflow is more appropriate because accounting controls require reproducibility and traceability.

Agentic behavior is most valuable where the system needs to:

- interpret ambiguous information
- summarize evidence
- propose candidates
- coordinate human review
- explain exceptions

Deterministic code remains responsible for financial facts and control decisions.

---

## 17. Summary

The proposed production architecture combines:

- deterministic accounting controls
- bounded LLM assistance
- explicit human review
- versioned configuration
- strong audit lineage
- idempotent processing
- reconciliation and release gates

The implemented repository demonstrates these principles through the manual-adjustment validation slice.

The key architectural boundary is:

> **AI can assist with interpretation and explanation, but financial facts, accounting calculations, control decisions and release authority remain deterministic and auditable.**