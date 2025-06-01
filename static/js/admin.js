/**
 * Admin panel functionality
 */

// グローバル変数
let currentUser = null;
let currentShokudo = null;

/**
 * Initialize admin panel
 */
function initAdminPanel(user, shokudo) {
    console.info('admin.js: Initializing admin panel with user:', user, 'shokudo:', shokudo);
    
    currentUser = user;
    currentShokudo = shokudo;
    
    const adminPanel = document.getElementById('admin-panel');
    const loading = document.getElementById('loading');
    const userRegistration = document.getElementById('user-registration');

    if (adminPanel) {
        console.info('admin.js: Showing admin panel');
        adminPanel.classList.remove('d-none');
        
        // フォームのセットアップを実行
        setupQuestionForm();
        setupColorForm();
        
        // Bootstrap タブイベントのセットアップ
        const questionTab = document.querySelector('#question-tab');
        const colorTab = document.querySelector('#color-tab');
        
        // 質問設定タブが表示されたときの処理
        if (questionTab) {
            questionTab.addEventListener('shown.bs.tab', () => {
                console.info('admin.js: Question tab shown');
                loadQuadrantSettings();
            });
        }
        
        // 色設定タブが表示されたときの処理
        if (colorTab) {
            colorTab.addEventListener('shown.bs.tab', () => {
                console.info('admin.js: Color tab shown');
                loadColorSettings();
            });
        }
        
        // 初期表示時の設定読み込み
        if (document.querySelector('#question.active')) {
            console.info('admin.js: Loading initial question settings');
            loadQuadrantSettings();
        }
    }

    if (loading) loading.classList.add('d-none');
    if (userRegistration) userRegistration.classList.add('d-none');
}

