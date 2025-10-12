# <a name="_9hgzcka5rjeq"></a>**Epics & TDD Stories — Email‑First Assignments System**
*Last updated: 10 Oct 2025*

This plan assumes the tech decisions in the companion ADR document (Gmail API inbound/outbound, Postgres, Drive, Sheets, FastAPI, React, Google OAuth, CT as canonical).

-----
## <a name="_mu2r48v19fk5"></a>**Epic 1 — Email Ingestion (Gmail → Parser → Domain)**
**Goal:** Reliably ingest inbound email for ASSIGN / SUBMIT / GRADE; persist raw MIME; produce idempotent domain events.
### <a name="_ihj89rnz84w1"></a>**Story 1.1 — Gmail Watch + Pub/Sub webhook**
**Description:** Establish Gmail users.watch on assignments@ with Pub/Sub push to ingestion endpoint.\
` `**Acceptance Criteria:**

- Given a valid watch, when a new message arrives, then the ingestion endpoint is invoked with a historyId.
- When watch expires or errors, then renewal job recreates the watch and logs an alert.\
  ` `**TDD:**\

- Unit: watch creation/renewal logic (mock Google).
- Integration: Pub/Sub push payload → endpoint → history fetch call issued.
- Contract: retries are idempotent by Gmail Message‑ID.
### <a name="_y4j1ihjj3zpi"></a>**Story 1.2 — Fetch + Persist Raw MIME**
**AC:**

- When a history event is received, the service fetches the new message with format=raw and full.
- Raw .eml stored in Drive under /email-ledger/<yyyy>/<mm>/<message-id>.eml with checksum.
- DB row created in emails with message‑id, from/to/subject, Drive fileId.\
  ` `**TDD:** unit for MIME checksum; integration storing in Drive (mock API).
### <a name="_ndfq3av6ydje"></a>**Story 1.3 — Parser: Command Routing**
**AC:**

- Subjects matching ASSIGN, SUBMIT <Code>, GRADE <Code> <StudentID> are routed.
- Body key:value extraction is strict; missing keys → auto‑reply template with instructions.
- Non‑commands → ignore (log only).\
  ` `**TDD:** regex/spec tests for subjects; body parser tests (fuzz whitespace, casing); golden tests for sample emails.
### <a name="_7f52vhlzkgjt"></a>**Story 1.4 — ASSIGN Handler**
**AC:**

- Validates teacher allowlist; looks up Class (term/class name) per roster.
- Creates Assignment (SCHEDULED), generates AssignmentCode, schedules announcement job.
- Duplicate within 10 minutes → flagged as potential duplicate (both persisted).\
  ` `**TDD:** unit validation; integration DB writes; idempotency test by Message‑ID.
### <a name="_ffvu5hw9jx97"></a>**Story 1.5 — SUBMIT Handler**
**AC:**

- Validates AssignmentCode and StudentID belongs to active Enrollment in that Class/Term.
- Accepts first submission only; forwards to teacher; late/on‑time set by effective deadline.
- Second submission → auto‑reply; REPLACEMENT\_REQUESTED logged.\
  ` `**TDD:** fixtures for term/class/enrollment; time boundary tests; attachment allowlist tests.
### <a name="_bjh27wxhi38p"></a>**Story 1.6 — GRADE Handler**
**AC:**

- Validates teacher allowlist and student/assignment relation.
- Creates Grade with graded\_at; emails parent+student; marks per‑student status GRADED.\
  ` `**TDD:** unit validation, integration email fan‑out, ledger updated.
-----
## <a name="_kpmvivn12c7s"></a>**Epic 2 — Outbound Mailer**
**Goal:** Send high‑deliverability emails via Gmail API with templates.
### <a name="_cw79ceq835h4"></a>**Story 2.1 — Template Renderer (HTML + Text)**
**AC:**

- Templates: Announcement, T‑2d Reminder, Missed Deadline, Hard Stop, Teacher Forward (on submit), Grading Result, Teacher Reminder, Escalation to Admin.
- All timestamps show CT and UTC offset.\
  ` `**TDD:** snapshot tests of rendered templates; i18n placeholders no‑op.
### <a name="_i3b62u4yg662"></a>**Story 2.2 — Gmail Send + Ledger**
**AC:**

- Emails sent as assignments@; Message‑ID captured; DB ledger row created.
- MAILER‑DAEMON replies flag the recipient as invalid.\
  ` `**TDD:** mock Gmail send; DSN/DAEMON parsing tests.
-----
## <a name="_vvm65c8b323f"></a>**Epic 3 — Domain Core & Persistence**
**Goal:** Postgres schema + repositories for entities; transactional correctness.
### <a name="_67yxsjs2i0hf"></a>**Story 3.1 — Schema Migrations**
**AC:**

