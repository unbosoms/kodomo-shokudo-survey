/**
 * Main application functionality
 */

// Initialize app when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // LIFF initialization is handled in liff.js
    console.info('app.js: DOM content loaded');
});

// グローバル変数を追加
let currentUser = null;
let currentShokudo = null;

/**
 * Main application initialization
 * This function is called from liff.js after user authentication
 */
function showMainApp(user, shokudo) {
    currentUser = user;
    currentShokudo = shokudo;

    console.info('app.js: showMainApp called with user:', user, 'shokudo:', shokudo);
    
    // 読み込み中の表示を非表示に
    const loading = document.getElementById('loading');
    if (loading) loading.classList.add('d-none');
    
    // メインアプリを表示
    const mainApp = document.getElementById('main-app');
    if (mainApp) {
        console.info('app.js: Showing main app container');
        mainApp.classList.remove('d-none');
        
        // カメラ起動ボタンのイベントリスナーを設定
        const startCameraButton = document.getElementById('start-camera');
        if (startCameraButton) {
            console.info('app.js: Setting up camera button listener');
            startCameraButton.addEventListener('click', () => {
                console.info('app.js: Camera button clicked');
                initCamera();
            });
        }

        // 子ども食堂名を設定
        const shokudoName = document.getElementById('shokudo-name');
        if (shokudoName) {
            shokudoName.textContent = shokudo.shokudo_name;
            console.info('app.js: Set shokudo name to:', shokudo.shokudo_name);
        }

        // 設定を読み込む
        loadSettings(shokudo.shokudo_id);
    }

    console.info('app.js: showMainApp completed successfully');
}

// APIエンドポイントの指定を修正
const API_BASE_URL = window.location.origin;

function loadSettings(shokudoId) {
    console.info('app.js: Loading settings for shokudo:', shokudoId);
    
    // URLの構築方法を修正
    const protocol = window.location.protocol;
    const host = window.location.host;
    const apiUrl = `${protocol}//${host}/api/get-settings?shokudoId=${shokudoId}`;
    
    console.info('app.js: Fetching from:', apiUrl);

    fetch(apiUrl)
        .then(response => {
            console.info('app.js: Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.info('app.js: Received data:', data);
            if (data.success) {
                console.info('app.js: Settings loaded:', data);
                
                // 色の設定を適用
                if (data.color) {
                    setColorTexts(data.color);
                }
                
                // 質問の設定を適用
                if (data.quadrant) {
                    setQuadrantTexts(data.quadrant);
                }
            } else {
                console.error('app.js: Failed to load settings:', data.error);
            }
        })
        .catch(error => {
            console.error('app.js: Failed to load settings:', error);
            throw error;
        });
}

function setColorTexts(colorSettings) {
    console.info('app.js: Setting color texts:', colorSettings);
    
    const elements = {
        red: document.getElementById('color-red-text'),
        green: document.getElementById('color-green-text'),
        blue: document.getElementById('color-blue-text'),
        yellow: document.getElementById('color-yellow-text')
    };

    if (elements.red) elements.red.textContent = colorSettings.color_red || '';
    if (elements.green) elements.green.textContent = colorSettings.color_green || '';
    if (elements.blue) elements.blue.textContent = colorSettings.color_blue || '';
    if (elements.yellow) elements.yellow.textContent = colorSettings.color_yellow || '';
}

function setQuadrantTexts(quadrantSettings) {
    console.info('app.js: Setting quadrant texts:', quadrantSettings);
    
    const elements = {
        question: document.getElementById('question-text'),
        ul: document.getElementById('quadrant-ul-text'),
        ur: document.getElementById('quadrant-ur-text'),
        ll: document.getElementById('quadrant-ll-text'),
        lr: document.getElementById('quadrant-lr-text')
    };

    if (elements.question) elements.question.textContent = quadrantSettings.question || '';
    if (elements.ul) elements.ul.textContent = quadrantSettings.quadrant_ul || '';
    if (elements.ur) elements.ur.textContent = quadrantSettings.quadrant_ur || '';
    if (elements.ll) elements.ll.textContent = quadrantSettings.quadrant_ll || '';
    if (elements.lr) elements.lr.textContent = quadrantSettings.quadrant_lr || '';
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
