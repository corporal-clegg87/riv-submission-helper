# <a name="_uof1yjapqicl"></a>**Tech Decisions (ADR Pack) — Email‑First Assignments System**
*Last updated: 10 Oct 2025*
## <a name="_5uk72zuh6891"></a>**0) Context, Goals, Constraints**
- **Context:** Small education company; assignments, reminders, grading via email; minimal web admin; roster & metrics in Google Sheets.
- **Goals:** High deliverability and robust parsing using email; low ops; clear audit; per‑term/class escalations; export metrics to Google Sheets; CT as canonical deadline timezone.
- **Constraints & Preferences:**\

  - Prefer **Google Workspace**/G Suite primitives where sensible.
  - **Python** backend; **React** admin front‑end.
  - **Light structure** in email subjects/bodies; LM only if needed.
  - Simple auth; no parent portal.
-----
## <a name="_3wnm0s60izjv"></a>**1) Architecture Overview (high level)**
**Ingestion**: Gmail API watch → Pub/Sub → Ingestion service (Python on Cloud Run) → Parser → Domain services → DB (+ files to Drive) → Outbound Mailer (Gmail API send).

**Scheduling**: Cloud Scheduler → queue worker → reminder/escalation jobs.

**Storage**: Cloud SQL (PostgreSQL) for relational core; Google Drive (Shared Drive) for artifacts; Google Sheets (roster import + metrics export).

**Admin UI**: React (Vite/Next) front‑end → FastAPI backend; Google OAuth for admin login.

**Observability**: Cloud Logging + Error Reporting; structured logs with Gmail Message‑ID correlation.

