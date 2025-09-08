// Main application JavaScript

// Open file in system (placeholder - implement based on OS)
function openFile(filePath) {
    // This would need backend support to open files
    console.log('Opening file:', filePath);
    alert('File opening not implemented. Path: ' + filePath);
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.querySelector('input[name="query"]');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }
});

// Show loading state
document.getElementById('chatForm')?.addEventListener('submit', function() {
    const button = this.querySelector('button[type="submit"]');
    button.textContent = 'Thinking...';
    button.disabled = true;
});