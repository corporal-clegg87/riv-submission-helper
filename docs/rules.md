# <a name="_9mscyg9lk3r9"></a>**AI Developer Guardrails (Rules File)**
Purpose: Prevent the most frequent and harmful errors introduced by AI-generated changes. These rules are **binding** for this repo. Every PR created or assisted by an AI must comply. Where a rule conflicts with product specs, the spec wins—update this file.
## <a name="_mpbc8yfqst1d"></a>**0. Golden Principles**
1. **Do no harm.** Default to *minimal, surgical diffs* that preserve existing behavior. If in doubt, prefer adding over modifying; prefer modifying over deleting.
1. **Explain every change.** PR description must include: *intent*, *touched components*, *risk areas*, *rollback plan*.
1. **Prove it works.** Every behavioral change ships with tests that would fail before and pass after.
1. **Stay within the contract.** Never invent new APIs/flags/CLI options/configs unless the ticket requires it.
1. **Determinism first.** Outputs, migrations, builds, and tests must be deterministic and reproducible.
-----
## <a name="_k9l0hiikbgar"></a>**1. Repository Hygiene & Diffs**
- **R1. Minimal diff mandate.** Do not reformat unrelated files or reorder imports across the codebase. Touch only what the change requires.
- **R2. Preserve comments & intent.** Do not delete comments without migrating their rationale into code/docs.
- **R3. Keep public API stable.** Any change to function/class signatures that are publicly used must be feature‑flagged or versioned.
- **R4. No dead‑code drives‑by.** Do not remove code unless a failing test proves it is truly unused (coverage shows 0% and search confirms no references).
- **R5. Respect file boundaries.** Place new code in the appropriate module; do not stuff multiple responsibilities into a single file.

**AI Checklist:** Before proposing changes, fetch and read: README, CONTRIBUTING, this file, and module‑level docs. Summarize understood intent in PR.

-----
## <a name="_wtxebnjcvdwz"></a>**2. Tests & TDD**
- **T1. Mandatory test delta.** New or changed logic must have matching unit tests. Integration tests for I/O (DB, network, filesystem). End‑to‑end where flows change.
- **T2. Red→Green discipline.** Include a failing test in the PR history when feasible (commit order: failing test, implementation, refactor).
- **T3. Idempotent tests.** Tests must not rely on wall‑clock or external state; use fakes, fixtures, and time freezing.
- **T4. Mutation resistance.** For critical functions, add property‑based tests or fuzz cases (inputs near boundaries, empty, huge, invalid).
- **T5. Coverage guard.** Do not reduce coverage in changed files; add tests to retain or improve it.

**AI Checklist:** Propose tests first; generate test names from the acceptance criteria in the ticket/spec.

-----
## <a name="_5a9wlw9n8mip"></a>**3. Security Baselines**
- **S1. Input validation everywhere.** Validate and sanitize *all* external inputs; never directly interpolate into SQL/command strings.
- **S2. AuthN/Z is explicit.** Do not weaken authentication or bypass role checks. Add tests for both allowed and denied paths.
- **S3. Secrets & keys.** Never hardcode secrets, tokens, or passwords. Use the secrets manager and environment variables defined by ops. Redact in logs.
- **S4. Web security headers.** HTTP responses must include standard security headers where relevant.
- **S5. Logging hygiene.** No PII or secrets in logs; use structured logs with correlation IDs.
- **S6. Dependency discipline.** New libraries require justification, license compatibility, minimal footprint, and pinned versions.
- **S7. Rate limits & quotas.** Do not remove throttling or retries. Implement exponential backoff with jitter.

**AI Checklist:** For each external boundary (HTTP handlers, email parsing, DB, file I/O), list validations performed.

