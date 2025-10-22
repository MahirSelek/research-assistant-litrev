/**
 * Polo GGB Research Assistant - Main JavaScript
 * Handles loading overlays and UI interactions
 */

// Full-Screen Loading Overlay Functions - Enhanced
function showLoadingOverlay(message = "Processing...", subtext = "Please wait while we work on your request", progress = "") {
    // Remove any existing overlay first
    let existingOverlay = document.getElementById('loading-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    // Create new overlay
    let overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    
    // Set overlay content
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
            <div class="loading-subtext">${subtext}</div>
            ${progress ? `<div class="loading-progress">${progress}</div>` : ''}
        </div>
    `;
    
    // Add to body
    document.body.appendChild(overlay);
    
    // Force show overlay immediately
    setTimeout(() => {
        overlay.classList.add('show');
        document.body.classList.add('loading-active');
    }, 10);
    
    // Block all interactions
    overlay.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return false;
    });
    
    overlay.addEventListener('keydown', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return false;
    });
    
    // Block scrolling
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('show');
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 300);
        
        // Restore scrolling
        document.body.classList.remove('loading-active');
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
    }
}

// Make functions globally available
window.showLoadingOverlay = showLoadingOverlay;
window.hideLoadingOverlay = hideLoadingOverlay;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Polo GGB Research Assistant UI initialized');
});
