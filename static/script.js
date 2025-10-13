// Tab switching
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
}

// Input validation helper
function validateInput(value, type, fieldName) {
    if (!value || value.trim() === '') {
        throw new Error(`${fieldName} is required`);
    }
    
    switch (type) {
        case 'text':
            if (value.length > 200) {
                throw new Error(`${fieldName} must be less than 200 characters`);
            }
            break;
        case 'assignment_code':
            if (!/^[A-Z0-9]+-[A-Z0-9]+$/.test(value)) {
                throw new Error(`${fieldName} must be in format like ENG7-0115`);
            }
            break;
        case 'student_id':
            if (!/^[A-Z0-9]+$/.test(value)) {
                throw new Error(`${fieldName} must contain only letters and numbers`);
            }
            break;
        case 'date':
            const date = new Date(value);
            if (isNaN(date.getTime())) {
                throw new Error(`${fieldName} must be a valid date`);
            }
            if (date < new Date()) {
                throw new Error(`${fieldName} must be in the future`);
            }
            break;
    }
    
    return value.trim();
}

// Assignment creation
document.getElementById('assignForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const title = validateInput(document.getElementById('assignTitle').value, 'text', 'Assignment title');
        const className = validateInput(document.getElementById('assignClass').value, 'text', 'Class name');
        const deadline = validateInput(document.getElementById('assignDeadline').value, 'date', 'Deadline');
        const instructions = document.getElementById('assignInstructions').value?.trim() || '';
        
        const emailBody = `Title: ${title}\nClass: ${className}\nDeadline: ${deadline} 23:59 CT\nInstructions: ${instructions}`;
        
        const response = await fetch('/api/process-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: 'ASSIGN',
                body: emailBody,
                from_email: 'teacher@example.com',
                to_email: 'assignments@example.com',
                message_id: `assign_${Date.now()}@example.com`
            })
        });
        
        const result = await response.json();
        showResult('assignResult', result.success ? result.response : result.detail, result.success ? 'success' : 'error');
        
        if (result.success) {
            document.getElementById('assignForm').reset();
            loadAllAssignments(); // Refresh assignments list
        }
    } catch (error) {
        showResult('assignResult', `Error: ${error.message}`, 'error');
    }
});

// Submission
document.getElementById('submitForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const code = validateInput(document.getElementById('submitCode').value.toUpperCase(), 'assignment_code', 'Assignment code');
        const studentId = validateInput(document.getElementById('submitStudentId').value.toUpperCase(), 'student_id', 'Student ID');
        
        const emailBody = `StudentID: ${studentId}`;
        
        const response = await fetch('/api/process-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: `SUBMIT ${code}`,
                body: emailBody,
                from_email: 'student@example.com',
                to_email: 'assignments@example.com',
                message_id: `submit_${Date.now()}@example.com`
            })
        });
        
        const result = await response.json();
        showResult('submitResult', result.success ? result.response : result.detail, result.success ? 'success' : 'error');
        
        if (result.success) {
            document.getElementById('submitForm').reset();
        }
    } catch (error) {
        showResult('submitResult', `Error: ${error.message}`, 'error');
    }
});

// Return grade
document.getElementById('returnForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const code = validateInput(document.getElementById('returnCode').value.toUpperCase(), 'assignment_code', 'Assignment code');
        const studentId = validateInput(document.getElementById('returnStudentId').value.toUpperCase(), 'student_id', 'Student ID');
        const grade = validateInput(document.getElementById('returnGrade').value, 'text', 'Grade');
        const feedback = document.getElementById('returnFeedback').value?.trim() || '';
        
        const emailBody = `Grade: ${grade}\nFeedback: ${feedback}`;
        
        const response = await fetch('/api/process-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: `RETURN ${code} ${studentId}`,
                body: emailBody,
                from_email: 'teacher@example.com',
                to_email: 'assignments@example.com',
                message_id: `return_${Date.now()}@example.com`
            })
        });
        
        const result = await response.json();
        showResult('returnResult', result.success ? result.response : result.detail, result.success ? 'success' : 'error');
        
        if (result.success) {
            document.getElementById('returnForm').reset();
        }
    } catch (error) {
        showResult('returnResult', `Error: ${error.message}`, 'error');
    }
});

// Load assignment status
async function loadStatus() {
    try {
        const code = validateInput(document.getElementById('statusCode').value.toUpperCase(), 'assignment_code', 'Assignment code');
        
        const response = await fetch(`/api/assignments/${code}/status`);
        const result = await response.json();
        
        if (response.ok) {
            displayStatus(result);
        } else {
            showResult('statusResult', result.detail, 'error');
        }
    } catch (error) {
        showResult('statusResult', `Error: ${error.message}`, 'error');
    }
}

