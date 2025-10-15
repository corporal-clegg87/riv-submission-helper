# User Acceptance Testing (UAT) Procedures
## RIV Assignment Management System

### Overview
This document provides comprehensive testing procedures for the RIV Assignment Management System deployed on Google Cloud Platform. All tests should be performed in the production environment after deployment.

---

## Prerequisites for UAT

### 1. Environment Setup
- [ ] GCP deployment completed successfully
- [ ] Database migrations applied
- [ ] Seed data loaded
- [ ] Service URL obtained
- [ ] Test email accounts configured

### 2. Test Data Requirements
- [ ] Valid teacher emails (whitelisted)
- [ ] Valid student IDs
- [ ] Valid class names
- [ ] Sample assignment attachments (JPEG/PDF)

### 3. Test Tools
- [ ] Web browser (Chrome/Firefox)
- [ ] Email client (Gmail/Outlook)
- [ ] API testing tool (Postman/curl)
- [ ] Cloud Console access

---

## Test Scenarios

### Scenario 1: Teacher Creates Assignment (ASSIGN Command)

#### Test Steps:
1. **Send ASSIGN Email**
   ```
   To: assignments@rivendell-academy.co.uk
   From: john.smith@rivendell-academy.co.uk (whitelisted teacher)
   Subject: ASSIGN
   
   Body:
   Title: English Essay - Character Analysis
   Class: English 7A
   Deadline: 2024-02-15 23:59 CT
   Instructions: Write a 500-word essay analyzing the main character in the assigned reading.
   ```

2. **Verify Response**
   - [ ] System sends confirmation email to teacher
   - [ ] Assignment appears in admin interface
   - [ ] Assignment code is generated (format: ENG7-0215)
   - [ ] Announcement email sent to all enrolled students/parents

3. **Check Admin Interface**
   - [ ] Navigate to: `https://riv-assignments-iuhqct2csq-uc.a.run.app/`
   - [ ] Login (if authentication enabled)
   - [ ] Verify assignment appears in list
   - [ ] Check assignment details are correct

#### Expected Results:
- Assignment created with status "SCHEDULED"
- Assignment code follows format: [CLASS_PREFIX]-[MMDD]
- Announcement emails sent to enrolled students
- Admin can view assignment details

---

### Scenario 2: Student Submits Assignment (SUBMIT Command)

#### Test Steps:
1. **Send SUBMIT Email**
   ```
   To: assignments@rivendell-academy.co.uk
   From: brown.family@example.com (parent email)
   Subject: SUBMIT ENG7-0215
   
   Body:
   StudentID: S001
   
   Attachments: [Sample essay document in PDF format]
   ```

2. **Verify Response**
   - [ ] System sends confirmation email to parent
   - [ ] Submission forwarded to teacher
   - [ ] Submission recorded as "on time" (if before deadline)

3. **Check Admin Interface**
   - [ ] Navigate to assignment status page
   - [ ] Verify submission appears in list
   - [ ] Check submission timestamp and status

#### Expected Results:
- Submission recorded with status "RECEIVED"
- On-time status calculated correctly
- Teacher receives forwarded submission
- Parent receives confirmation

---

### Scenario 3: Teacher Grades Assignment (GRADE Command)

#### Test Steps:
1. **Send GRADE Email**
   ```
   To: assignments@rivendell-academy.co.uk
   From: john.smith@rivendell-academy.co.uk (teacher)
   Subject: GRADE ENG7-0215 S001
   
   Body:
   Grade: A-
   Feedback: Excellent analysis of character development. Well-structured essay with clear examples from the text.
   ```

2. **Verify Response**
   - [ ] System sends grade notification to parent and student
   - [ ] Grade recorded in system
   - [ ] Feedback included in notification

3. **Check Admin Interface**
   - [ ] Navigate to assignment status page
   - [ ] Verify grade appears in submission details
   - [ ] Check feedback is displayed

#### Expected Results:
- Grade recorded with timestamp
- Feedback included in grade record
- Notification sent to parent and student
- Admin can view graded submission

---

### Scenario 4: API Endpoint Testing

#### Test Steps:
1. **Test Process Email Endpoint**
   ```bash
   curl -X POST "https://riv-assignments-iuhqct2csq-uc.a.run.app/api/process-email" \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "ASSIGN",
       "body": "Title: Test Assignment\nClass: English 7A\nDeadline: 2024-02-20 23:59 CT",
       "from_email": "john.smith@rivendell-academy.co.uk",
       "to_email": "assignments@rivendell-academy.co.uk",
       "message_id": "test-001@example.com"
     }'
   ```

2. **Test List Assignments Endpoint**
   ```bash
   curl -X GET "https://riv-assignments-iuhqct2csq-uc.a.run.app/api/assignments"
   ```

3. **Test Assignment Status Endpoint**
   ```bash
   curl -X GET "https://riv-assignments-iuhqct2csq-uc.a.run.app/api/assignments/ENG7-0215/status"
   ```

4. **Test Health Check Endpoint**
   ```bash
   curl -X GET "https://riv-assignments-iuhqct2csq-uc.a.run.app/health"
   ```

#### Expected Results:
- All API endpoints return appropriate HTTP status codes
- JSON responses are properly formatted
- Error handling works correctly for invalid requests

---

### Scenario 5: Error Handling and Validation

#### Test Steps:
1. **Invalid Teacher Email**
   ```
   To: assignments@rivendell-academy.co.uk
   From: unauthorized@example.com (not whitelisted)
   Subject: ASSIGN
   
   Body: [Valid assignment content]
   ```
   - [ ] System rejects email with appropriate error message
   - [ ] Admin receives notification of unauthorized attempt

