# <a name="_175t0jsbvida"></a>**1) Scope & goals**
- **Primary goal:** Run the full assignment lifecycle by email (no student/parent app) with minimal admin web back-office.
- **Key outcomes:**\

  - Fewer missed/late submissions via automated reminders.
  - Timely grading via teacher SLAs and reminders.
  - Clear audit trail to resolve disputes.
  - Admin visibility: per-teacher response time, submission timing, and per-term/class “3 missed” escalations.
- **Non-goals (now):** AI grading/feedback, multi-guardian support (may add later), rich branding.
# <a name="_k6upi4kyb07y"></a>**2) Roles & actors**
- **Admin/Owner:** Full override controls, receives escalations (realredshamrock@gmail.com).
- **Teacher:** Creates assignments, receives submissions, sends grades/feedback.
- **Student:** Submits work by email.
- **Parent/Guardian:** Receives announcements, reminders, grades, and late notices.
- **System:** Ingests and sends email, enforces deadlines and SLAs, writes metrics to Google Sheets.
# <a name="_qp1q0axdq3b3"></a>**3) Time & calendars**
- **Canonical timezone:** China Time (CT) for all deadlines/reminders.
- **Storage:** All timestamps stored in UTC with a tz field = CT.
- **Terms:** SPRING, SUMMER, FALL, WINTER. Each **Class** is term-scoped (e.g., “ENG7 – Fall 2025”).
# <a name="_7g6szbrwk0av"></a>**4) Data model (logical)**
**Identifiers:** All entities have a stable id (UUID). User-visible codes are short, deterministic strings.

- **Student**: {id, student\_id (human ID), first\_name, last\_name, email?, status, created\_at}
- **Parent**: {id, email, first\_name?, last\_name?, status}
- **Teacher**: {id, email (whitelisted), first\_name, last\_name, status}
- **Term**: {id, name in {SPRING,SUMMER,FALL,WINTER}, year, start\_date, end\_date}
- **Class**: {id, term\_id, name, subject?, teacher\_id, roster\_version, status}
- **Enrollment**: {id, class\_id, student\_id, parent\_id, active (bool), joined\_at, left\_at?}
  - *Note:* Term/class changes handled by creating new Class each term and new Enrollment rows.
- **Rubric (optional link)**: {id, code, name, description?}
- **Assignment**: {id, code, class\_id, title, instructions, deadline\_at (UTC), deadline\_tz='CT', rubric\_id?, created\_by\_teacher\_id, status in {SCHEDULED, ANNOUNCED, CLOSED}, grace\_days=7, created\_at}
- **Submission**: {id, assignment\_id, student\_id, received\_at (UTC), on\_time (bool), late\_reason?, status in {RECEIVED, REPLACEMENT\_REQUESTED, REJECTED, HARD\_STOP}, artifacts[]}
- **Grade**: {id, assignment\_id, student\_id, grade\_value (string/enum), feedback\_text, artifacts[], graded\_by\_teacher\_id, graded\_at (UTC)}
- **Extension**: {id, assignment\_id, student\_id, extended\_deadline\_at (UTC), reason, granted\_by\_admin\_id, created\_at}
- **EmailMessage** (ledger): {id, direction in {IN, OUT}, from, to[], cc[], subject, body\_hash, message\_id, in\_reply\_to?, headers, attachments\_meta[], processed\_at, parse\_result, linked\_entity\_type/id}
- **Reminder/Event**: {id, type, assignment\_id?, class\_id?, student\_id?, teacher\_id?, scheduled\_for, sent\_at?, status, payload}
- **Escalation**: {id, student\_id, class\_id, term\_id, trigger='MISSED\_3', count, first\_missed\_at, last\_missed\_at, notified\_admin\_at}
- **MetricsSnapshot**: denormalized aggregates for Sheets export (see §11).

**Files/Artifacts:** Stored with {storage\_key, mime\_type, size, checksum}; kept 5 years; JPEG/PDF only.
# <a name="_17cl8c5ntxl6"></a>**5) Roster & Google Sheets integration**
- **Source of truth:** One **Roster Sheet** with tabs: Students, Parents, Teachers, Classes, Enrollments, Rubrics (opt).
- **Sync policy:** On a schedule (e.g., hourly) + on-demand (admin click) → **import changes** into the system; maintain roster\_version on Class.
- **Metrics export:** Separate **Metrics Sheet** (see §11).

**Expected columns (minimal):**

