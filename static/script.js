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

// Assignment creation
document.getElementById('assignForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('assignTitle').value;
    const className = document.getElementById('assignClass').value;
    const deadline = document.getElementById('assignDeadline').value;
    const instructions = document.getElementById('assignInstructions').value;
    
    const emailBody = `Title: ${title}\nClass: ${className}\nDeadline: ${deadline} 23:59 CT\nInstructions: ${instructions}`;
    
    try {
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
    
    const code = document.getElementById('submitCode').value;
    const studentId = document.getElementById('submitStudentId').value;
    
    const emailBody = `StudentID: ${studentId}`;
    
    try {
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
    
    const code = document.getElementById('returnCode').value;
    const studentId = document.getElementById('returnStudentId').value;
    const grade = document.getElementById('returnGrade').value;
    const feedback = document.getElementById('returnFeedback').value;
    
    const emailBody = `Grade: ${grade}\nFeedback: ${feedback}`;
    
    try {
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
    const code = document.getElementById('statusCode').value;
    if (!code) {
        showResult('statusResult', 'Please enter an assignment code', 'error');
        return;
    }
    
    try {
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
    
    let html = `
        <div class="assignment-item">
            <div class="assignment-code">${assignment.code}</div>
            <h3>${assignment.title}</h3>
            <p><strong>Class:</strong> ${assignment.class_name}</p>
            <p><strong>Due:</strong> ${new Date(assignment.deadline_at).toLocaleString()} ${assignment.deadline_tz}</p>
            <p><strong>Status:</strong> ${assignment.status}</p>
            ${assignment.instructions ? `<p><strong>Instructions:</strong> ${assignment.instructions}</p>` : ''}
        </div>
    `;
    
    if (submissions.length > 0) {
        html += '<h4>Submissions:</h4>';
        submissions.forEach(sub => {
            const statusClass = sub.on_time ? 'on-time' : 'late';
            const statusText = sub.on_time ? 'On Time' : 'Late';
            html += `
                <div class="submission-item">
                    <strong>Student ${sub.student_id}</strong> - <span class="${statusClass}">${statusText}</span><br>
                    <small>Received: ${new Date(sub.received_at).toLocaleString()}</small>
                </div>
            `;
        });
    } else {
        html += '<p><em>No submissions yet.</em></p>';
    }
    
    showResult('statusResult', html, 'info');
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
        
        let html = '';
        assignments.forEach(assignment => {
            html += `
                <div class="assignment-item">
                    <div class="assignment-code">${assignment.code}</div>
                    <h4>${assignment.title}</h4>
                    <p><strong>Class:</strong> ${assignment.class_name}</p>
                    <p><strong>Due:</strong> ${new Date(assignment.deadline_at).toLocaleString()} ${assignment.deadline_tz}</p>
                    <p><strong>Status:</strong> ${assignment.status}</p>
                </div>
            `;
        });
        
        showResult('allAssignments', html, 'info');
    } catch (error) {
        showResult('allAssignments', `Error: ${error.message}`, 'error');
    }
}

// Show result message
function showResult(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = message;
    element.className = `result ${type}`;
}

// Load assignments on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAllAssignments();
});
