# One-page reflection

## What I would build with three months instead of eight hours

I would turn the prototype into a versioned reporting workflow with persistent raw-input snapshots, a configurable policy engine, a COA mapping workbench, FX controls, intercompany matching/elimination, statement generation, reconciliation checkpoints and a reviewer UI. I would also add richer lineage so an auditor can navigate from any statement cell to source rows, transformations, configuration versions and approvals.

## Where the prototype would break at scale

The small prototype assumes a single supplied entity and batch. At thousands of accounts and multi-entity consolidation, lineage volume, concurrent period processing, COA versioning, FX dependencies, intercompany matching and human-review queues become the main engineering constraints. Those areas need durable storage, partitioned processing, deterministic job IDs and strong workflow state management.

## How AI tools were used

AI assistance was used to accelerate code scaffolding, test-case generation, documentation structure and edge-case review. The accounting control boundary was kept explicit: the model is not responsible for balancing entries, inventing mappings, selecting FX rates, correcting amounts or deciding whether an entry is safe to post.

## One thing I think is easy to underestimate

The difficult part is not generating a formatted financial statement. It is preserving the chain of evidence and control state when the underlying data is incomplete or contradictory. A system that produces a plausible number but cannot prove exactly which source rows, FX rates, COA version, adjustments and approvals produced it is not suitable for audit-sensitive financial reporting.