/**
 * Camera functionality for taking and processing photos
 */

// Global variables
let stream = null;
let videoElement = null;
let canvasElement = null;
let guideOverlayElement = null;
let photoData = null;

/**
 * Initialize camera
 */
function initCamera() {
    // Get elements
    videoElement = document.getElementById('camera');
    canvasElement = document.getElementById('canvas');
    guideOverlayElement = document.getElementById('guide-overlay');
    
    // Check if camera is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('お使いのブラウザはカメラをサポートしていません');
        return;
    }
    
    // Request camera access
    navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: 'environment',
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            aspectRatio: { ideal: 4/3 }
        }
    })
    .then(function(s) {
        stream = s;
        videoElement.srcObject = stream;
        
        // カメラ起動後のUI更新
        document.getElementById('start-camera').classList.add('d-none');
        videoElement.classList.remove('d-none');
        
        // ボタンのイベントリスナーを設定
        const takePhotoButton = document.getElementById('take-photo');
        const retakePhotoButton = document.getElementById('retake-photo');
        const uploadPhotoButton = document.getElementById('upload-photo');
        
        takePhotoButton.addEventListener('click', takePhoto);
        retakePhotoButton.addEventListener('click', retakePhoto);
        uploadPhotoButton.addEventListener('click', uploadPhoto);
        
        // Play video
        videoElement.play();
        
        // Wait for video to be ready
        videoElement.onloadedmetadata = function() {
            // Show take photo button
            takePhotoButton.classList.remove('d-none');
            
            // Load guide overlay
            loadGuideOverlay();
        };
    })
    .catch(function(error) {
        console.error('camera.js: Error starting camera:', error);
        showError('カメラの起動に失敗しました: ' + error.message);
    });
}

/**
 * Load guide overlay (クライアントサイドで生成)
 */
function loadGuideOverlay() {
    const wrapper = document.querySelector('.camera-aspect-wrapper');
    const width = wrapper.clientWidth;
    const height = wrapper.clientHeight;

    if (!width || !height) {
        setTimeout(loadGuideOverlay, 100);
        return;
    }

    drawGuideLines(width, height);
}

/**
 * Draw guide lines on overlay
 */
function drawGuideLines(width, height) {
    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.width = width;
    overlayCanvas.height = height;
    const ctx = overlayCanvas.getContext('2d');
    const midX = width / 2;
    const midY = height / 2;
    const margin = 8;

    // 外枠ガイド（緑）: 台紙をこの枠に合わせる
    ctx.strokeStyle = 'rgba(0, 200, 0, 0.8)';
    ctx.lineWidth = 3;
    ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);

    // 十字線（赤）: 4象限の境界
    ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(margin, midY);
    ctx.lineTo(width - margin, midY);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(midX, margin);
    ctx.lineTo(midX, height - margin);
    ctx.stroke();

    // 象限ラベル（日本語）
    ctx.fillStyle = 'rgba(255, 50, 50, 0.95)';
    ctx.font = 'bold 15px sans-serif';
    ctx.fillText('左上', margin + 6, midY - 8);
    ctx.fillText('右上', midX + 8, midY - 8);
    ctx.fillText('左下', margin + 6, height - margin - 8);
    ctx.fillText('右下', midX + 8, height - margin - 8);

    // 案内文（緑）
    ctx.fillStyle = 'rgba(0, 180, 0, 0.9)';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('台紙をこの枠に合わせてください', midX, margin + 18);

    guideOverlayElement.src = overlayCanvas.toDataURL('image/png');
    guideOverlayElement.style.display = 'block';
}

/**
 * Take photo
 */
function takePhoto() {
    console.info('camera.js: takePhoto button clicked');

    // object-fit: cover の表示領域に合わせてクロップ
    const wrapper = document.querySelector('.camera-aspect-wrapper');
    const containerW = wrapper.clientWidth;
    const containerH = wrapper.clientHeight;
    const videoW = videoElement.videoWidth;
    const videoH = videoElement.videoHeight;

    const scaleX = containerW / videoW;
    const scaleY = containerH / videoH;
    const scale = Math.max(scaleX, scaleY);

    const visibleW = containerW / scale;
    const visibleH = containerH / scale;
    const offsetX = (videoW - visibleW) / 2;
    const offsetY = (videoH - visibleH) / 2;

    canvasElement.width = Math.round(visibleW);
    canvasElement.height = Math.round(visibleH);

    const context = canvasElement.getContext('2d');
    context.drawImage(videoElement, offsetX, offsetY, visibleW, visibleH,
                      0, 0, canvasElement.width, canvasElement.height);

    // UI更新：表示の切り替え
    videoElement.classList.add('d-none');
    guideOverlayElement.style.display = 'none';
    canvasElement.classList.remove('d-none');

    // ボタンの表示を切り替え
    const takePhotoButton = document.getElementById('take-photo');
    const retakePhotoButton = document.getElementById('retake-photo');
    const uploadPhotoButton = document.getElementById('upload-photo');

    takePhotoButton.classList.add('d-none');
    retakePhotoButton.classList.remove('d-none');
    uploadPhotoButton.classList.remove('d-none');

    // 写真データを保存：画質0.8で圧縮
    photoData = canvasElement.toDataURL('image/jpeg', 0.8);
}

