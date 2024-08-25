document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const statusContainer = document.getElementById('statusContainer');
    const status = document.getElementById('status');

    feather.replace();  // Initialize Feather icons

    startButton.addEventListener('click', () => handleReservation('start', startButton, stopButton));
    stopButton.addEventListener('click', () => handleReservation('stop', stopButton, startButton));
});

function handleReservation(action, activeButton, inactiveButton) {
    activeButton.disabled = true;
    inactiveButton.disabled = true;
    activeButton.classList.add('opacity-50', 'cursor-not-allowed');
    inactiveButton.classList.add('opacity-50', 'cursor-not-allowed');

    // Animate button
    activeButton.classList.add('animate-pulse');

    fetch(`/${action}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            updateStatus(data.status);
            activeButton.disabled = false;
            activeButton.classList.remove('opacity-50', 'cursor-not-allowed', 'animate-pulse');
            
            if (action === 'start') {
                inactiveButton.disabled = false;
                inactiveButton.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus('Une erreur est survenue');
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