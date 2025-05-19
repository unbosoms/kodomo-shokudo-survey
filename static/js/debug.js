/**
 * Debug utility for troubleshooting
 */

// Override console.log, console.error, etc. to display on page
(function() {
    // Create debug container if it doesn't exist
    let debugContainer = document.getElementById('debug-container');
    if (!debugContainer) {
        debugContainer = document.createElement('div');
        debugContainer.id = 'debug-container';
        debugContainer.style.position = 'fixed';
        debugContainer.style.bottom = '0';
        debugContainer.style.left = '0';
        debugContainer.style.right = '0';
        debugContainer.style.maxHeight = '200px';
        debugContainer.style.overflowY = 'auto';
        debugContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        debugContainer.style.color = 'white';
        debugContainer.style.padding = '10px';
        debugContainer.style.fontSize = '12px';
        debugContainer.style.fontFamily = 'monospace';
        debugContainer.style.zIndex = '9999';
        
        // Add toggle button
        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Toggle Debug';
        toggleButton.style.position = 'fixed';
        toggleButton.style.top = '10px';
        toggleButton.style.right = '10px';
        toggleButton.style.zIndex = '10000';
        toggleButton.style.padding = '5px 10px';
        toggleButton.style.backgroundColor = '#007bff';
        toggleButton.style.color = 'white';
        toggleButton.style.border = 'none';
        toggleButton.style.borderRadius = '4px';
        toggleButton.style.cursor = 'pointer';
        
        toggleButton.addEventListener('click', function() {
            if (debugContainer.style.display === 'none') {
                debugContainer.style.display = 'block';
            } else {
                debugContainer.style.display = 'none';
            }
        });
        
        // Add to document
        document.body.appendChild(toggleButton);
        document.body.appendChild(debugContainer);
    }
    
    // Override console methods
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    
    console.log = function() {
        originalLog.apply(console, arguments);
        logToDebugContainer('LOG', arguments);
    };
    
    console.error = function() {
        originalError.apply(console, arguments);
        logToDebugContainer('ERROR', arguments);
    };
    
    console.warn = function() {
        originalWarn.apply(console, arguments);
        logToDebugContainer('WARN', arguments);
    };
    
    console.info = function() {
        originalInfo.apply(console, arguments);
        logToDebugContainer('INFO', arguments);
    };
    
    // Log to debug container
    function logToDebugContainer(type, args) {
        const debugContainer = document.getElementById('debug-container');
        
        // Create log entry
        const logEntry = document.createElement('div');
        logEntry.style.borderBottom = '1px solid #444';
        logEntry.style.padding = '5px 0';
        
        // Add timestamp
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        const timestampSpan = document.createElement('span');
        timestampSpan.textContent = `[${timestamp}] `;
        timestampSpan.style.color = '#aaa';
        logEntry.appendChild(timestampSpan);
        
        // Add type
        const typeSpan = document.createElement('span');
        typeSpan.textContent = `[${type}] `;
        
        switch (type) {
            case 'ERROR':
                typeSpan.style.color = '#ff5252';
                break;
            case 'WARN':
                typeSpan.style.color = '#ffab40';
                break;
            case 'INFO':
                typeSpan.style.color = '#2196f3';
                break;
            default:
                typeSpan.style.color = '#fff';
        }
        
        logEntry.appendChild(typeSpan);
        
        // Add message
        const messageSpan = document.createElement('span');
        
        // Convert arguments to string
        let message = '';
        for (let i = 0; i < args.length; i++) {
            if (typeof args[i] === 'object') {
                try {
                    message += JSON.stringify(args[i]);
                } catch (e) {
                    message += args[i];
                }
            } else {
                message += args[i];
            }
            
            if (i < args.length - 1) {
                message += ' ';
            }
        }
        
        messageSpan.textContent = message;
        logEntry.appendChild(messageSpan);
        
        // Add to debug container
        debugContainer.appendChild(logEntry);
        
        // Scroll to bottom
        debugContainer.scrollTop = debugContainer.scrollHeight;
    }
    
    // Log page load
    console.info('Debug utility loaded');
})();

// Add global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.message, 'at', event.filename, 'line', event.lineno, 'column', event.colno);
    console.error('Stack:', event.error ? event.error.stack : 'No stack available');
});

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// Add debug info about the current state
document.addEventListener('DOMContentLoaded', function() {
    // Log LIFF ID
    if (typeof liffId !== 'undefined') {
        console.info('LIFF ID:', liffId);
    } else {
        console.error('LIFF ID is not defined');
    }
    
    // Log DOM elements
    console.info('Loading element visible:', !document.getElementById('loading').classList.contains('d-none'));
    console.info('Registration form visible:', !document.getElementById('registration-form').classList.contains('d-none'));
    console.info('Main app visible:', !document.getElementById('main-app').classList.contains('d-none'));
    
    // Add debug info to showMainApp function
    const originalShowMainApp = window.showMainApp;
    window.showMainApp = function(user, shokudo) {
        console.info('showMainApp called with user:', user, 'shokudo:', shokudo);
        
        // Call original function
        if (originalShowMainApp) {
            try {
                originalShowMainApp(user, shokudo);
                console.info('showMainApp completed successfully');
            } catch (error) {
                console.error('Error in showMainApp:', error);
            }
        } else {
            console.error('originalShowMainApp is not defined');
        }
    };
});
