let currentTaskId = null;
let statusCheckInterval = null;


const resizeForm = document.getElementById('resizeForm');
const imageUrlInput = document.getElementById('imageUrl');
const widthInput = document.getElementById('width');
const heightInput = document.getElementById('height');


const formSection = document.querySelector('.form-section');
const statusSection = document.getElementById('statusSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');


resizeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    hideAllSections();
    showLoading();
    
    try {
        const response = await fetch('/queue-task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_type: 'resize',
                image_url: imageUrlInput.value,
                parameters: {
                    width: parseInt(widthInput.value),
                    height: parseInt(heightInput.value)
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // Show status section
        document.getElementById('taskId').textContent = currentTaskId;
        statusSection.style.display = 'block';
        
        // Start checking status every 2 seconds
        checkStatus();
        statusCheckInterval = setInterval(checkStatus, 2000);
        
    } catch (error) {
        showError(`Failed to queue task: ${error.message}`);
    }
});


async function checkStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/task-status/${currentTaskId}`);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update status display
        document.getElementById('taskStatus').textContent = data.status || 'unknown';
        
        // If task is complete, show result
        if (data.status === 'completed' && data.result) {
            clearInterval(statusCheckInterval);
            showResult(data.result);
        }
        
        // If task failed
        if (data.status === 'failed') {
            clearInterval(statusCheckInterval);
            showError(`Task failed: ${data.error || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Status check failed:', error);
    }
}


function showResult(result) {
    statusSection.style.display = 'none';
    resultSection.style.display = 'block';
    
    if (result.image_url) {
        document.getElementById('resultImage').src = result.image_url;
    }
    
    document.getElementById('resultMessage').textContent = 
        `Image resized to ${result.width}x${result.height}px`;
}

// Show error
function showError(message) {
    hideAllSections();
    document.getElementById('errorMessage').textContent = message;
    errorSection.style.display = 'block';
}

// Show loading message
function showLoading() {
    const formSection = document.querySelector('.form-section');
    const loadingMsg = document.createElement('p');
    loadingMsg.id = 'loadingMessage';
    loadingMsg.textContent = 'Queuing task...';
    loadingMsg.style.textAlign = 'center';
    loadingMsg.style.color = '#667eea';
    loadingMsg.style.fontWeight = 'bold';
    formSection.appendChild(loadingMsg);
}

// Hide all sections
function hideAllSections() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (loadingMsg) loadingMsg.remove();
    
    statusSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}

// Reset form
function resetForm() {
    clearInterval(statusCheckInterval);
    currentTaskId = null;
    
    resizeForm.reset();
    hideAllSections();
    formSection.style.display = 'block';
}

// Initial display
formSection.style.display = 'block';
