document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const statusContainer = document.getElementById('statusContainer');
    const status = document.getElementById('status');

    feather.replace();  // Initialize Feather icons

    startButton.addEventListener('click', () => handleReservation('start', startButton, stopButton));
    stopButton.addEventListener('click', () => handleReservation('stop', stopButton, startButton));

    // Check initial status
    checkStatus();

    // Set up periodic status check
    setInterval(checkStatus, 5000);  // Check every 5 seconds
});

function handleReservation(action, activeButton, inactiveButton) {
    activeButton.disabled = true;
    inactiveButton.disabled = true;
    activeButton.classList.add('opacity-50', 'cursor-not-allowed');
    inactiveButton.classList.add('opacity-50', 'cursor-not-allowed');

    // Animate button
    activeButton.classList.add('animate-pulse');

    fetch(`/${action}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateStatus(data.status);
            checkStatus();  // Update buttons state
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus(`Une erreur est survenue: ${error.message}`);
        })
        .finally(() => {
            activeButton.disabled = false;
            inactiveButton.disabled = false;
            activeButton.classList.remove('opacity-50', 'cursor-not-allowed', 'animate-pulse');
            inactiveButton.classList.remove('opacity-50', 'cursor-not-allowed');
        });
}

function updateStatus(message) {
    const statusContainer = document.getElementById('statusContainer');
    const status = document.getElementById('status');
    
    statusContainer.classList.remove('hidden');
    status.textContent = `Statut: ${message}`;
    
    // Animate status update
    statusContainer.classList.add('animate-bounce');
    setTimeout(() => statusContainer.classList.remove('animate-bounce'), 1000);
}

function checkStatus() {
    fetch('/status', { method: 'GET' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateStatus(data.status);
            updateButtons(data.isRunning);
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus(`Erreur lors de la vérification du statut: ${error.message}`);
        });
}

function updateButtons(isRunning) {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');

    if (isRunning) {
        startButton.disabled = true;
        startButton.classList.add('opacity-50', 'cursor-not-allowed');
        stopButton.disabled = false;
        stopButton.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
        startButton.disabled = false;
        startButton.classList.remove('opacity-50', 'cursor-not-allowed');
        stopButton.disabled = true;
        stopButton.classList.add('opacity-50', 'cursor-not-allowed');
    }
}