// 質問設定の読み込み関数を分離
function loadQuadrantSettings() {
    if (!currentShokudo) {
        console.error('admin.js: No shokudo data available');
        return;
    }

    console.info('admin.js: Loading quadrant settings...');
    fetch(`/api/get-settings?shokudoId=${currentShokudo.shokudo_id}`)
        .then(response => {
            console.info('admin.js: Settings API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.info('admin.js: Received settings data:', data);
            try {
                if (data.success && data.quadrant) {
                    // フォームの更新
                    updateQuadrantForm(data.quadrant);
                    // 表示の更新
                    updateQuadrantDisplay(data.quadrant);
                } else {
                    console.warn('admin.js: No quadrant data in response');
                }
            } catch (error) {
                console.error('admin.js: Error processing quadrant data:', error);
                throw error; // エラーを再スローしてcatchブロックで処理
            }
        })
        .catch(error => {
            console.error('admin.js: Error loading settings:', error);
            showError('設定の読み込みに失敗しました');
        });
}

// フォームの更新を別関数に分離
function updateQuadrantForm(quadrant) {
    const elements = {
        question: document.getElementById('questionText'),
        ul: document.getElementById('quadrantUL'),
        ur: document.getElementById('quadrantUR'),
        ll: document.getElementById('quadrantLL'),
        lr: document.getElementById('quadrantLR')
    };

    // nullチェック付きで値を設定
    if (elements.question) elements.question.value = quadrant.question || '';
    if (elements.ul) elements.ul.value = quadrant.quadrant_ul || '';
    if (elements.ur) elements.ur.value = quadrant.quadrant_ur || '';
    if (elements.ll) elements.ll.value = quadrant.quadrant_ll || '';
    if (elements.lr) elements.lr.value = quadrant.quadrant_lr || '';
}

/**
 * Update quadrant display
 */
function updateQuadrantDisplay(quadrant) {
    // 現在の設定表示部分の更新
    const currentSettings = document.getElementById('current-question-settings');
    if (currentSettings) {
        try {
            currentSettings.innerHTML = `
                <div class="card">
                    <div class="card-header">質問設定</div>
                    <div class="card-body">
                        <h5>質問文</h5>
                        <p>${quadrant.question || ''}</p>
                        <h5>回答選択肢</h5>
                        <div class="row">
                            <div class="col-6">
                                <strong>左上:</strong>
                                <p>${quadrant.quadrant_ul || ''}</p>
                            </div>
                            <div class="col-6">
                                <strong>右上:</strong>
                                <p>${quadrant.quadrant_ur || ''}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                <strong>左下:</strong>
                                <p>${quadrant.quadrant_ll || ''}</p>
                            </div>
                            <div class="col-6">
                                <strong>右下:</strong>
                                <p>${quadrant.quadrant_lr || ''}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('admin.js: Error updating quadrant display:', error);
            throw error;
        }
    } else {
        console.warn('admin.js: current-question-settings element not found');
    }
}

/**
 * Load settings for the current shokudo
 */
function loadSettings() {
    if (!currentShokudo) {
        console.error('admin.js: No shokudo data available');
        return;
    }

    console.info('admin.js: Loading settings for shokudo:', currentShokudo.shokudo_id);

    fetch(`/api/get-settings?shokudoId=${currentShokudo.shokudo_id}`)
        .then(response => {
            console.info('admin.js: Settings API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.info('admin.js: Received settings data:', data);
            if (data.success) {
                if (data.quadrant) {
                    console.info('admin.js: Setting quadrant values:', data.quadrant);
                    // フォームの値を設定
                    document.getElementById('questionText').value = data.quadrant.question || '';
                    document.getElementById('quadrantUL').value = data.quadrant.quadrant_ul || '';
                    document.getElementById('quadrantUR').value = data.quadrant.quadrant_ur || '';
                    document.getElementById('quadrantLL').value = data.quadrant.quadrant_ll || '';
                    document.getElementById('quadrantLR').value = data.quadrant.quadrant_lr || '';
                    
                    // 現在の設定表示部分も更新
                    const currentSettings = document.getElementById('current-question-settings');
                    if (currentSettings) {
                        currentSettings.innerHTML = `
                            <div class="card">
                                <div class="card-header">質問設定</div>
                                <div class="card-body">
                                    <h5>質問文</h5>
                                    <p>${data.quadrant.question || ''}</p>
                                    <h5>回答選択肢</h5>
                                    <div class="row">
                                        <div class="col-6">
                                            <strong>左上:</strong>
                                            <p>${data.quadrant.quadrant_ul || ''}</p>
                                        </div>
                                        <div class="col-6">
                                            <strong>右上:</strong>
                                            <p>${data.quadrant.quadrant_ur || ''}</p>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-6">
                                            <strong>左下:</strong>
                                            <p>${data.quadrant.quadrant_ll || ''}</p>
                                        </div>
                                        <div class="col-6">
                                            <strong>右下:</strong>
                                            <p>${data.quadrant.quadrant_lr || ''}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                } else {
                    console.info('admin.js: No quadrant data received');
                }
            } else {
                console.error('admin.js: Failed to load settings:', data.error);
                showError('設定の読み込みに失敗しました: ' + (data.error || '不明なエラー'));
            }
        })
        .catch(error => {
            console.error('admin.js: Error loading settings:', error);
            showError('設定の読み込み中にエラーが発生しました: ' + error.message);
        });
}

/**
 * Display quadrant settings
 */
function displayQuadrantSettings(settings) {
    // 要素の存在確認を追加
    const elements = {
        question: document.getElementById('current-question'),
        ul: document.getElementById('current-quadrant-ul'),
        ur: document.getElementById('current-quadrant-ur'),
        ll: document.getElementById('current-quadrant-ll'),
        lr: document.getElementById('current-quadrant-lr')
    };

    // 要素が存在するか確認してからテキストを設定
    if (elements.question) elements.question.textContent = settings.question || '';
    if (elements.ul) elements.ul.textContent = settings.quadrant_ul || '';
    if (elements.ur) elements.ur.textContent = settings.quadrant_ur || '';
    if (elements.ll) elements.ll.textContent = settings.quadrant_ll || '';
    if (elements.lr) elements.lr.textContent = settings.quadrant_lr || '';
}

/**
 * Display color settings
 */