/**
 * Retake photo
 */
function retakePhoto() {
    // プレビューを非表示にしてビデオを表示
    canvasElement.classList.add('d-none');
    videoElement.classList.remove('d-none');
    guideOverlayElement.style.display = 'block';

    // ボタンの表示を切り替え
    document.getElementById('take-photo').classList.remove('d-none');
    document.getElementById('retake-photo').classList.add('d-none');
    document.getElementById('upload-photo').classList.add('d-none');

    // 写真データをクリア
    photoData = null;
}

/**
 * Upload photo
 */
function uploadPhoto() {
    console.info('camera.js: upload button clicked');
    if (!photoData) {
        showError('写真が撮影されていません');
        return;
    }

    // カメラコンテナ全体を非表示
    const cameraContainer = document.querySelector('.camera-container');
    if (cameraContainer) {
        cameraContainer.classList.add('d-none');
    }

    // ローディング表示を表示
    const loading = document.getElementById('loading');
    if (loading) {
        loading.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><div class="mt-2">計算中...</div></div>';
        loading.classList.remove('d-none');
    }

    // 画像をリサイズ（横長4:3を維持）
    resizeImage(photoData, 1600, 1200, function(resizedImageData) {
        console.info('Image resized for upload. Original size vs. New size (bytes):', 
                    photoData.length, resizedImageData.length);
        
        // FormDataの作成
        const formData = new FormData();
        const blob = dataURLtoBlob(resizedImageData);
        
        formData.append('image', blob, 'photo.jpg');
        formData.append('shokudoId', currentShokudo.shokudo_id);
        formData.append('userId', currentUser.user_id);
        formData.append('eventDate', document.getElementById('event-date').value);

        // アップロード実行
        uploadWithRetry('/api/upload', formData, 3);
    });
}

/**
 * Upload with retry logic
 */
function uploadWithRetry(url, formData, maxRetries, currentRetry = 0) {
    console.info(`Attempting upload (attempt ${currentRetry + 1} of ${maxRetries})...`);
    
    // Set longer timeout for the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        // Clear the timeout
        clearTimeout(timeoutId);

        // レスポンスのJSONを読み取る（エラー時も内容を取得するため）
        return response.json().then(data => ({ ok: response.ok, status: response.status, data }));
    })
    .then(({ ok, status, data }) => {
        // Hide loading spinner
        document.getElementById('loading').classList.add('d-none');

        if (ok && data.success) {
            // Show results
            showResults(data.counts);

            // Close LIFF browser after 5 seconds if in LINE
            if (liff.isInClient()) {
                setTimeout(() => {
                    liff.closeWindow();
                }, 5000);
            }
        } else {
            // エラー種別に応じた日本語メッセージを表示
            const errorMessages = {
                'image_processing': '画像処理に失敗しました。アンケート用紙がしっかり映るように撮り直してください。',
                'drive_upload': 'Google Driveへのアップロードに失敗しました。しばらく待ってから再度お試しください。'
            };
            const errorType = data.error_type;
            const userMessage = errorMessages[errorType] || data.error || 'エラーが発生しました。もう一度お試しください。';

            console.error(`Upload failed (error_type=${errorType}, status=${status}):`, data.error);
            showError(userMessage);

            // Re-enable buttons
            document.getElementById('retake-photo').disabled = false;
            document.getElementById('upload-photo').disabled = false;
        }
    })
    .catch(error => {
        // Clear the timeout
        clearTimeout(timeoutId);

        console.error('Upload error:', error);

        // Check if we should retry
        if (currentRetry < maxRetries - 1) {
            console.info(`Upload failed. Retrying... (${currentRetry + 1}/${maxRetries})`);

            // Show retry message
            const loadingElement = document.getElementById('loading');
            if (loadingElement) {
                // Create retry message if it doesn't exist
                let retryMessage = document.getElementById('retry-message');
                if (!retryMessage) {
                    retryMessage = document.createElement('div');
                    retryMessage.id = 'retry-message';
                    retryMessage.className = 'text-center mt-2';
                    loadingElement.appendChild(retryMessage);
                }

                // Update retry message
                retryMessage.textContent = `接続エラーが発生しました。再試行中... (${currentRetry + 2}/${maxRetries})`;
            }

            // Wait a bit before retrying (exponential backoff)
            const delay = Math.min(1000 * Math.pow(2, currentRetry), 10000);
            setTimeout(() => {
                uploadWithRetry(url, formData, maxRetries, currentRetry + 1);
            }, delay);
        } else {
            // Hide loading spinner
            document.getElementById('loading').classList.add('d-none');

            // Show error
            showError('ネットワークエラーが発生しました。接続を確認してから再度お試しください。');

            // Re-enable buttons
            document.getElementById('retake-photo').disabled = false;
            document.getElementById('upload-photo').disabled = false;
        }
    });
}

