/**
 * Admin panel functionality
 */

/**
 * Initialize admin panel
 */
function initAdminPanel() {
    // Show admin panel
    document.getElementById('admin-panel').classList.remove('d-none');
    
    // Load children's cafeterias
    loadShokudoList();
    
    // Set up form submissions
    setupShokudoForm();
    setupQuestionForm();
    setupColorForm();
    
    // Set up settings display
    setupSettingsDisplay();
}

/**
 * Load list of children's cafeterias
 */
function loadShokudoList() {
    fetch('/api/get-shokudos')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.shokudos) {
                // Populate shokudo list table
                populateShokudoTable(data.shokudos);
                
                // Populate shokudo select dropdowns
                populateShokudoSelects(data.shokudos);
            } else {
                showError('こども食堂の一覧の取得に失敗しました');
            }
        })
        .catch(error => {
            showError(`API error: ${error.message}`);
        });
}

/**
 * Populate children's cafeteria table
 */
function populateShokudoTable(shokudos) {
    const tableBody = document.getElementById('shokudo-list');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add row for each children's cafeteria
    shokudos.forEach(shokudo => {
        const row = document.createElement('tr');
        
        // ID cell
        const idCell = document.createElement('td');
        idCell.textContent = shokudo.shokudo_id;
        row.appendChild(idCell);
        
        // Name cell
        const nameCell = document.createElement('td');
        nameCell.textContent = shokudo.shokudo_name;
        row.appendChild(nameCell);
        
        // Address cell
        const addressCell = document.createElement('td');
        addressCell.textContent = shokudo.address || '';
        row.appendChild(addressCell);
        
        // Actions cell
        const actionsCell = document.createElement('td');
        
        // Edit button
        const editButton = document.createElement('button');
        editButton.className = 'btn btn-sm btn-outline-primary me-2';
        editButton.textContent = '編集';
        editButton.addEventListener('click', () => {
            // TODO: Implement edit functionality
            alert('編集機能は現在開発中です');
        });
        actionsCell.appendChild(editButton);
        
        row.appendChild(actionsCell);
        
        // Add row to table
        tableBody.appendChild(row);
    });
}

/**
 * Populate children's cafeteria select dropdowns
 */
function populateShokudoSelects(shokudos) {
    // Get all select elements
    const selects = [
        document.getElementById('questionShokudoId'),
        document.getElementById('currentQuestionShokudoId'),
        document.getElementById('colorShokudoId'),
        document.getElementById('currentColorShokudoId')
    ];
    
    // Populate each select
    selects.forEach(select => {
        if (!select) return;
        
        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Add options for each children's cafeteria
        shokudos.forEach(shokudo => {
            const option = document.createElement('option');
            option.value = shokudo.shokudo_id;
            option.textContent = shokudo.shokudo_name;
            select.appendChild(option);
        });
    });
}

/**
 * Set up children's cafeteria form
 */
function setupShokudoForm() {
    const form = document.getElementById('shokudo-form');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form data
        const shokudoName = document.getElementById('shokudoName').value;
        const address = document.getElementById('address').value;
        const latitude = document.getElementById('latitude').value;
        const longitude = document.getElementById('longitude').value;
        
        if (!shokudoName) {
            showError('こども食堂名を入力してください');
            return;
        }
        
        // Show loading spinner
        document.getElementById('loading').classList.remove('d-none');
        
        // Submit form
        fetch('/api/register-shokudo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                shokudoName: shokudoName,
                address: address,
                latitude: latitude,
                longitude: longitude
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            if (data.success) {
                // Show success message
                alert('こども食堂を登録しました');
                
                // Clear form
                form.reset();
                
                // Reload children's cafeterias
                loadShokudoList();
            } else {
                showError(data.error || 'こども食堂の登録に失敗しました');
            }
        })
        .catch(error => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            showError(`API error: ${error.message}`);
        });
    });
}

/**
 * Set up question form
 */