function displayColorSettings(settings) {
    // 要素の存在確認を追加
    const elements = {
        red: document.getElementById('current-color-red'),
        green: document.getElementById('current-color-green'),
        blue: document.getElementById('current-color-blue'),
        yellow: document.getElementById('current-color-yellow')
    };

    // 要素が存在するか確認してからテキストを設定
    if (elements.red) elements.red.textContent = settings.color_red || '';
    if (elements.green) elements.green.textContent = settings.color_green || '';
    if (elements.blue) elements.blue.textContent = settings.color_blue || '';
    if (elements.yellow) elements.yellow.textContent = settings.color_yellow || '';
}

/**
 * Setup question form submission
 */
function setupQuestionForm() {
    const form = document.getElementById('question-form');
    if (!form) {
        console.error('admin.js: Question form not found');
        return;
    }

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        console.info('admin.js: Question form submitted');
        
        const formData = {
            shokudo_id: currentShokudo.shokudo_id,
            question: document.getElementById('questionText').value,
            quadrant_ul: document.getElementById('quadrantUL').value,
            quadrant_ur: document.getElementById('quadrantUR').value,
            quadrant_ll: document.getElementById('quadrantLL').value,
            quadrant_lr: document.getElementById('quadrantLR').value
        };

        console.info('admin.js: Form data:', formData);
        saveQuadrantSettings(formData);
    });
}

/**
 * Setup color form submission
 */
function setupColorForm() {
    const form = document.getElementById('color-form');
    if (!form) {
        console.error('admin.js: Color form not found');
        return;
    }

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        console.info('admin.js: Color form submitted');
        
        // フィールド名をAPIの期待する形式に修正
        const formData = {
            shokudoId: currentShokudo.shokudo_id, // shokudo_id から shokudoId に変更
            red: document.getElementById('colorRed').value,
            green: document.getElementById('colorGreen').value,
            blue: document.getElementById('colorBlue').value,
            yellow: document.getElementById('colorYellow').value
        };

        console.info('admin.js: Sending color settings:', formData);
        saveColorSettings(formData);
    });
}

/**
 * Save quadrant settings
 */
function saveQuadrantSettings(settings) {
    console.info('admin.js: Saving quadrant settings:', settings);

    // 保存メッセージを非表示に
    const saveMessage = document.getElementById('question-save-message');
    if (saveMessage) {
        saveMessage.style.display = 'none';
    }

    fetch('/api/update-quadrant', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        console.info('admin.js: Save response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.info('admin.js: Save response data:', data);
        if (data.success) {
            // 保存成功後に再読み込み
            loadQuadrantSettings();
            
            // 成功メッセージを表示
            if (saveMessage) {
                saveMessage.style.display = 'inline';
                // 3秒後にメッセージを非表示
                setTimeout(() => {
                    saveMessage.style.display = 'none';
                }, 3000);
            }
        } else {
            console.error('admin.js: Save failed:', data.error);
            showError(`質問設定の保存に失敗しました: ${data.error || '不明なエラー'}`);
        }
    })
    .catch(error => {
        console.error('admin.js: Error saving quadrant settings:', error);
        showError('質問設定の保存中にエラーが発生しました: ' + error.message);
    });
}

/**
 * Save color settings
 */
function saveColorSettings(settings) {
    console.info('admin.js: Sending color settings:', settings);

    // 保存メッセージを非表示に
    const saveMessage = document.getElementById('color-save-message');
    if (saveMessage) {
        saveMessage.style.display = 'none';
    }

    fetch('/api/update-color', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        console.info('admin.js: Response status:', response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 成功時の処理
            loadColorSettings();
            
            // 成功メッセージを表示
            if (saveMessage) {
                saveMessage.style.display = 'inline';
                setTimeout(() => {
                    saveMessage.style.display = 'none';
                }, 3000);
            }
        } else {
            console.error('admin.js: Save failed:', data.error);
            showError(`色設定の保存に失敗しました: ${data.error || ''}`);
        }
    })
    .catch(error => {
        console.error('admin.js: Error saving color settings:', error);
        showError('色設定の保存中にエラーが発生しました: ' + error.message);
    });
}