- Students: student\_id, first\_name, last\_name, email?
- Parents: email, first\_name?, last\_name?
- Teachers: email, first\_name, last\_name, active
- Classes: term, year, class\_name, teacher\_email
- Enrollments: class\_name, term, year, student\_id, parent\_email, active
- Rubrics (opt): rubric\_code, name, description?

**Validation on import:** referential integrity, email formats, duplicate IDs, inactive flags.
# <a name="_smyfdgl8ym1n"></a>**6) Email interaction model**
- **Single shared address:** assignments@… (receive and send).
- **Parsing:** “light structure” (strict enough to be robust; no LLM required).
- **Accepted attachments:** JPEG, PDF; max size (configurable, e.g., 20–25MB total).
- **Threading:** System sends single-purpose, clean emails (no long chains).
- **Whitelist:** Only teacher emails listed in Teachers can create/grade.
### <a name="_l87dum8ldcmy"></a>**6.1 Teacher → Create assignment**
**Subject:** ASSIGN (any additional text allowed)\
` `**Body (key: value lines; order free):**

Title: <text>

Class: <class\_name as in Sheet>

Deadline: <YYYY-MM-DD [HH:mm]> CT

Instructions:

<free text, optional>

Rubric: <rubric\_code, optional>

**Validation & outcomes:**

- Teacher email must be whitelisted and match the class’s teacher.
- Deadline default time: 23:59 CT if time omitted.
- On success: create Assignment (SCHEDULED) → trigger Announcement.
### <a name="_tqa1o21v4waw"></a>**6.2 System → Announcement (parents + students)**
**Subject:** [Assignment <Code>] <Title> (Due <CT str>)\
` `**Body (plain & HTML):** Title, class, instructions, due date in CT (and UTC note), **submission instructions**:

To submit, email this address with:

Subject: SUBMIT <AssignmentCode>

Body must include: StudentID: <your\_student\_id>

Attach your work (PDF or JPEG only).

### <a name="_n2757gtco6u6"></a>**6.3 Student/Parent → Submit**
**Subject:** SUBMIT <AssignmentCode>\
` `**Body:** must contain a line StudentID: <ID>\
` `**Attachments:** JPEG/PDF

**Processing:**

- Match Assignment by code; match Student by ID and active Enrollment in that class/term.
- If **first** submission: create Submission with status RECEIVED, mark on\_time by comparing against **effective deadline** (deadline or extension).
- Forward a **copy to teacher** (single email containing student name/ID, timestamp, attachment list).
- If not first: auto-reply: “A submission is already on file. Contact admin to request a change.” Log as REPLACEMENT\_REQUESTED.

**After deadline (≤7 days):** accept as **Late**; mark on\_time=false.\
` `**After 7 days:** auto-reply decline; status HARD\_STOP.
### <a name="_16s26yq9n29y"></a>**6.4 Teacher → Grade**
**Subject:** GRADE <AssignmentCode> <StudentID>\
` `**Body (key: value + free text):**

Grade: <text or scale>

Feedback:

<free text>

**Attachments (optional):** annotated PDFs/ images.\
` `**Processing:** create Grade, link artifacts, email **parent + student** the results; mark student as GRADED for that assignment.
# <a name="_4s0z5i4putei"></a>**7) Reminders & SLAs**
**Pre-deadline:**

- **T-2 days (CT)** → reminder to parent + student if no Submission.RECEIVED.

**Deadline pass:**

- Send **missed notice** to parent + student for all Not Submitted; open 7-day late window.

**Grading SLA:**

- For **on-time** submissions: SLA window = **deadline → deadline + 3 days**.
- For **late** submissions: SLA window = **received\_at → received\_at + 7 days**.
- **Teacher reminders:** start at **+2 days** after SLA start, then **daily** until the student is graded. Each reminder lists all outstanding students per assignment.

**Extensions:**

- Admin may set **per-student** extended deadline (+7d standard) → recalculates “on-time” and reminder schedules.
# <a name="_wqe1sbvvnkna"></a>**8) Escalations (per term & class)**
- **Trigger:** A student reaches **3 missed assignments** **within the same Class in the same Term**.
  - “Missed” = no submission by the **end of the 7-day late window** (i.e., status Closed – No Submission).
- **Action:** Immediately email admin with: student, class, term, list of missed assignment codes/titles & dates, parent email(s).
- **Reset:** Counter resets each new Class/Term (because classes change each term).
# <a name="_4u12kzjzxxsj"></a>**9) Minimal web back-office (single admin interface)**
**Capabilities:**

