# RIV Assignment System - Complete Project Plan
*Email-First Assignment Management with Automated Reminders & Escalations*

## 🎯 Project Overview
**Goal**: Run the full assignment lifecycle by email with minimal admin web back-office
**Approach**: 4-Week Hybrid MVP → Production Hardening → Advanced Features
**Timeline**: 4 weeks to working system, 2-3 months to full feature set

---

## 🏗️ Architecture & Tech Decisions

### Core Architecture
- **Ingestion**: Gmail API watch → Pub/Sub → Python service → Parser → Domain → DB → Outbound Mailer
- **Storage**: Cloud SQL (PostgreSQL) + Google Drive (artifacts) + Google Sheets (roster/metrics)
- **Scheduling**: Cloud Scheduler → Pub/Sub → Worker for reminders/escalations
- **Admin UI**: React front-end → FastAPI backend → Google OAuth

### Key Tech Decisions
- **Gmail API** for inbound/outbound (stays in Google ecosystem)
- **PostgreSQL** for relational data (terms/classes/enrollments/assignments)
- **Google Drive** for file storage (raw MIME, submissions, grades)
- **CT timezone** canonical, UTC storage, explicit timezone rendering
- **Python + FastAPI** backend, React admin front-end

---

## 📋 MVP Implementation Roadmap

### Week 1-2: Essential Loop ✅
**Goal**: Teachers can assign → Students can submit → Teachers can grade

#### Database & Core Models
- [ ] PostgreSQL schema setup (migrate from SQLite)
- [ ] Core models: Assignment, Submission, Grade, EmailMessage
- [ ] Alembic migrations configured
- [ ] Basic validation and constraints

#### Email Processing Core  
- [ ] Gmail watch on assignments@rivendell-academy.co.uk
- [ ] Pub/Sub webhook endpoint
- [ ] ASSIGN email parsing (Title, Class, Deadline CT)
- [ ] SUBMIT email parsing (AssignmentCode, StudentID)
- [ ] GRADE email parsing (AssignmentCode, StudentID, Grade, Feedback)
- [ ] Basic error handling and logging

#### Admin Interface (Minimal)
- [ ] Assignment list view
- [ ] Assignment detail with submissions
- [ ] Simple authentication (dev mode)

**Success Criteria**: Complete assignment lifecycle via email

### Week 3: Production Hardening 🔒
**Goal**: Secure and reliable for production

#### Infrastructure
- [ ] Cloud SQL PostgreSQL setup
- [ ] Environment configuration
- [ ] Structured logging with correlation IDs
- [ ] Health checks and monitoring

#### Security & Validation
- [ ] Teacher allowlist enforcement
- [ ] Email validation and sanitization
- [ ] Rate limiting (per sender, global)
- [ ] Attachment validation (JPEG/PDF only, size limits)
- [ ] SPF/DKIM/DMARC for outbound domain

#### Google Drive Integration
- [ ] Raw MIME storage (/email-ledger/<yyyy>/<mm>/<message-id>.eml)
- [ ] Artifact storage (/Assignments/<Code>/<StudentID>/)
- [ ] Proper file organization and checksums

**Success Criteria**: Production-ready security and reliability

### Week 4: Automation 🤖
**Goal**: Automated reminders and escalation

#### Email Templates
- [ ] Assignment announcement template
- [ ] T-2d reminder template  
- [ ] Missed deadline template
- [ ] Teacher SLA reminder template
- [ ] Grade notification template
- [ ] Escalation admin alert template

#### Reminder System
- [ ] T-2d reminder job (Cloud Scheduler)
- [ ] Deadline pass notification job
- [ ] Teacher SLA reminder system (daily after +2d)
- [ ] Hard stop job (+7d late window)

#### Escalation System
- [ ] 3-missed assignments detection (per term/class)
- [ ] Admin escalation email with details
- [ ] Escalation tracking and acknowledgment

**Success Criteria**: Automated reminders and escalation working

---

## 📧 Email Contracts & Processing

### Teacher → Create Assignment
**Subject**: `ASSIGN`
**Body** (key:value lines):
```
Title: <text>
Class: <class_name>
Deadline: <YYYY-MM-DD [HH:mm]> CT
Instructions: <optional free text>
Rubric: <optional rubric_code>
```
**Validation**: Teacher email whitelisted, class exists in term
**Outcome**: Assignment created (SCHEDULED) → Announcement sent

### Student/Parent → Submit Work
**Subject**: `SUBMIT <AssignmentCode>`
**Body**: Must contain `StudentID: <ID>`
**Attachments**: JPEG/PDF only
**Validation**: Assignment exists, student enrolled, first submission
**Outcome**: Submission recorded → Forwarded to teacher

### Teacher → Grade Work
**Subject**: `GRADE <AssignmentCode> <StudentID>`
**Body**:
```
Grade: <text or scale>
Feedback: <free text>
```
**Attachments**: Optional annotated files
**Outcome**: Grade recorded → Results sent to parent+student

---

## 🗄️ Data Model

### Core Entities
- **Student**: {id, student_id, first_name, last_name, email?, status}
- **Parent**: {id, email, first_name?, last_name?, status}  
- **Teacher**: {id, email (whitelisted), first_name, last_name, status}
- **Term**: {id, name (SPRING/SUMMER/FALL/WINTER), year, start_date, end_date}
- **Class**: {id, term_id, name, subject?, teacher_id, roster_version, status}
- **Enrollment**: {id, class_id, student_id, parent_id, active, joined_at, left_at?}