2. **Invalid Assignment Format**
   ```
   To: assignments@rivendell-academy.co.uk
   From: john.smith@rivendell-academy.co.uk
   Subject: ASSIGN
   
   Body: Invalid format - missing required fields
   ```
   - [ ] System responds with validation error
   - [ ] Clear error message sent to sender

3. **Duplicate Submission**
   ```
   To: assignments@rivendell-academy.co.uk
   From: brown.family@example.com
   Subject: SUBMIT ENG7-0215
   
   Body: StudentID: S001
   ```
   - [ ] System detects duplicate submission
   - [ ] Appropriate message sent explaining first submission counts

4. **Invalid Student ID**
   ```
   To: assignments@rivendell-academy.co.uk
   From: brown.family@example.com
   Subject: SUBMIT ENG7-0215
   
   Body: StudentID: INVALID123
   ```
   - [ ] System validates student ID exists
   - [ ] Error message sent if student not found

#### Expected Results:
- All validation rules enforced correctly
- Clear, helpful error messages
- No system crashes or data corruption
- Proper logging of all errors

---

### Scenario 6: Gmail Integration and Pub/Sub

#### Test Steps:
1. **Verify Gmail Watch Setup**
   - [ ] Gmail watch configured on assignments@rivendell-academy.co.uk
   - [ ] Pub/Sub topic receives notifications
   - [ ] Subscription processes messages correctly

2. **Test Email Processing Flow**
   - [ ] Send test email to assignments@rivendell-academy.co.uk
   - [ ] Verify Pub/Sub notification received
   - [ ] Check email processed within 5 minutes
   - [ ] Verify response email sent

3. **Check Logging**
   - [ ] Review Cloud Run logs for email processing
   - [ ] Verify Pub/Sub message acknowledgments
   - [ ] Check for any error messages

#### Expected Results:
- Gmail integration working correctly
- Pub/Sub messages processed successfully
- Email processing happens automatically
- Comprehensive logging available

---

### Scenario 7: Database Operations

#### Test Steps:
1. **Verify Database Connection**
   - [ ] Health check endpoint returns "healthy"
   - [ ] Database queries execute successfully
   - [ ] No connection timeouts

2. **Test Data Integrity**
   - [ ] All created records have proper relationships
   - [ ] Foreign key constraints enforced
   - [ ] Data validation rules working

3. **Check Performance**
   - [ ] API responses under 2 seconds
   - [ ] Database queries optimized
   - [ ] No memory leaks detected

#### Expected Results:
- Database operations stable and fast
- Data integrity maintained
- Performance meets requirements
- No data corruption

---

### Scenario 8: Security and Access Control

#### Test Steps:
1. **Test CORS Configuration**
   - [ ] Web interface loads correctly
   - [ ] API calls work from browser
   - [ ] No CORS errors in console

2. **Test Input Validation**
   - [ ] SQL injection attempts blocked
   - [ ] XSS attempts sanitized
   - [ ] File upload restrictions enforced

3. **Test Rate Limiting**
   - [ ] Rapid API calls handled gracefully
   - [ ] No system overload
   - [ ] Appropriate error responses

#### Expected Results:
- Security measures working correctly
- No unauthorized access possible
- System resilient to attacks
- Proper error handling

---

## Performance Testing

### Load Testing Scenarios

1. **Concurrent Email Processing**
   - Send 10 emails simultaneously
   - Verify all processed correctly
   - Check response times under load

2. **Database Load**
   - Create 100 assignments
   - Process 500 submissions
   - Verify system performance maintained

3. **API Load Testing**
   - 100 concurrent API requests
   - Verify response times under 2 seconds
   - Check for any failures

---

## Monitoring and Alerting Verification

### Test Steps:
1. **Check Cloud Monitoring**
   - [ ] Metrics visible in Cloud Console
   - [ ] Custom metrics configured
   - [ ] Dashboards working correctly

2. **Test Alerting**
   - [ ] Error rate alerts configured
   - [ ] Performance alerts set up
   - [ ] Notification channels working

3. **Verify Logging**
   - [ ] Structured logs in Cloud Logging
   - [ ] Log levels appropriate
   - [ ] Log retention configured

---

## UAT Sign-off Checklist

### Functional Requirements
- [ ] All email commands work correctly (ASSIGN, SUBMIT, GRADE)
- [ ] Admin interface displays data accurately
- [ ] API endpoints function as expected
- [ ] Error handling works properly
- [ ] Gmail integration processes emails automatically

### Non-Functional Requirements
- [ ] System performance meets requirements (<2s response time)
- [ ] Security measures implemented correctly
- [ ] Monitoring and alerting configured
- [ ] Database operations stable
- [ ] Logging comprehensive and accessible

### Business Requirements
- [ ] Complete assignment lifecycle works end-to-end
- [ ] Teacher workflow efficient and intuitive
- [ ] Student/parent experience smooth
- [ ] Admin visibility into all operations
- [ ] System handles edge cases gracefully

---

## Post-UAT Actions

### If Tests Pass:
1. [ ] Document any issues found and resolved
2. [ ] Update system documentation
3. [ ] Train end users on system usage
4. [ ] Schedule go-live date
5. [ ] Set up production monitoring

### If Tests Fail:
1. [ ] Document all failures with details
2. [ ] Prioritize issues by severity
3. [ ] Fix critical issues immediately
4. [ ] Re-run failed test scenarios
5. [ ] Update deployment procedures if needed

---

## Contact Information

**System Administrator**: [Your Name]
**Email**: [Your Email]
**Emergency Contact**: [Emergency Phone]

**GCP Project**: riv-grading-helper
**Service URL**: https://riv-assignments-iuhqct2csq-uc.a.run.app/
**Cloud Console**: https://console.cloud.google.com/

---

*This UAT procedure should be completed before system go-live. All test scenarios must pass for production deployment approval.*