- **Roster view & import:** display last import status; force re-import; show data quality warnings.
- **Assignments:** list/filter by term/class/teacher/status; open an assignment to see per-student status, submission timestamps, and grading progress.
- **Overrides:**\

  - Approve submission change (swap artifacts; log reason).
  - Grant extension (per student; pick new deadline in CT).
  - Resend any outbound email (admin-only).
  - Mark graded/ungraded with reason (e.g., offline hand-in).
- **Escalations:** queue of triggered events; “acknowledge” and add notes.
- **Delivery issues:** bounced addresses/OOO log.
- **Settings:** CT timezone confirmation, attachment size limits, grace days (default 7), reminder cadence.
# <a name="_il7izdonl43c"></a>**10) State machines**
**Assignment (per student perspective):**\
` `NOTIFIED → (submit on time) → SUBMITTED\_ON\_TIME → (grade within SLA) → GRADED\
` `NOTIFIED → (no submit) → MISSED\_DEADLINE (grace open) → (submit ≤7d) → SUBMITTED\_LATE → GRADED\
` `MISSED\_DEADLINE → (no submit >7d) → CLOSED\_NO\_SUBMISSION

**Teacher grading timer:**

- Starts at assignment **deadline** for on-time submissions; starts at received\_at for late.
- Reminder events fire until GRADED.
# <a name="_xq6qol3rcp3m"></a>**11) Metrics & Google Sheets (export schema)**
**Metrics Sheet tabs & columns:**

1. **PerTeacher\_ResponseTime**\

   1. term, year, teacher\_email, class\_name, num\_graded, mean\_hours, median\_hours, p90\_hours
   1. For each graded student:
      1. if on-time → hours = grade.graded\_at - assignment.deadline\_at
      1. if late → hours = grade.graded\_at - submission.received\_at
1. **SubmissionTiming**\

   1. term, year, class\_name, assignment\_code, student\_id, submitted (bool), on\_time (bool), hours\_relative\_to\_deadline
   1. hours\_relative\_to\_deadline = submission.received\_at - effective\_deadline (negative = early)
1. **AssignmentStatus**\

   1. term, year, class\_name, assignment\_code, title, teacher\_email, total\_enrolled, submitted\_on\_time, submitted\_late, no\_submission, graded, grading\_overdue (count)
1. **Escalations**\

   1. term, year, class\_name, student\_id, missed\_count, first\_missed\_at, last\_missed\_at, notified\_admin\_at

**Export cadence:** nightly + manual push.
# <a name="_1gbrcm52nr2y"></a>**12) Validation & error handling**
- **Teacher create:** reject if teacher not whitelisted; class not in term; malformed deadline; missing Title/Class/Deadline.
- **Submission:** reject if missing StudentID, unknown AssignmentCode, wrong class/term, wrong file type, exceeds size, arrived after hard stop.
- **Idempotency:** if the same teacher sends **identical** ASSIGN (title+class+deadline within 10 min window), flag duplicate and ask admin to merge or keep both (default: keep both, per your rule; merge available via admin).
- **Delivery failures:** log bounces; alert admin; mark parent contact “invalid” until roster fix.
- **Clock drift:** all scheduling engine uses UTC; rendering uses CT.
# <a name="_ialf1mx29q51"></a>**13) Security & privacy (pragmatic)**
- **Email allow-list** for teachers; SPF/DKIM/DMARC set on outbound domain.
- **Submission verification:** StudentID must match active Enrollment.
- **Rate limiting:** throttle inbound/outbound to avoid abuse (configurable).
- **Access:** Only admin UI accounts (minimal) and assigned teacher can view student work; no public links.
- **Retention:** 5 years fixed.
- **No AV scanning** per your call (documented risk).
# <a name="_86sjawvb08f"></a>**14) Non-functional requirements**
- **Reliability:**\

  - Inbound email handler ≥ once-only processing (queue + idempotency key = provider message\_id).
  - Scheduled jobs resilient to retries (reminder/escalation jobs idempotent).