### Assignment Entities  
- **Assignment**: {id, code, class_id, title, instructions, deadline_at (UTC), deadline_tz='CT', created_by_teacher_id, status, grace_days=7}
- **Submission**: {id, assignment_id, student_id, received_at (UTC), on_time, status, artifacts[]}
- **Grade**: {id, assignment_id, student_id, grade_value, feedback_text, graded_by_teacher_id, graded_at (UTC)}
- **Extension**: {id, assignment_id, student_id, extended_deadline_at (UTC), reason, granted_by_admin_id}

### System Entities
- **EmailMessage**: {id, direction (IN/OUT), from, to[], subject, message_id, processed_at, parse_result}
- **Reminder/Event**: {id, type, assignment_id?, scheduled_for, sent_at?, status, payload}
- **Escalation**: {id, student_id, class_id, term_id, trigger='MISSED_3', count, first_missed_at, last_missed_at}

---

## ⏰ Reminders & SLAs

### Pre-Deadline
- **T-2 days (CT)**: Reminder to parent+student if no submission

### Deadline Pass  
- **At deadline**: Missed notice to parent+student, open 7-day late window
- **+7 days**: Hard stop, reject new submissions

### Teacher SLA
- **On-time submissions**: SLA = deadline → deadline + 3 days
- **Late submissions**: SLA = received_at → received_at + 7 days  
- **Reminders**: Start at +2d after SLA start, then daily until graded

### Escalations
- **Trigger**: 3 missed assignments within same Class+Term
- **Action**: Immediate admin email with student/class/term details
- **Reset**: Counter resets each new Class/Term

---

## 🔒 Security & Validation

### Teacher Whitelist
- Only emails from Teachers table can ASSIGN/GRADE
- Others rejected with admin alert

### Email Hygiene
- Size limits (configurable, e.g., 20-25MB total)
- MIME type allowlist (JPEG/PDF only)
- Strip executables, store raw but don't execute
- Rate limits per sender and global

### Access Control
- Admin UI: Google OAuth, allowlist emails
- No parent/teacher portal (admin only)
- Audit trail: Every email logged with message-id, parsed fields

---

## 📊 Metrics & Google Sheets

### Roster Import
- **Source**: Google Sheet with tabs (Students, Parents, Teachers, Classes, Enrollments)
- **Sync**: Hourly + on-demand import
- **Validation**: Referential integrity, email formats, duplicate IDs

### Metrics Export
- **PerTeacher_ResponseTime**: term, teacher_email, class_name, num_graded, mean/median/p90 hours
- **SubmissionTiming**: term, class_name, assignment_code, student_id, on_time, hours_relative_to_deadline
- **AssignmentStatus**: term, class_name, assignment_code, total_enrolled, submitted_on_time, submitted_late, no_submission, graded
- **Escalations**: term, class_name, student_id, missed_count, first_missed_at, last_missed_at

---

## 🚀 Future Phases (Post-MVP)

### Phase 2: Advanced Features
- [ ] Google Sheets roster import automation
- [ ] Metrics export system
- [ ] Advanced admin UI (React with shadcn/ui)
- [ ] Google OAuth authentication
- [ ] CI/CD pipeline with Cloud Run

### Phase 3: Enterprise Features  
- [ ] Multi-guardian support
- [ ] AI pre-grade (teacher-approved)
- [ ] Advanced monitoring and alerting
- [ ] Virus scanning toggle
- [ ] Branding and localization

---

## 🧪 Testing Strategy

### TDD Acceptance Criteria
- **A1**: Given whitelisted teacher + existing class → ASSIGN creates assignment + sends announcement
- **S1**: Given announcement sent + enrolled student → SUBMIT records first submission as on-time
- **S2**: When second SUBMIT arrives → auto-reply explains first counts, no overwrite
- **D1**: Given no submission by deadline → deadline job sends missed notice, opens late window
- **G1**: Given on-time submission → SLA reminders start at +2d until graded
- **E1**: Given 2 prior missed + third assignment closes → immediate admin escalation

### Test Data & Fixtures
- Sample roster Sheet with 2 terms, 2 classes, 5 students, parents, teachers
- Email fixtures: ASSIGN, SUBMIT, GRADE (valid/invalid/malformed)
- Time fixtures across CT boundaries (DST irrelevant but include UTC conversions)

---

## 📝 Technical Debt & Notes

### Current Technical Debt
- [ ] Replace in-memory deduplication with database-based idempotency
- [ ] Implement proper timezone handling (CT/UTC conversions)
- [ ] Add comprehensive test coverage
- [ ] Performance optimization for larger datasets
- [ ] Documentation updates

### Open Questions
- **Bounce handling**: Accept Gmail-only approach for now? (Lower fidelity)
- **Admin domain**: Is assignments@ under a Workspace domain we control?
- **Drive vs GCS**: Chose Drive; revisit if listing performance becomes important
- **Auth scope**: Only owner needs UI now? Any staff? Add allowlist as needed

---

## 🎯 Success Metrics

### Week 1-2
- ✅ "Teachers can create assignments, students can submit, I can see everything"

### Week 3  
- ✅ "System is secure and reliable for production use"

### Week 4
- ✅ "System automatically reminds everyone and escalates problems"

### Full System
- Fewer missed/late submissions via automated reminders
- Timely grading via teacher SLAs and reminders  
- Clear audit trail to resolve disputes
- Admin visibility: per-teacher response time, submission timing, per-term/class escalations
