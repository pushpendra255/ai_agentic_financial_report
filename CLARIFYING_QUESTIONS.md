# Pre-start clarifying questions

The assignment permits up to three pre-start questions. These questions are tied directly to the defects and accounting semantics present in the supplied data.

1. For COA accounts whose cash-flow category is ambiguous (`TBD`), should the production system quarantine affected reporting outputs until Finance supplies a classification, or is there an approved policy fallback?

2. For a non-functional currency with no period-end FX rate, should affected rows be blocked/quarantined until Finance provides an approved rate, or is there an approved fallback source/rate?

3. If the source trial balance remains out of balance after the supplied FX translation and input controls, should statement generation be blocked, or should the platform produce an exception-only result that clearly prevents release?

These questions do not assume an accounting answer; the system should persist the response as configuration/policy rather than infer it.