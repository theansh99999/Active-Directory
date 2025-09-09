// Custom JavaScript for Active Directory Clone

// Theme toggle functionality
function toggleTheme() {
    const html = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = html.getAttribute('data-bs-theme');
    
    if (currentTheme === 'dark') {
        html.setAttribute('data-bs-theme', 'light');
        themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
        localStorage.setItem('theme', 'light');
    } else {
        html.setAttribute('data-bs-theme', 'dark');
        themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
        localStorage.setItem('theme', 'dark');
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const html = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');
    
    html.setAttribute('data-bs-theme', savedTheme);
    
    if (themeToggle) {
        if (savedTheme === 'dark') {
            themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
        }
    }
});

// Auto-refresh functionality for dashboard
function autoRefreshDashboard() {
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        // Refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    }
}

// Search functionality with debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Enhanced search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    
    searchInputs.forEach(input => {
        const debouncedSubmit = debounce(() => {
            input.form.submit();
        }, 500);
        
        input.addEventListener('input', debouncedSubmit);
    });
});

// Confirm delete functionality
function confirmDelete(itemName, deleteUrl, itemType = 'item') {
    const message = `Are you sure you want to delete ${itemType} "${itemName}"? This action cannot be undone.`;
    
    if (confirm(message)) {
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = deleteUrl;
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfToken.getAttribute('content');
            form.appendChild(csrfInput);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Status change confirmation for computers
function confirmStatusChange(computerName, action) {
    const actionMessages = {
        'ON': 'turn on',
        'OFF': 'turn off',
        'RESTART': 'restart'
    };
    
    const message = `Are you sure you want to ${actionMessages[action]} computer "${computerName}"?`;
    return confirm(message);
}

// Form validation enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        if (input.name === 'password' || input.name === 'new_password') {
            input.addEventListener('input', function() {
                validatePasswordStrength(this);
            });
        }
    });
});

function validatePasswordStrength(input) {
    const password = input.value;
    const strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) {
        // Create strength indicator if it doesn't exist
        const indicator = document.createElement('div');
        indicator.id = 'password-strength';
        indicator.className = 'form-text';
        input.parentNode.appendChild(indicator);
    }
    
    let strength = 0;
    let messages = [];
    
    if (password.length >= 8) {
        strength++;
    } else {
        messages.push('at least 8 characters');
    }
    
    if (/[A-Z]/.test(password)) {
        strength++;
    } else {
        messages.push('one uppercase letter');
    }
    
    if (/\d/.test(password)) {
        strength++;
    } else {
        messages.push('one number');
    }
    
    const indicator = document.getElementById('password-strength');
    
    if (password.length === 0) {
        indicator.textContent = '';
        indicator.className = 'form-text';
    } else if (strength === 3) {
        indicator.textContent = 'Strong password ✓';
        indicator.className = 'form-text text-success';
    } else {
        indicator.textContent = `Password needs: ${messages.join(', ')}`;
        indicator.className = 'form-text text-warning';
    }
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Tooltip initialization
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Table sorting functionality
function sortTable(columnIndex, tableId) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.dataset.sortOrder !== 'asc';
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (isAscending) {
            return aText.localeCompare(bText);
        } else {
            return bText.localeCompare(aText);
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Real-time status updates (placeholder for WebSocket implementation)
function initializeStatusUpdates() {
    // This would connect to a WebSocket for real-time updates
    // For now, we'll use periodic polling for computer status
    if (window.location.pathname === '/computers') {
        setInterval(function() {
            // Refresh computer status every 60 seconds
            const statusElements = document.querySelectorAll('.computer-status');
            // Implementation would go here for real-time updates
        }, 60000);
    }
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeStatusUpdates();
    autoRefreshDashboard();
});

// Utility functions
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    Copied to clipboard!
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 3000);
    });
}