/**
 * Load color settings
 */
function loadColorSettings() {
    if (!currentShokudo) {
        console.error('admin.js: No shokudo data available');
        return;
    }

    console.info('admin.js: Loading color settings...');
    fetch(`/api/get-settings?shokudoId=${currentShokudo.shokudo_id}`)
        .then(response => {
            console.info('admin.js: Settings API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.info('admin.js: Received settings data:', data);
            try {
                if (data.success && data.color) {
                    // フォームの更新
                    updateColorForm(data.color);
                    // 表示の更新
                    updateColorDisplay(data.color);
                } else {
                    console.warn('admin.js: No color data in response');
                }
            } catch (error) {
                console.error('admin.js: Error processing color data:', error);
                throw error;
            }
        })
        .catch(error => {
            console.error('admin.js: Error loading color settings:', error);
            showError('色設定の読み込みに失敗しました');
        });
}

/**
 * Update color form with values
 */
function updateColorForm(color) {
    const elements = {
        red: document.getElementById('colorRed'),
        green: document.getElementById('colorGreen'),
        blue: document.getElementById('colorBlue'),
        yellow: document.getElementById('colorYellow')
    };

    // nullチェック付きで値を設定
    if (elements.red) elements.red.value = color.color_red || '';
    if (elements.green) elements.green.value = color.color_green || '';
    if (elements.blue) elements.blue.value = color.color_blue || '';
    if (elements.yellow) elements.yellow.value = color.color_yellow || '';
}

/**
 * Update color display
 */
function updateColorDisplay(color) {
    const currentSettings = document.getElementById('current-color-settings');
    if (currentSettings) {
        try {
            currentSettings.innerHTML = `
                <div class="card">
                    <div class="card-header">色の意味設定</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <strong><span class="badge bg-danger">赤</span>:</strong>
                                <p>${color.color_red || ''}</p>
                            </div>
                            <div class="col-6">
                                <strong><span class="badge bg-success">緑</span>:</strong>
                                <p>${color.color_green || ''}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                <strong><span class="badge bg-primary">青</span>:</strong>
                                <p>${color.color_blue || ''}</p>
                            </div>
                            <div class="col-6">
                                <strong><span class="badge bg-warning">黄</span>:</strong>
                                <p>${color.color_yellow || ''}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('admin.js: Error updating color display:', error);
            throw error;
        }
    } else {
        console.warn('admin.js: current-color-settings element not found');
    }
}

/**
 * Set current values for quadrant form
 */
function setQuadrantFormValues(settings) {
    console.info('admin.js: Setting quadrant form values:', settings);
    
    const questionInput = document.getElementById('questionText');
    const ulInput = document.getElementById('quadrantUL');
    const urInput = document.getElementById('quadrantUR');
    const llInput = document.getElementById('quadrantLL');
    const lrInput = document.getElementById('quadrantLR');

    if (questionInput) questionInput.value = settings.question || '';
    if (ulInput) ulInput.value = settings.quadrant_ul || '';
    if (urInput) urInput.value = settings.quadrant_ur || '';
    if (llInput) llInput.value = settings.quadrant_ll || '';
    if (lrInput) lrInput.value = settings.quadrant_lr || '';
}

/**
 * Set color form values
 */
function setColorFormValues(settings) {
    console.info('admin.js: Setting color form values:', settings);
    
    const redInput = document.getElementById('colorRed');
    const greenInput = document.getElementById('colorGreen');
    const blueInput = document.getElementById('colorBlue');
    const yellowInput = document.getElementById('colorYellow');

    if (redInput) redInput.value = settings.color_red || '';
    if (greenInput) greenInput.value = settings.color_green || '';
    if (blueInput) blueInput.value = settings.color_blue || '';
    if (yellowInput) yellowInput.value = settings.color_yellow || '';
}

/**
 * Show error message
 */
function showError(message) {
    console.error('admin.js:', message);
    alert(message);  // TODO: Replace with better error display
}

// Make initAdminPanel globally available
window.initAdminPanel = initAdminPanel;