- Tables for students, parents, teachers, terms, classes, enrollments, assignments, submissions, grades, extensions, emails, events, escalations.
- Constraints and indexes per spec; Alembic migrations versioned.\
  ` `**TDD:** migration smoke tests; referential integrity tests.
### <a name="_4ppb6y2kwvmc"></a>**Story 3.2 — Effective Deadline & Status Machine**
**AC:**

- Computes per‑student effective deadline (assignment deadline or extension); exposes helpers for status transitions.\
  ` `**TDD:** boundary tests for on‑time/late; extension recompute tests.
### <a name="_prk6c71xxfj4"></a>**Story 3.3 — Idempotency & Correlation**
**AC:**

- All email‑driven commands deduped by gmail\_message\_id.
- All domain events carry correlation\_id.\
  ` `**TDD:** duplicate delivery tests.
-----
## <a name="_x9t2oyrvyo4h"></a>**Epic 4 — Scheduler & Jobs**
**Goal:** Deterministic reminder/escalation processing in CT with UTC storage.
### <a name="_u2f3q79vip02"></a>**Story 4.1 — T‑2d Reminder Job**
**AC:**

- For each assignment, at T‑2d CT, send reminder to parent+student if no submission.\
  ` `**TDD:** timezone conversion tests; idempotent re‑runs.
### <a name="_jnxwzwh5qo57"></a>**Story 4.2 — Deadline Pass Job**
**AC:**

- At deadline CT, send missed notices; open 7‑day window; schedule hard stop.\
  ` `**TDD:** students with/without submissions; partial class coverage.
### <a name="_aiceotwjij2q"></a>**Story 4.3 — Hard Stop Job (+7d)**
**AC:**

- Reject new submissions; send auto‑decline; mark CLOSED\_NO\_SUBMISSION.\
  ` `**TDD:** boundary at exactly +7d.
### <a name="_lhvan9wu99h4"></a>**Story 4.4 — Teacher SLA Reminder Job**
**AC:**

- For on‑time: SLA window = deadline→deadline+3d; start reminders at +2d from window start, then daily.
- For late: SLA window = received\_at→+7d; start reminders at +2d, then daily.\
  ` `**TDD:** windows, starts, daily cadence; stops when graded.
### <a name="_r1h4hogeh9iu"></a>**Story 4.5 — Three‑Missed Escalation (per Term/Class)**
**AC:**

- When a third CLOSED\_NO\_SUBMISSION occurs for the same student in same class+term, send immediate admin escalation.\
  ` `**TDD:** accumulation tests, reset per term/class.
-----
## <a name="_6alv38ermqid"></a>**Epic 5 — Admin Web UI (React)**
**Goal:** Minimal back‑office for visibility and overrides.
### <a name="_mwnxqbrjlwyu"></a>**Story 5.1 — Auth (Google OAuth + Allowlist)**
**AC:**

- Only allowlisted Google accounts can log in; sessions issued; logout works.\
  ` `**TDD:** e2e with mocked OAuth; unauthorized blocked.
### <a name="_c412z76dymvs"></a>**Story 5.2 — Assignment Dashboard**
**AC:**

- List assignments with filters (term/class/teacher/status); detail view shows per‑student status and timestamps.\
  ` `**TDD:** UI rendering tests; API contract tests.
### <a name="_r9flplz25a4q"></a>**Story 5.3 — Overrides: Extension & Replace Submission**
**AC:**

- Admin can grant a 7‑day extension per student; recompute reminders.
- Admin can replace first submission with a new artifact; logs reason.\
  ` `**TDD:** server API tests; optimistic UI rollback on failure.
### <a name="_m4v25f3lk0td"></a>**Story 5.4 — Resend Email & Force Status**
**AC:**

- Admin can resend any outbound; can mark graded/ungraded with reason.\
  ` `**TDD:** audit log tests; email dedupe.
### <a name="_1gqsfglwjo6g"></a>**Story 5.5 — Delivery Issues & Escalations Queue**
**AC:**

- Show bounces/invalid contacts; show escalation items; acknowledge with notes.\
  ` `**TDD:** pagination, state transitions.
-----
## <a name="_ob5s4lv183fb"></a>**Epic 6 — Google Integrations (Roster & Metrics)**
**Goal:** Import roster from Sheets; nightly metrics export.
### <a name="_cdzq6g25fcmb"></a>**Story 6.1 — Roster Importer**
**AC:**

- Hourly and manual sync; tabs validated; diffs applied; errors surfaced in UI.\
  ` `**TDD:** schema validation; referential checks; partial updates.
### <a name="_n2cyod6d42q3"></a>**Story 6.2 — Metrics Exporter**
**AC:**