// Display assignment status
function displayStatus(data) {
    const assignment = data.assignment;
    const submissions = data.submissions;
    
    const container = document.createElement('div');
    container.className = 'assignment-item';
    
    const codeDiv = document.createElement('div');
    codeDiv.className = 'assignment-code';
    codeDiv.textContent = assignment.code;
    
    const titleH3 = document.createElement('h3');
    titleH3.textContent = assignment.title;
    
    const classP = document.createElement('p');
    classP.innerHTML = '<strong>Class:</strong> ';
    classP.appendChild(document.createTextNode(assignment.class_name));
    
    const dueP = document.createElement('p');
    dueP.innerHTML = '<strong>Due:</strong> ';
    dueP.appendChild(document.createTextNode(`${new Date(assignment.deadline_at).toLocaleString()} ${assignment.deadline_tz}`));
    
    const statusP = document.createElement('p');
    statusP.innerHTML = '<strong>Status:</strong> ';
    statusP.appendChild(document.createTextNode(assignment.status));
    
    container.appendChild(codeDiv);
    container.appendChild(titleH3);
    container.appendChild(classP);
    container.appendChild(dueP);
    container.appendChild(statusP);
    
    if (assignment.instructions) {
        const instrP = document.createElement('p');
        instrP.innerHTML = '<strong>Instructions:</strong> ';
        instrP.appendChild(document.createTextNode(assignment.instructions));
        container.appendChild(instrP);
    }
    
    if (submissions.length > 0) {
        const subH4 = document.createElement('h4');
        subH4.textContent = 'Submissions:';
        container.appendChild(subH4);
        
        submissions.forEach(sub => {
            const subDiv = document.createElement('div');
            subDiv.className = 'submission-item';
            
            const strong = document.createElement('strong');
            strong.textContent = `Student ${sub.student_id}`;
            
            const statusSpan = document.createElement('span');
            statusSpan.className = sub.on_time ? 'on-time' : 'late';
            statusSpan.textContent = sub.on_time ? 'On Time' : 'Late';
            
            const small = document.createElement('small');
            small.textContent = `Received: ${new Date(sub.received_at).toLocaleString()}`;
            
            subDiv.appendChild(strong);
            subDiv.appendChild(document.createTextNode(' - '));
            subDiv.appendChild(statusSpan);
            subDiv.appendChild(document.createElement('br'));
            subDiv.appendChild(small);
            
            container.appendChild(subDiv);
        });
    } else {
        const noSub = document.createElement('p');
        const em = document.createElement('em');
        em.textContent = 'No submissions yet.';
        noSub.appendChild(em);
        container.appendChild(noSub);
    }
    
    const resultDiv = document.getElementById('statusResult');
    resultDiv.innerHTML = '';
    resultDiv.appendChild(container);
    resultDiv.className = 'result info';
}

// Load all assignments
async function loadAllAssignments() {
    try {
        const response = await fetch('/api/assignments');
        const assignments = await response.json();
        
        if (assignments.length === 0) {
            showResult('allAssignments', 'No assignments found.', 'info');
            return;
        }
        
        const container = document.createDocumentFragment();
        assignments.forEach(assignment => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'assignment-item';
            
            const codeDiv = document.createElement('div');
            codeDiv.className = 'assignment-code';
            codeDiv.textContent = assignment.code;
            
            const titleH4 = document.createElement('h4');
            titleH4.textContent = assignment.title;
            
            const classP = document.createElement('p');
            classP.innerHTML = '<strong>Class:</strong> ';
            classP.appendChild(document.createTextNode(assignment.class_name));
            
            const dueP = document.createElement('p');
            dueP.innerHTML = '<strong>Due:</strong> ';
            dueP.appendChild(document.createTextNode(`${new Date(assignment.deadline_at).toLocaleString()} ${assignment.deadline_tz}`));
            
            const statusP = document.createElement('p');
            statusP.innerHTML = '<strong>Status:</strong> ';
            statusP.appendChild(document.createTextNode(assignment.status));
            
            itemDiv.appendChild(codeDiv);
            itemDiv.appendChild(titleH4);
            itemDiv.appendChild(classP);
            itemDiv.appendChild(dueP);
            itemDiv.appendChild(statusP);
            
            container.appendChild(itemDiv);
        });
        
        const resultDiv = document.getElementById('allAssignments');
        resultDiv.innerHTML = '';
        resultDiv.appendChild(container);
        resultDiv.className = 'result info';
    } catch (error) {
        showResult('allAssignments', `Error: ${error.message}`, 'error');
    }
}

// Show result message
function showResult(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `result ${type}`;
}

// Load assignments on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAllAssignments();
});