/**
 * Show results
 */
function showResults(counts) {
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    
    if (!resultContainer || !resultContent) {
        console.error('Result container elements not found');
        return;
    }

    // Clear previous results
    resultContent.innerHTML = '';
    
    // Create result HTML
    let html = '<h5>集計結果</h5>';
    
    // Get quadrant texts from the current page
    const quadrantTexts = {
        'UL': document.getElementById('quadrant-ul-text')?.textContent || '左上',
        'UR': document.getElementById('quadrant-ur-text')?.textContent || '右上',
        'LL': document.getElementById('quadrant-ll-text')?.textContent || '左下',
        'LR': document.getElementById('quadrant-lr-text')?.textContent || '右下'
    };
    
    // Get color texts
    const colorTexts = {
        'red': document.getElementById('color-red-text')?.textContent || '赤',
        'green': document.getElementById('color-green-text')?.textContent || '緑',
        'blue': document.getElementById('color-blue-text')?.textContent || '青',
        'yellow': document.getElementById('color-yellow-text')?.textContent || '黄'
    };

    // Create table
    html += '<table class="table table-bordered">';
    html += '<thead><tr><th>位置</th><th>回答</th><th>数</th></tr></thead>';
    html += '<tbody>';
    
    // Add data rows
    for (const quadrant in counts) {
        for (const color in counts[quadrant]) {
            const count = counts[quadrant][color];
            html += `<tr>
                <td>${quadrantTexts[quadrant]}</td>
                <td>${colorTexts[color]}</td>
                <td>${count}</td>
            </tr>`;
        }
    }

    html += '</tbody></table>';

    // Set result HTML
    resultContent.innerHTML = html;

    // Show result container
    resultContainer.classList.remove('d-none');

    // 開催日入力欄をロック
    const dateInput = document.getElementById('event-date');
    if (dateInput) dateInput.disabled = true;
}

/**
 * Convert data URL to Blob
 */
function dataURLtoBlob(dataURL) {
    // Split data URL into parts
    const parts = dataURL.split(';base64,');
    const contentType = parts[0].split(':')[1];
    const raw = window.atob(parts[1]);
    const rawLength = raw.length;
    const uInt8Array = new Uint8Array(rawLength);
    
    // Convert to Uint8Array
    for (let i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i);
    }
    
    // Create Blob
    return new Blob([uInt8Array], { type: contentType });
}

/**
 * Stop camera stream
 */
function stopCamera() {
    if (stream) {
        const tracks = stream.getTracks();
        
        tracks.forEach(function(track) {
            track.stop();
        });
        
        stream = null;
    }
}

/**
 * Resize image to reduce file size
 */
function resizeImage(dataURL, maxWidth, maxHeight, callback) {
    // Create an image to get the original dimensions
    const img = new Image();
    img.onload = function() {
        // Calculate new dimensions while maintaining aspect ratio
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth) {
            height = Math.round(height * (maxWidth / width));
            width = maxWidth;
        }
        
        if (height > maxHeight) {
            width = Math.round(width * (maxHeight / height));
            height = maxHeight;
        }
        
        // Create a canvas for resizing
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        
        // Draw the resized image
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        // Get the resized data URL with reduced quality
        const resizedDataURL = canvas.toDataURL('image/jpeg', 0.7);
        
        // Call the callback with the resized image
        callback(resizedDataURL);
    };
    
    // Set the source of the image
    img.src = dataURL;
}

/**
 * Clean up when page is unloaded
 */
window.addEventListener('beforeunload', function() {
    stopCamera();
});

/**
 * 開催日入力欄に今日の日付をデフォルト設定
 */
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('event-date');
    if (dateInput) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${yyyy}-${mm}-${dd}`;
    }
});