- Write PerTeacher\_ResponseTime, SubmissionTiming, AssignmentStatus, Escalations tabs.
- Nightly + manual export; overwrite or append strategy documented.\
  ` `**TDD:** numeric correctness tests; sheet write mocks.
-----
## <a name="_9iaeb75cu5h6"></a>**Epic 7 — Metrics & Analytics (Backend)**
**Goal:** Compute aggregates used by exports and UI.
### <a name="_51dxd3bvqw71"></a>**Story 7.1 — Response Time Aggregation**
**AC:**

- Mean/median/p90 per teacher, per class, per term.\
  ` `**TDD:** dataset with mixed on‑time/late submissions; verify formulas.
### <a name="_or0v24nad81q"></a>**Story 7.2 — Submission Timing Distribution**
**AC:**

- Hours before/after deadline; bucket counts.\
  ` `**TDD:** boundary at 0h; bucket edges.
-----
## <a name="_exfc4crhp7yn"></a>**Epic 8 — Security & Observability**
**Goal:** Protect endpoints; log and alert meaningfully.
### <a name="_i9lbnzvclc75"></a>**Story 8.1 — Teacher Whitelist Enforcement**
**AC:**

- Only teachers in Teachers can ASSIGN/GRADE; others rejected; admin alerted.\
  ` `**TDD:** negative tests; alert payload snapshot.
### <a name="_x4zcscpdd7qn"></a>**Story 8.2 — Rate Limits & Size Limits**
**AC:**

- Per‑sender caps; attachment size enforcement; MIME allowlist.\
  ` `**TDD:** rate limiter unit tests; rejection messages.
### <a name="_7zuoyloar54c"></a>**Story 8.3 — Structured Logging & Correlation**
**AC:**

- All actions log JSON with gmail\_message\_id, assignment\_code, student\_id.\
  ` `**TDD:** log schema tests; redaction of PII where needed.
### <a name="_d8do3izah1mv"></a>**Story 8.4 — Alerts**
**AC:**

- Alerts on watch expiry, ingestion failure spikes, outbound error rate, escalation triggers.\
  ` `**TDD:** simulate conditions → webhook invoked.
-----
## <a name="_x3pbb1wi25ua"></a>**Epic 9 — Deployment & CI/CD**
**Goal:** Reproducible builds, migrations, environments.
### <a name="_ek84r1l8wmk3"></a>**Story 9.1 — CI Pipeline**
**AC:**

- Lint/typecheck/tests; coverage gate; build Docker images for backend/front‑end.\
  ` `**TDD:** failing test blocks merge; artifacts produced.
### <a name="_oiszcy980071"></a>**Story 9.2 — Migrations & Seeding**
**AC:**

- Alembic migrations applied on deploy; seed terms/classes from sample Sheets.\
  ` `**TDD:** migration rollback/forward tests.
### <a name="_6w99vi345wu"></a>**Story 9.3 — Env Config & Secrets**
**AC:**

- Use Google Secret Manager for OAuth credentials, service accounts, DB URL; twelve‑factor config.\
  ` `**TDD:** missing secret → startup fails clearly.
-----
## <a name="_wtm3eicmf391"></a>**Test Data & Fixtures**
- **Sample Roster Sheet** with two terms, two classes, 5 students, parents, teachers.
- **Email fixtures**: ASSIGN, SUBMIT, GRADE (valid/invalid/malformed); DSN bounce; OOO.
- **Time fixtures** across CT boundaries (DST irrelevant but include UTC conversions).
-----
## <a name="_fjef2g11xduv"></a>**Definition of Done (per story)**
- Tests: unit + integration (and e2e where applicable) green.
- Logs and metrics instrumented.
- Security reviewed (whitelists, size limits, rate limits where relevant).
- Documentation updated (README, runbooks, env vars).
-----
## <a name="_jby8qv4iwibq"></a>**Out‑of‑Scope (MVP)**
- Multi‑guardian fan‑out; branding; AV scanning; AI pre‑grade; external mail provider.
-----
## <a name="_76kl2e99m4qd"></a>**Delivery Order (suggested)**
1. Domain Core + Schema (Epic 3.1–3.3)
1. Gmail Ingestion (Epic 1.1–1.3)
1. Outbound Mailer + Templates (Epic 2)
1. ASSIGN/SUBMIT/GRADE handlers (Epic 1.4–1.6)
1. Scheduler & Jobs (Epic 4)
1. Admin UI Auth + Dashboard (Epic 5.1–5.2)
1. Overrides & Escalations (Epic 5.3–5.5, Epic 4.5)
1. Sheets Import/Export (Epic 6)
1. Metrics & Analytics (Epic 7)
1. Security/Observability polish (Epic 8) and CI/CD (Epic 9)

