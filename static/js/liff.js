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
            
            // Store user info in form fields if they exist
            const userIdElement = document.getElementById('userId');
            if (userIdElement) {
                userIdElement.value = profile.userId;
            }
            
            const displayNameElement = document.getElementById('displayName');
            if (displayNameElement) {
                displayNameElement.value = profile.displayName;
            }
            
            // Check if we're on the admin page
            if (window.location.pathname.includes('/admin')) {
                console.info('liff.js: On admin page, checking if user is admin');
                // For admin page, we only need to check if user is admin
                checkAdminStatus(profile);
            } else {
                // For main app, check user registration status
                console.info('liff.js: On main page, checking user registration');
                checkUserRegistration(profile);
            }
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
    
    // Call API to check user registration
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
        console.info('liff.js: User registration data:', data);
        
        if (data.success) {
            if (data.isAdmin) {
                // User is admin, show admin panel
                console.info('liff.js: User is admin, showing admin panel');
                showAdminPanel();
            } else if (data.isRegistered) {
                // User is registered, show main app
                console.info('liff.js: User is registered, showing main app');
                
                // Hide loading and registration form if visible
                document.getElementById('loading').classList.add('d-none');
                document.getElementById('registration-form').classList.add('d-none');
                
                // Call initializeMainApp with user and shokudo data
                initializeMainApp(data.user, data.shokudo);
            } else {
                // User is not registered, show registration form
                console.info('liff.js: User is not registered, showing registration form');
                showRegistrationForm();
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
    fetch('/api/get-shokudos')
        .then(response => response.json())
        .then(data => {
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
            showError(`API error: ${error.message}`);
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
    fetch(`/api/get-settings?shokudoId=${shokudoId}`)
        .then(response => response.json())
        .then(data => {
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
                showError('設定の取得に失敗しました');
            }
        })
        .catch(error => {
            showError(`API error: ${error.message}`);
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