-----
## <a name="_au1r88gbw82v"></a>**2) Email Ingestion & Delivery**
### <a name="_vqqwu6wcxnri"></a>**Decision E‑1: Inbound email via Gmail API + Pub/Sub on a dedicated mailbox assignments@<domain>**
- **Why**: Stays within Google suite; supports push notifications; avoids polling.
- **How**: Use users.watch to create a Gmail history watch; Pub/Sub topic triggers Cloud Run ingestion endpoint; renew watch every ~6 days.
- **Parsing surface**: The ingestion service fetches message via users.messages.get?format=full including headers/parts; stores raw MIME in Drive for audit.
- **Risks**: Watch expiry/renewal; quota limits; collaborative inbox quirks.
- **Mitigations**: Health check that auto‑renews; dead‑letter queue on failures; idempotency key = Gmail Message‑ID.
### <a name="_ts4m2fm628ms"></a>**Decision E‑2: Outbound email via Gmail API (send as assignments@)**
- **Why**: Simplicity and SPF/DKIM aligned with Google.
- **Trade‑off**: Bounce/DSN visibility is weaker than SES/SendGrid. We’ll detect MAILER‑DAEMON replies and mark addresses invalid.
- **Alternative (deferred)**: Switch outbound to SendGrid for better bounce analytics while keeping Gmail inbound.
### <a name="_f6zadjyxpxot"></a>**Subject/Body Contracts (enforced)**
- Teacher create: ASSIGN in subject; key:value body fields (Title, Class, Deadline, Instructions, Rubric?).
- Student submit: SUBMIT <AssignmentCode>; body contains StudentID: <ID>; attachments JPEG/PDF.
- Teacher grade: GRADE <AssignmentCode> <StudentID>; body Grade: and Feedback:.
-----
## <a name="_3t9tfwxv3j74"></a>**3) Data Storage Decisions**
### <a name="_csvmd47lpgmm"></a>**Decision D‑1: Cloud SQL (PostgreSQL) for core data**
- **Why**: Strong relational model (terms/classes/enrollments/assignments/submissions/grades), transactional integrity, easy analytics SQL for exports.
- **Scale fit**: Low volume (<< 10k emails/month) — Postgres is more than enough.
### <a name="_keaevuj95b4j"></a>**Decision D‑2: Google Drive (Shared Drive) for artifacts & raw email MIME**
- **Why**: Stays in Google ecosystem; simple sharing to admins; cheap.
- **Structure**: /Assignments/<AssignmentCode>/<StudentID>/submission/\* and /grades/\*; store raw.eml per message under /email-ledger/ for audit.
- **Reference**: DB stores Drive file IDs + checksums.
- **Trade‑offs**: Drive API listing rate limits; permission model managed via service account with domain‑wide delegation.
- **Alternative**: GCS bucket (easier listing, lifecycle policies). Can swap later via repository abstraction.
### <a name="_3hfxsx2a400r"></a>**Decision D‑3: Google Sheets integration**
- **Roster import** from a canonical Sheet (tabs: Students, Parents, Teachers, Classes, Enrollments, Rubrics); hourly + on‑demand; validate referential integrity.
- **Metrics export** to a separate Metrics Sheet; nightly + on‑demand.
-----
## <a name="_pfeswj8j8g9t"></a>**4) Backend Platform**
### <a name="_8jdsyeuhw17u"></a>**Decision B‑1: Python + FastAPI (HTTP + background workers)**
- **Why**: Fast dev, strong typing (Pydantic), good for webhooks; ecosystem for email/MIME.
- **Background jobs**: Use Cloud Tasks / Pub/Sub workers triggered by Scheduler for reminders and escalations.
- **Libraries**: google-api-python-client (Gmail/Drive/Sheets), google-auth, pydantic, email (stdlib) / mail-parser for MIME, sqlalchemy for Postgres.
### <a name="_b7kuk7fiduce"></a>**Decision B‑2: Time handling**
- Store UTC with explicit tz\_source='CT'; convert on render; use pendulum/zoneinfo.
### <a name="_tyjsrf8fx33u"></a>**Decision B‑3: Validation/Parsing**
- Strict key:value extraction; reject malformed; LM fallback (optional) to suggest corrections, never auto‑assume.
-----
## <a name="_f2pndc4apcxm"></a>**5) Front‑End (Admin Back‑Office)**
### <a name="_7yufjeykqg4y"></a>**Decision F‑1: React (Vite or Next.js) + component lib (shadcn/ui)**
- **Scope**: Roster import status, assignments list/detail, per‑student status, overrides (extension, replace submission), resend, delivery issues, escalations queue, settings.
- **Charts**: Minimal (response time distribution, submission timing buckets) using Recharts.
### <a name="_dz40g5ufuzp4"></a>**Decision F‑2: Auth (simple)**
- **Google OAuth 2.0** sign‑in; allowlist emails (owner + designated staff). No parent/teacher portal.
- **Session**: Backend‑issued signed cookies (short‑lived) or OAuth proxy; CSRF on mutating routes.
-----
## <a name="_633owdqh2znt"></a>**6) Scheduling & Jobs**
### <a name="_mnowuv7m49mv"></a>**Decision S‑1: Cloud Scheduler → Pub/Sub → Worker**
- Schedules: T‑2d reminders, deadline pass, hard‑stop (+7d), teacher SLA reminders (start at +2d then daily), nightly exports, watch renewals.
- Jobs idempotent by (assignment\_id, student\_id, job\_type, due\_at).
-----
## <a name="_6oaxz691rxau"></a>**7) LM Usage (optional, minimal)**
### <a name="_f300vwr1immb"></a>**Decision L‑1: No LLM for core parsing (avoid brittleness)**
- **Optional assist**: Mini ChatGPT model can:
  - Propose fixes when fields are missing/ambiguous (draft reply to teacher asking for corrected format).
  - Summarise free‑text instructions into a clean bullet list for announcement.
  - (Future) AI pre‑grade: gated by teacher approval.
