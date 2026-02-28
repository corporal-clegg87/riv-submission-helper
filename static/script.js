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

// Monitoring functionality
let monitoringInterval = null;
let requestRateChart = null;
let responseTimeChart = null;
let errorRateChart = null;

// Load monitoring data
async function loadMonitoringData() {
    try {
        const response = await fetch('/api/monitoring/metrics');
        const data = await response.json();
        
        if (response.ok) {
            displayMetrics(data);
            updateCharts(data);
            updateLastUpdateTime();
        } else {
            showMonitoringError('Failed to load monitoring data');
        }
    } catch (error) {
        console.error('Error loading monitoring data:', error);
        showMonitoringError('Error loading monitoring data');
    }
}

// Display metrics in the UI
function displayMetrics(data) {
    // Cloud Run metrics
    const cloudRun = data.cloud_run || {};
    document.getElementById('requestCount').textContent = cloudRun.request_count || 'N/A';
    document.getElementById('avgLatency').textContent = cloudRun.avg_latency_ms ? `${cloudRun.avg_latency_ms.toFixed(2)}ms` : 'N/A';
    document.getElementById('errorRate').textContent = cloudRun.error_rate ? `${cloudRun.error_rate.toFixed(2)}%` : 'N/A';
    document.getElementById('activeInstances').textContent = cloudRun.active_instances || 'N/A';
    
    // Cloud SQL metrics
    const cloudSql = data.cloud_sql || {};
    document.getElementById('activeConnections').textContent = cloudSql.active_connections || 'N/A';
    document.getElementById('cpuUtilization').textContent = cloudSql.cpu_utilization ? `${(cloudSql.cpu_utilization * 100).toFixed(1)}%` : 'N/A';
    
    // Application metrics
    const application = data.application || {};
    document.getElementById('uptime').textContent = application.uptime_seconds ? formatUptime(application.uptime_seconds) : 'N/A';
    document.getElementById('environment').textContent = application.environment || 'N/A';
    document.getElementById('status').textContent = data.status || 'N/A';
}

// Update charts with new data
function updateCharts(data) {
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();
    
    // Initialize charts if they don't exist
    if (!requestRateChart) {
        initializeCharts();
    }
    
    // Update chart data
    if (requestRateChart) {
        requestRateChart.data.labels.push(timeLabel);
        requestRateChart.data.datasets[0].data.push(data.cloud_run?.request_count || 0);
        if (requestRateChart.data.labels.length > 20) {
            requestRateChart.data.labels.shift();
            requestRateChart.data.datasets[0].data.shift();
        }
        requestRateChart.update('none');
    }
    
    if (responseTimeChart) {
        responseTimeChart.data.labels.push(timeLabel);
        responseTimeChart.data.datasets[0].data.push(data.cloud_run?.avg_latency_ms || 0);
        if (responseTimeChart.data.labels.length > 20) {
            responseTimeChart.data.labels.shift();
            responseTimeChart.data.datasets[0].data.shift();
        }
        responseTimeChart.update('none');
    }
    
    if (errorRateChart) {
        errorRateChart.data.labels.push(timeLabel);
        errorRateChart.data.datasets[0].data.push(data.cloud_run?.error_rate || 0);
        if (errorRateChart.data.labels.length > 20) {
            errorRateChart.data.labels.shift();
            errorRateChart.data.datasets[0].data.shift();
        }
        errorRateChart.update('none');
    }
}

// Initialize Chart.js charts
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    };
    
    // Request Rate Chart
    const requestRateCtx = document.getElementById('requestRateChart').getContext('2d');
    requestRateChart = new Chart(requestRateCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Requests',
                data: [],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Requests per minute'
                    }
                }
            }
        }
    });
    
    // Response Time Chart
    const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
    responseTimeChart = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Response Time',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Milliseconds'
                    }
                }
            }
        }
    });
    
    // Error Rate Chart
    const errorRateCtx = document.getElementById('errorRateChart').getContext('2d');
    errorRateChart = new Chart(errorRateCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Error Rate',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Percentage'
                    }
                }
            }
        }
    });
}

// Start auto-refresh for monitoring
function startMonitoringRefresh() {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
    
    // Load data immediately
    loadMonitoringData();
    
    // Set up auto-refresh every 5 seconds
    monitoringInterval = setInterval(loadMonitoringData, 5000);
}

// Stop auto-refresh
function stopMonitoringRefresh() {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
}

// Show monitoring error
function showMonitoringError(message) {
    document.getElementById('requestCount').textContent = 'Error';
    document.getElementById('avgLatency').textContent = 'Error';
    document.getElementById('errorRate').textContent = 'Error';
    document.getElementById('activeInstances').textContent = 'Error';
    document.getElementById('activeConnections').textContent = 'Error';
    document.getElementById('cpuUtilization').textContent = 'Error';
    document.getElementById('uptime').textContent = 'Error';
    document.getElementById('environment').textContent = 'Error';
    document.getElementById('status').textContent = 'Error';
    
    console.error('Monitoring error:', message);
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

// Format uptime in human readable format
function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Enhanced tab switching to handle monitoring
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
    
    // Handle monitoring tab specific logic
    if (tabName === 'monitoringTab') {
        startMonitoringRefresh();
    } else {
        stopMonitoringRefresh();
    }
}

// Load assignments on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAllAssignments();
});
