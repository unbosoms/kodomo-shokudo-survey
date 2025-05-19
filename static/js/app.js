/**
 * Main application functionality
 */

// Initialize app when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // LIFF initialization is handled in liff.js
    console.info('app.js: DOM content loaded');
});

/**
 * Main application initialization
 * This function is called from liff.js after user authentication
 */
function showMainApp(user, shokudo) {
    console.info('app.js: showMainApp called with user:', user, 'shokudo:', shokudo);
    
    try {
        // Show main app container if it's hidden
        const mainAppElement = document.getElementById('main-app');
        if (mainAppElement.classList.contains('d-none')) {
            console.info('app.js: Showing main app container');
            mainAppElement.classList.remove('d-none');
        }
        
        // Set shokudo name
        const shokudoNameElement = document.getElementById('shokudo-name');
        if (shokudoNameElement) {
            shokudoNameElement.textContent = shokudo.shokudo_name || '';
            // Store shokudo ID in data attribute
            shokudoNameElement.dataset.shokudoId = shokudo.shokudo_id || '';
            console.info('app.js: Set shokudo name to:', shokudo.shokudo_name);
        }
        
        // Set up camera button
        const startCameraButton = document.getElementById('start-camera');
        if (startCameraButton) {
            // Remove any existing event listeners
            const newButton = startCameraButton.cloneNode(true);
            startCameraButton.parentNode.replaceChild(newButton, startCameraButton);
            
            // Add event listener
            newButton.addEventListener('click', function() {
                console.info('app.js: Start camera button clicked');
                // Hide this button
                this.classList.add('d-none');
                
                // Initialize camera
                if (typeof initCamera === 'function') {
                    initCamera();
                } else {
                    showError('カメラ機能が利用できません');
                    console.error('app.js: initCamera function not found');
                }
            });
        }
        
        console.info('app.js: showMainApp completed successfully');
    } catch (error) {
        console.error('app.js: Error in showMainApp:', error);
        showError('アプリの初期化中にエラーが発生しました: ' + error.message);
    }
}

/**
 * Format counts for display
 */
function formatCounts(counts) {
    // Get quadrant names
    const quadrantNames = {
        'UL': '左上',
        'UR': '右上',
        'LL': '左下',
        'LR': '右下'
    };
    
    // Get color names
    const colorNames = {
        'red': '赤',
        'green': '緑',
        'blue': '青',
        'yellow': '黄'
    };
    
    // Format counts
    let result = '';
    
    for (const quadrant in counts) {
        const quadrantName = quadrantNames[quadrant] || quadrant;
        
        result += `【${quadrantName}】\n`;
        
        for (const color in counts[quadrant]) {
            const count = counts[quadrant][color];
            
            if (count > 0) {
                const colorName = colorNames[color] || color;
                result += `・${colorName}: ${count}個\n`;
            }
        }
        
        result += '\n';
    }
    
    return result;
}

/**
 * Calculate total counts
 */
function calculateTotalCounts(counts) {
    const totals = {
        byQuadrant: {},
        byColor: {
            'red': 0,
            'green': 0,
            'blue': 0,
            'yellow': 0
        },
        total: 0
    };
    
    // Calculate totals
    for (const quadrant in counts) {
        totals.byQuadrant[quadrant] = 0;
        
        for (const color in counts[quadrant]) {
            const count = counts[quadrant][color];
            
            totals.byQuadrant[quadrant] += count;
            totals.byColor[color] += count;
            totals.total += count;
        }
    }
    
    return totals;
}

/**
 * Create chart for counts
 */
function createCountsChart(counts, elementId) {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Get canvas element
    const canvas = document.getElementById(elementId);
    if (!canvas) {
        console.error(`Canvas element with ID ${elementId} not found`);
        return;
    }
    
    // Calculate totals
    const totals = calculateTotalCounts(counts);
    
    // Create datasets
    const datasets = [];
    
    // Add dataset for each color
    const colors = {
        'red': 'rgba(255, 99, 132, 0.8)',
        'green': 'rgba(75, 192, 192, 0.8)',
        'blue': 'rgba(54, 162, 235, 0.8)',
        'yellow': 'rgba(255, 206, 86, 0.8)'
    };
    
    for (const color in colors) {
        const data = [];
        
        for (const quadrant in counts) {
            data.push(counts[quadrant][color] || 0);
        }
        
        datasets.push({
            label: colorNames[color] || color,
            backgroundColor: colors[color],
            data: data
        });
    }
    
    // Create chart
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: Object.keys(counts).map(q => quadrantNames[q] || q),
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    precision: 0
                }
            }
        }
    });
}
