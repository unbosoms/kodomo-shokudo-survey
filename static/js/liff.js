/**
 * LIFF Initialization and Authentication
 */

// Initialize LIFF when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize LIFF
    initializeLiff();
});

/**
 * Initialize LIFF
 */
function initializeLiff() {
    // Check if liffId is defined
    if (!liffId) {
        showError('LIFF ID is missing');
        return;
    }
    
    // Initialize LIFF
    liff.init({ liffId: liffId })
        .then(() => {
            // Check if running in LINE browser
            if (!liff.isInClient() && !liff.isLoggedIn()) {
                // Not in LINE browser and not logged in
                liff.login();
            } else {
                // Successfully initialized
                onLiffInitialized();
            }
        })
        .catch((error) => {
            showError(`LIFF initialization failed: ${error.message}`);
        });
}

/**
 * Called after LIFF is initialized
 */
function onLiffInitialized() {
    // Hide loading spinner
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.classList.add('d-none');
    }
    
    // Get user profile
    liff.getProfile()
        .then(profile => {
            console.info('liff.js: Got user profile:', profile.userId, profile.displayName);
            
            // Store user info in form fields
            const userIdElement = document.getElementById('userId');
            if (userIdElement) {
                userIdElement.value = profile.userId;
            }
            
            const displayNameElement = document.getElementById('displayName');
            if (displayNameElement) {
                displayNameElement.value = profile.displayName;
            }
            
            // Check user registration status
            checkUserRegistration(profile);
        })
        .catch(error => {
            console.error('liff.js: Failed to get profile:', error);
            showError(`Failed to get profile: ${error.message}`);
        });
}

/**
 * Check if user is admin
 */
function checkAdminStatus(profile) {
    console.info('liff.js: Checking admin status for user ID:', profile.userId);
    
    // Call API to check admin status
    fetch('/api/check-user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userId: profile.userId,
            displayName: profile.displayName
        })
    })
    .then(response => {
        console.info('liff.js: Got response from /api/check-user:', response.status);
        return response.json();
    })
    .then(data => {
        console.info('liff.js: Admin check data:', data);
        
        if (data.success) {
            if (data.isAdmin) {
                // User is admin, show admin panel
                console.info('liff.js: User is admin, showing admin panel');
                showAdminPanel();
            } else {
                // User is not admin, show error
                console.error('liff.js: User is not admin');
                showError('管理者権限がありません');
                
                // Show admin auth container
                const adminAuthElement = document.getElementById('admin-auth');
                if (adminAuthElement) {
                    adminAuthElement.classList.remove('d-none');
                    
                    // Show message
                    const authMessageElement = document.getElementById('auth-message');
                    if (authMessageElement) {
                        authMessageElement.innerHTML = `
                            <div class="alert alert-danger">
                                <strong>アクセス拒否</strong><br>
                                ユーザー ${profile.displayName} (${profile.userId}) は管理者として登録されていません。
                            </div>
                        `;
                    }
                }
            }
        } else {
            console.error('liff.js: Failed to check admin status:', data.error);
            showError('管理者権限の確認に失敗しました: ' + (data.error || '不明なエラー'));
        }
    })
    .catch(error => {
        console.error('liff.js: API error in checkAdminStatus:', error);
        showError(`API エラー: ${error.message}`);
    });
}

/**
 * Check if user is registered
 */
function checkUserRegistration(profile) {
    console.info('liff.js: Checking user registration for user ID:', profile.userId);
    
    fetch('/api/check-user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            userId: profile.userId,
            displayName: profile.displayName
        })
    })
    .then(response => response.json())
    .then(data => {
        console.info('liff.js: User registration data:', data);
        
        if (data.success) {
            if (data.isRegistered) {
                // User is registered, show admin panel or main app
                console.info('liff.js: User is registered');
                if (window.location.pathname.includes('/admin')) {
                    if (typeof initAdminPanel === 'function') {
                        console.info('liff.js: Calling initAdminPanel');
                        initAdminPanel(data.user, data.shokudo);
                    } else {
                        console.error('liff.js: initAdminPanel function not found');
                        showError('管理画面の初期化に失敗しました: initAdminPanel関数が見つかりません');
                    }
                } else if (window.location.pathname.startsWith('/results')) {
                    if (typeof initResultsPage === 'function') {
                        console.info('liff.js: Calling initResultsPage');
                        initResultsPage(data.user, data.shokudo);
                    } else {
                        console.error('liff.js: initResultsPage function not found');
                        showError('集計結果ページの初期化に失敗しました');
                    }
                } else {
                    initializeMainApp(data.user, data.shokudo);
                }
            } else {
                // User is not registered
                console.info('liff.js: User is not registered');
                if (window.location.pathname.startsWith('/results')) {
                    // 未登録ユーザーはトップページへ
                    window.location.href = '/';
                } else {
                    showRegistrationForm();
                }
            }
        } else {
            console.error('liff.js: Failed to check user registration:', data.error);
            showError('ユーザー情報の確認に失敗しました: ' + (data.error || '不明なエラー'));
        }
    })
    .catch(error => {
        console.error('liff.js: API error in checkUserRegistration:', error);
        showError(`API エラー: ${error.message}`);
    });
}

/**
 * Show registration form
 */