- **PII**: Keep off by default; toggleable; redact emails/IDs in prompts.
-----
## <a name="_3b83nl3ed611"></a>**8) Security**
- **Teacher whitelist**: Only emails from Teachers tab may ASSIGN/GRADE.
- **Inbound hygiene**: Size limits; MIME type allowlist; strip executables; store raw but don’t execute.
- **Rate limits**: Per sender and global.
- **SPF/DKIM/DMARC**: Ensure domain auth for outbound.
- **Least privilege**: Service account scopes limited to Gmail/Drive/Sheets for assigned resources.
- **Audit**: Every email logged with message‑id, parsed fields, linked entities; immutable audit trail.
-----
## <a name="_soetm8e3q02i"></a>**9) Observability & Ops**
- **Structured logging** (JSON) with correlation: gmail\_message\_id, assignment\_code, student\_id.
- **Metrics**: ingestion latency, parse failures, send failures, watch renewal status, queue depth, job success rates.
- **Alerts**: On ingestion failure spikes; on watch expiration; on outbound error rate; on escalation triggers.
-----
## <a name="_3h55yy9dmnzn"></a>**10) Deliverability Considerations**
- **Pros (Gmail outbound)**: Simplicity, fewer moving parts.
- **Cons**: Weaker bounce analytics; potential sending limits.
- **Mitigation**: Monitor for MAILER‑DAEMON; nightly invalid‑email digest; cap daily sends (far below Workspace limits at current scale).
- **Plan B**: If deliverability becomes a risk, switch outbound to SendGrid/Postmark (keep same templates), retain Gmail inbound.
-----
## <a name="_xmt9lir92jer"></a>**11) Data Model (physical highlights)**
- PostgreSQL schemas aligning to the logical model: students, parents, teachers, terms, classes, enrollments, assignments, submissions, grades, extensions, emails, events, escalations.
- **Indexes**: (class\_id, student\_id); (assignment\_id, student\_id); (term\_id, class\_id); time‑based on deadline\_at.
- **Files**: Drive file IDs stored alongside checksums and roles (submission, grade, raw\_eml).
-----
## <a name="_hv321bpeybu1"></a>**12) Email Templates & Rendering**
- Templated in backend (Jinja2) with plain‑text + HTML; locale = EN; minimal branding placeholders for later.
- All dates rendered as CT (UTC±offset) with explicit timestamp.
-----
## <a name="_4rkhjjk36k3"></a>**13) Security/Privacy Policies (per owner’s stance)**
- Retention: 5 years; manual purge job available.
- No AV scanning (documented risk). If later required, add ClamAV or Cloud Run AV service.
-----
## <a name="_o1wc945j6edv"></a>**14) Edge Cases & Policies**
- Duplicate ASSIGN within 10 minutes → mark as potential duplicate; default keep both; admin can merge.
- Parent‑only submissions allowed (must include StudentID).
- No student email? Comms go to parent only.
- Class/term change → new class row; historical links preserved.
-----
## <a name="_2qzbpi6rmjet"></a>**15) Open Questions / Assumptions (flagged)**
- **Bounce handling:** Accept Gmail‑only approach for now? (Lower fidelity.)
- **Admin domain:** Is assignments@ under a Workspace domain we control (needed for domain‑wide delegation)?
- **Drive vs GCS:** We chose Drive; revisit if listing performance or lifecycle policies become important.
- **Auth scope:** Only owner needs UI now? Any staff? Add allowlist as needed.
-----
## <a name="_r5hdveneg9ao"></a>**16) Cutlines (MVP → Next)**
**MVP**

- Gmail inbound/outbound; parser; Postgres; Drive storage; CT‑based scheduler; admin UI with roster import status, assignment dashboard, overrides; Sheets export; escalations per term/class.

**Next**

- Deliverability improvements (outbound provider); multi‑guardian; AV scanning toggle; branding; AI pre‑grade (teacher‑approved).
-----
## <a name="_31u1tu73wj9j"></a>**17) Tooling & TDD Setup**
- **Backend**: pytest, pytest‑asyncio, factory fixtures, contract tests for parser; responses/httpretty for Google API mocks.
- **Front‑end**: Vitest + Playwright for admin UI flows.
- **CI**: GitHub Actions (lint/test/typecheck), preview deploys to Cloud Run; DB migrations via Alembic.
- **Seed data**: Sample Google Sheet; seed classes/terms; fake Gmail messages.
-----
## <a name="_3b33dp54furm"></a>**18) High‑Level Risks & Mitigations**
- **Email parsing brittleness** → enforce contracts; strict validation; helpful auto‑replies; optional LM suggestions.
- **Gmail watch lapses** → renewal cron; alarms; ingest backlog polling fallback.
- **Roster drift** → hourly sync + manual trigger; metrics stamped with roster version.
- **Timezone mistakes** → explicit CT rendering everywhere; UTC storage tests.
-----
## <a name="_n9eft7b7o5t"></a>**19) Ready for Epics & Stories (next step)**
Proposed epics: Email Ingestion, Outbound Mailer, Domain Core, Scheduler/Jobs, Admin UI, Google Integrations (Drive/Sheets), Metrics & Exports, Security/Observability, Deploy/CI. We can break each into TDD‑ready stories with acceptance criteria.