-----
## <a name="_3yif7mdcy0va"></a>**4. Reliability & Time**
- **RLY1. Timezones.** Store UTC; render in the designated canonical zone. Never compare naive datetimes.
- **RLY2. Idempotency.** Handlers for webhooks, schedulers, and email processing must be safe to run twice. Use idempotency keys.
- **RLY3. Retries.** All network calls have bounded retries with backoff; operations are atomic or compensating.
- **RLY4. Concurrency.** Guard shared resources; avoid race conditions (transactions/locks where needed).
- **RLY5. Deterministic builds.** Pin dependencies; lockfiles committed; avoid non‑deterministic codegen.
-----
## <a name="_c96obvr63r9p"></a>**5. Migrations & Data**
- **D1. No breaking migrations.** Never drop columns or tables without a two‑phase migrate (write new, backfill, switch, drop later).
- **D2. Backfills are resumable.** Batch, checkpoint, and make them idempotent. Include a dry‑run plan.
- **D3. Data shape is contract.** Do not change enums/JSON shapes without versioning and migration tests.
- **D4. Protected data.** Retention and deletion policies must be respected; never bypass soft‑delete semantics.
-----
## <a name="_lyk3v8seneoe"></a>**6. Interfaces & Emails (Project‑Specific)**
- **E1. Subject contracts are law.** Do not change subject formats (ASSIGN, SUBMIT <Code>, GRADE <Code> <StudentID>) or key:value body schema without product approval.
- **E2. Attachment policy.** Only JPEG/PDF accepted; enforce size limits; reject others with clear auto‑reply.
- **E3. CT deadlines.** All user‑facing timestamps show China Time with UTC note; scheduling uses UTC.
- **E4. Announcements are single‑purpose.** Do not thread unrelated messages; keep one clean email per event.
-----
## <a name="_fpf0qjvf9x5e"></a>**7. Parsing & LLM Use**
- **P1. Rule‑based first.** Use deterministic parsers for commands. LLMs may assist in error messaging but not in silent auto‑fixes.
- **P2. Never invent APIs.** Do not reference non‑existent libraries or endpoints. If unsure, search the repo first and propose a stub behind a feature flag.
- **P3. Diff‑aware refactors.** Before altering existing code, summarise its purpose from comments/tests and include that summary in the PR to show understanding.
- **P4. Prompt hygiene.** When using an LLM to generate code, include repo context (interfaces, types, constraints). Ask it to *conform to existing patterns and file structure*.
-----
## <a name="_booy0i2cv2ai"></a>**8. Observability & Ops**
- **O1. Structured logging only.** No print debugging in merged code. Use the logging framework; include correlation IDs.
- **O2. Metrics for new flows.** Add counters/timers for new handlers and jobs.
- **O3. Feature flags.** Gate risky changes; default off; include rollback steps.
-----
## <a name="_umd3j3qsggs5"></a>**9. Documentation & PR Discipline**
- **DOC1. Update the docs.** README, runbooks, API docs, and this rules file must reflect changes.
- **DOC2. Changelogs.** Summarize user‑visible changes and migration notes.
- **DOC3. Example first.** Add a small example or snippet in the docs for any new public API.
-----
## <a name="_ncaobvp72309"></a>**10. Review Checklist (to paste into every PR)**
- I read **README/CONTRIBUTING/RULES** and followed architecture and conventions.
- I made a **minimal diff**; no unrelated reformatting.
- I added/updated **tests** (unit/integration/e2e) and they fail before/ pass after.
- I validated **inputs** and added negative tests.
- I avoided **non‑determinism**; pinned deps; deterministic outputs.
- I maintained **idempotency** for handlers/jobs.
- I respected **security** baselines (no secrets in code/logs; headers; authz).
- I kept **email subject/body contracts** unchanged.
- I updated **docs** and provided a **rollback plan**.
-----
## <a name="_afj0tkcsp4sn"></a>**11. Auto‑Checks (CI Gate Suggestions)**
- Lint + format check (no global reformat).
- Schema drift detection (migrations required for model changes).
- Secret scan (block commits with credentials).
- Static analysis (security linters for the languages in repo).
- Test flakiness detector (retry runner; flag flaky tests).
- Dependency diff (new packages flagged for review, license check, pinning enforced).
- Commit message scanner requiring ticket IDs and PR template completion.
-----
## <a name="_afebullfy5vu"></a>**12. Examples of Violations (and Fix Patterns)**
- **Overwriting a module without reading tests:** Fix by first summarising existing behavior, writing failing tests that capture it, then refactor.
- **Inventing an API call:** Fix by finding existing service/repository, extending it, adding contract tests.
- **Non‑deterministic test using wall‑clock:** Fix by injecting a clock or freezing time.
- **Dropping a column in one step:** Fix by two‑phase migrate with backfill and clean‑up PR.
-----
## <a name="_k1e1idrlslr"></a>**13. Amendments**
Submit PRs to update these rules with rationale. Changes require approval from product owner and tech lead.