function showRegistrationForm() {
    // Show registration form
    document.getElementById('registration-form').classList.remove('d-none');
    
    // Load available children's cafeterias
    loadShokudoList();
    
    // Set up form submission
    document.getElementById('user-form').addEventListener('submit', function(event) {
        event.preventDefault();
        
        const userId = document.getElementById('userId').value;
        const displayName = document.getElementById('displayName').value;
        const shokudoId = document.getElementById('shokudoId').value;
        
        if (!userId || !displayName || !shokudoId) {
            showError('すべての項目を入力してください');
            return;
        }
        
        // Register user
        fetch('/api/register-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: userId,
                displayName: displayName,
                shokudoId: shokudoId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload page to show main app
                location.reload();
            } else {
                showError('ユーザー登録に失敗しました');
            }
        })
        .catch(error => {
            showError(`API error: ${error.message}`);
        });
    });
}

/**
 * Load list of children's cafeterias
 */
function loadShokudoList() {
    console.info('liff.js: Starting loadShokudoList');
    const apiUrl = window.location.origin + '/api/get-shokudos';
    console.info('liff.js: Fetching from:', apiUrl);

    fetch(apiUrl)
        .then(response => {
            console.info('liff.js: Shokudo list response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.info('liff.js: Shokudo list data:', data);
            
            if (data.success && data.shokudos) {
                const select = document.getElementById('shokudoId');
                
                // Clear existing options except the first one
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                // Add options for each children's cafeteria
                data.shokudos.forEach(shokudo => {
                    const option = document.createElement('option');
                    option.value = shokudo.shokudo_id;
                    option.textContent = shokudo.shokudo_name;
                    select.appendChild(option);
                });
            } else {
                showError('こども食堂の一覧の取得に失敗しました');
            }
        })
        .catch(error => {
            console.error('liff.js: Error loading shokudo list:', error);
            showError(`こども食堂の一覧の取得に失敗しました: ${error.message}`);
        });
}

/**
 * Initialize main application
 * This function calls the showMainApp function in app.js
 */
function initializeMainApp(user, shokudo) {
    console.info('liff.js: Initializing main app with user:', user, 'shokudo:', shokudo);
    
    try {
        // Load settings
        loadSettings(shokudo.shokudo_id);
        
        // Call the showMainApp function from app.js
        if (typeof window.showMainApp === 'function') {
            window.showMainApp(user, shokudo);
        } else {
            console.error('liff.js: showMainApp function not found in global scope');
            showError('アプリの初期化に失敗しました: showMainApp関数が見つかりません');
        }
    } catch (error) {
        console.error('liff.js: Error in initializeMainApp:', error);
        showError('アプリの初期化中にエラーが発生しました: ' + error.message);
    }
}

/**
 * Load settings for the children's cafeteria
 */
function loadSettings(shokudoId) {
    console.info('liff.js: Starting loadSettings for shokudo:', shokudoId);
    const apiUrl = window.location.origin + `/api/get-settings?shokudoId=${shokudoId}`;
    console.info('liff.js: Fetching from:', apiUrl);

    fetch(apiUrl)
        .then(response => {
            console.info('liff.js: Settings response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.info('liff.js: Settings data:', data);
            if (data.success) {
                // Set question text
                if (data.quadrant && data.quadrant.question) {
                    document.getElementById('question-text').textContent = data.quadrant.question;
                }
                
                // Set quadrant answers
                if (data.quadrant) {
                    document.getElementById('quadrant-ul').textContent = data.quadrant.quadrant_ul || '';
                    document.getElementById('quadrant-ur').textContent = data.quadrant.quadrant_ur || '';
                    document.getElementById('quadrant-ll').textContent = data.quadrant.quadrant_ll || '';
                    document.getElementById('quadrant-lr').textContent = data.quadrant.quadrant_lr || '';
                }
                
                // Set color meanings
                if (data.color) {
                    document.getElementById('color-red').textContent = data.color.red || '';
                    document.getElementById('color-green').textContent = data.color.green || '';
                    document.getElementById('color-blue').textContent = data.color.blue || '';
                    document.getElementById('color-yellow').textContent = data.color.yellow || '';
                }
            } else {
                console.error('liff.js: Failed to get settings:', data.error);
                showError('設定の取得に失敗しました');
            }
        })
        .catch(error => {
            console.error('liff.js: Error loading settings:', error, 'Stack:', error.stack);
            showError(`設定の取得に失敗しました: ${error.message}`);
        });
}

/**
 * Show admin panel
 */
function showAdminPanel() {
    // This function is implemented in admin.js
    if (typeof initAdminPanel === 'function') {
        initAdminPanel();
    } else {
        showError('管理画面の初期化に失敗しました');
    }
}

/**
 * Show error message
 */
function showError(message) {
    console.error(message);
    
    // Create alert if it doesn't exist
    let alertElement = document.getElementById('error-alert');
    if (!alertElement) {
        alertElement = document.createElement('div');
        alertElement.id = 'error-alert';
        alertElement.className = 'alert alert-danger mt-3';
        alertElement.role = 'alert';
        
        // Insert at the top of the container
        const container = document.querySelector('.container');
        container.insertBefore(alertElement, container.firstChild);
    }
    
    // Set message
    alertElement.textContent = message;
    
    // Hide loading spinner if visible
    document.getElementById('loading').classList.add('d-none');
}