function setupQuestionForm() {
    const form = document.getElementById('question-form');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form data
        const shokudoId = document.getElementById('questionShokudoId').value;
        const question = document.getElementById('questionText').value;
        const quadrantUL = document.getElementById('quadrantUL').value;
        const quadrantUR = document.getElementById('quadrantUR').value;
        const quadrantLL = document.getElementById('quadrantLL').value;
        const quadrantLR = document.getElementById('quadrantLR').value;
        
        if (!shokudoId || !question || !quadrantUL || !quadrantUR || !quadrantLL || !quadrantLR) {
            showError('すべての項目を入力してください');
            return;
        }
        
        // Show loading spinner
        document.getElementById('loading').classList.remove('d-none');
        
        // Submit form
        fetch('/api/update-quadrant', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                shokudoId: shokudoId,
                question: question,
                quadrantUL: quadrantUL,
                quadrantUR: quadrantUR,
                quadrantLL: quadrantLL,
                quadrantLR: quadrantLR
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            if (data.success) {
                // Show success message
                alert('質問設定を保存しました');
                
                // Clear form
                form.reset();
                
                // Update current settings display
                document.getElementById('currentQuestionShokudoId').value = shokudoId;
                loadQuadrantSettings(shokudoId);
            } else {
                showError(data.error || '質問設定の保存に失敗しました');
            }
        })
        .catch(error => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            showError(`API error: ${error.message}`);
        });
    });
}

/**
 * Set up color form
 */
function setupColorForm() {
    const form = document.getElementById('color-form');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form data
        const shokudoId = document.getElementById('colorShokudoId').value;
        const red = document.getElementById('colorRed').value;
        const green = document.getElementById('colorGreen').value;
        const blue = document.getElementById('colorBlue').value;
        const yellow = document.getElementById('colorYellow').value;
        
        if (!shokudoId || !red || !green || !blue || !yellow) {
            showError('すべての項目を入力してください');
            return;
        }
        
        // Show loading spinner
        document.getElementById('loading').classList.remove('d-none');
        
        // Submit form
        fetch('/api/update-color', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                shokudoId: shokudoId,
                red: red,
                green: green,
                blue: blue,
                yellow: yellow
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            if (data.success) {
                // Show success message
                alert('色設定を保存しました');
                
                // Clear form
                form.reset();
                
                // Update current settings display
                document.getElementById('currentColorShokudoId').value = shokudoId;
                loadColorSettings(shokudoId);
            } else {
                showError(data.error || '色設定の保存に失敗しました');
            }
        })
        .catch(error => {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');
            
            showError(`API error: ${error.message}`);
        });
    });
}

/**
 * Set up settings display
 */
function setupSettingsDisplay() {
    // Set up question settings display
    document.getElementById('currentQuestionShokudoId').addEventListener('change', function() {
        const shokudoId = this.value;
        if (shokudoId) {
            loadQuadrantSettings(shokudoId);
        }
    });
    
    // Set up color settings display
    document.getElementById('currentColorShokudoId').addEventListener('change', function() {
        const shokudoId = this.value;
        if (shokudoId) {
            loadColorSettings(shokudoId);
        }
    });
}

/**
 * Load quadrant settings
 */
function loadQuadrantSettings(shokudoId) {
    fetch(`/api/get-settings?shokudoId=${shokudoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.quadrant) {
                // Show settings container
                document.getElementById('current-question-settings').classList.remove('d-none');
                
                // Set question text
                document.getElementById('current-question-text').textContent = data.quadrant.question || '';
                
                // Set quadrant answers
                document.getElementById('current-quadrant-ul').textContent = data.quadrant.quadrant_ul || '';
                document.getElementById('current-quadrant-ur').textContent = data.quadrant.quadrant_ur || '';
                document.getElementById('current-quadrant-ll').textContent = data.quadrant.quadrant_ll || '';
                document.getElementById('current-quadrant-lr').textContent = data.quadrant.quadrant_lr || '';
            } else {
                // Hide settings container
                document.getElementById('current-question-settings').classList.add('d-none');
                
                // Show message if no settings found
                if (!data.error) {
                    showError('この食堂の質問設定はまだありません');
                } else {
                    showError(data.error || '質問設定の取得に失敗しました');
                }
            }
        })
        .catch(error => {
            showError(`API error: ${error.message}`);
        });
}

/**
 * Load color settings
 */
function loadColorSettings(shokudoId) {
    fetch(`/api/get-settings?shokudoId=${shokudoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.color) {
                // Show settings container
                document.getElementById('current-color-settings').classList.remove('d-none');
                
                // Set color meanings
                document.getElementById('current-color-red').textContent = data.color.red || '';
                document.getElementById('current-color-green').textContent = data.color.green || '';
                document.getElementById('current-color-blue').textContent = data.color.blue || '';
                document.getElementById('current-color-yellow').textContent = data.color.yellow || '';
            } else {
                // Hide settings container
                document.getElementById('current-color-settings').classList.add('d-none');
                
                // Show message if no settings found
                if (!data.error) {
                    showError('この食堂の色設定はまだありません');
                } else {
                    showError(data.error || '色設定の取得に失敗しました');
                }
            }
        })
        .catch(error => {
            showError(`API error: ${error.message}`);
        });
}