- **Performance:** ingest/process email within <30s typical; reminder batches <5m.
- **Observability:** structured logs with correlation IDs, email message IDs; metrics on queue lag, send failures, parser failures.
- **Configurability:** grace days, reminder cadences, attachment limits, CT timezone constant.
# <a name="_djtclf8jyljm"></a>**15) Email templates (outline)**
- **Announcement:** Title, class, CT due, UTC note, instructions, “How to submit” block, support contact.
- **T-2d Reminder:** “We haven’t recorded a submission for <Student Name/ID> for . Due .” How-to-submit block.
- **Missed Deadline:** “Deadline has passed for . A 7-day late window is open until .”
- **Hard Stop:** “Late window closed on . Please contact admin for policy questions.”
- **Teacher Forward (on submit):** Student, received\_at (CT), on-time/late flag, attachments list, link to admin UI record.
- **Grading Result (to parent+student):** Grade, feedback, attachments (if any), timestamp.
- **Teacher Grading Reminder:** List outstanding students (name/ID), deadlines, SLA rule reminder.
- **Escalation to Admin:** Student, class/term, 3 missed list, parent email(s), links to ledger.
# <a name="_3zgddtovur61"></a>**16) Scheduling & jobs**
- **On assignment creation:** queue announcements; schedule T-2d checks; schedule deadline pass job.
- **At deadline:** compute per-student status; send missed notices; open late window; schedule hard-stop at +7d.
- **Grading monitors:** for each submission, compute SLA start; schedule daily reminders beginning +2d.
- **Weekly/Nightly:** exports to Sheets; bounce/OOO digest.
# <a name="_3p050h25f93t"></a>**17) TDD acceptance criteria (executable story skeletons)**
*(Representative; to be expanded into individual tests.)*

**A1 – Create & announce**

- **Given** teacher is whitelisted and class exists this term
- **When** teacher emails ASSIGN with Title/Class/Deadline (CT)
- **Then** system creates Assignment, sends announcement to all active Enrollments’ parents (+students if email), and logs EmailMessage entries.

**S1 – On-time submission**

- **Given** announcement sent and student enrolled
- **When** email arrives SUBMIT <Code> with correct StudentID and PDF
- **Then** system records first Submission as on-time, forwards to teacher, and prevents further auto-overwrites.

**S2 – Duplicate submission**

- **When** second SUBMIT arrives for same student/assignment
- **Then** auto-reply explains first counts; status REPLACEMENT\_REQUESTED; no overwrite.

**D1 – Missed & late window**

- **Given** no submission by deadline
- **When** deadline job runs
- **Then** send missed notice, late window open 7 days.
- **And** submission during window marks on\_time=false and forwards to teacher.
- **And** submission after window is rejected with hard-stop message.

**G1 – SLA for on-time**

- **Given** on-time submission
- **When** no grade by deadline+2d
- **Then** send daily teacher reminders starting at +2d until graded.

**G2 – SLA for late**

- **Given** late submission
- **When** no grade by received\_at+2d
- **Then** daily reminders until graded; overdue after +7d.

**E1 – Three missed per term/class**

- **Given** student has 2 prior CLOSED\_NO\_SUBMISSION in same Class+Term
- **When** a third assignment closes with no submission
- **Then** immediate admin escalation email with details.

**X1 – Extension**

- **When** admin grants extension to a student
- **Then** effective deadline updates; on\_time evaluation and reminder schedule recomputed.

**R1 – Metrics export**

- **Given** graded items exist
- **When** nightly export runs
- **Then** PerTeacher\_ResponseTime rows reflect correct hours calculation; SubmissionTiming rows include hours relative to deadline.

**F1 – Re-import roster**

- **When** roster changes (student leaves/joins class)
- **Then** new Enrollments apply to subsequent assignments; past assignment rosters remain historical.

**SEC1 – Whitelist enforcement**

- **When** non-whitelisted email sends ASSIGN
- **Then** action blocked; admin alerted; no assignment created.
# <a name="_njdw2gf2zkqc"></a>**18) Edge cases & policies**
- **Student without email:** Only parent receives comms; submissions can still be sent by parent with StudentID.
- **Multiple parents (future):** Model supports multiple Enrollment rows (one per parent); currently we import the single parent from Sheet.
- **Teacher hand-grading offline:** Admin can upload artifact/feedback and mark graded.
- **Bounces:** Mark parent email invalid; include in nightly digest; rely on roster fix to clear.
- **Class changes mid-term:** New Class record; historical assignments remain attached to old Class.
# <a name="_3uo4k1pbb5ny"></a>**19) Future-proofing (deferred features)**
- **AI pre-grade & feedback improvement:** Add AIReview entity, approval gate for teacher, never email parents directly without teacher approval.
- **Multiple guardians:** Expand Enrollment cardinality and announcement fan-out.
- **Virus scanning:** Optional toggle later.
- **Branding/localisation:** Templating system placeholders already in templates.
-----
If you’re happy with this, next I can slice it into **deliverable epics** with **TDD story tickets** (ready to paste into your tracker), plus a minimal **data dictionary** and **email regex/parse specs** your devs can implement 1:1.

