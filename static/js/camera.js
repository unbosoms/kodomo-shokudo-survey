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
            facingMode: 'environment',  // Use back camera if available
            width: { ideal: 1280 },
            height: { ideal: 720 }
        } 
    })
    .then(function(s) {
        stream = s;
        videoElement.srcObject = stream;
        
        // Play video
        videoElement.play();
        
        // Wait for video to be ready
        videoElement.onloadedmetadata = function() {
            // Show take photo button
            document.getElementById('take-photo').classList.remove('d-none');
            
            // Load guide overlay
            loadGuideOverlay();
            
            // Set up take photo button
            document.getElementById('take-photo').addEventListener('click', takePhoto);
            
            // Set up retake photo button
            document.getElementById('retake-photo').addEventListener('click', retakePhoto);
            
            // Set up upload photo button
            document.getElementById('upload-photo').addEventListener('click', uploadPhoto);
        };
    })
    .catch(function(error) {
        showError(`カメラへのアクセスに失敗しました: ${error.message}`);
    });
}

/**
 * Load guide overlay
 */
function loadGuideOverlay() {
    // Get video dimensions
    const width = videoElement.videoWidth;
    const height = videoElement.videoHeight;
    
    if (!width || !height) {
        // Video not ready yet, try again later
        setTimeout(loadGuideOverlay, 100);
        return;
    }
    
    // Request guide overlay from server
    fetch(`/api/guide-overlay?width=${width}&height=${height}`)
        .then(response => response.blob())
        .then(blob => {
            // Create object URL
            const url = URL.createObjectURL(blob);
            
            // Set as guide overlay source
            guideOverlayElement.src = url;
            guideOverlayElement.style.display = 'block';
        })
        .catch(error => {
            console.error('Failed to load guide overlay:', error);
            // Draw guide lines directly on canvas as fallback
            drawGuideLines(width, height);
        });
}

/**
 * Draw guide lines directly on canvas (fallback)
 */
function drawGuideLines(width, height) {
    // Create a canvas for the overlay
    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.width = width;
    overlayCanvas.height = height;
    const ctx = overlayCanvas.getContext('2d');
    
    // Draw horizontal line
    ctx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
    
    // Draw vertical line
    ctx.beginPath();
    ctx.moveTo(width / 2, 0);
    ctx.lineTo(width / 2, height);
    ctx.stroke();
    
    // Add labels
    ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
    ctx.font = '20px Arial';
    ctx.fillText('左上', 10, height / 2 - 10);
    ctx.fillText('右上', width / 2 + 10, height / 2 - 10);
    ctx.fillText('左下', 10, height - 10);
    ctx.fillText('右下', width / 2 + 10, height - 10);
    
    // Convert to data URL
    const dataURL = overlayCanvas.toDataURL('image/png');
    
    // Set as guide overlay source
    guideOverlayElement.src = dataURL;
    guideOverlayElement.style.display = 'block';
}

/**
 * Take photo
 */
function takePhoto() {
    if (!videoElement || !canvasElement) {
        showError('カメラが初期化されていません');
        return;
    }
    
    // Get video dimensions
    const width = videoElement.videoWidth;
    const height = videoElement.videoHeight;
    
    // Set canvas dimensions
    canvasElement.width = width;
    canvasElement.height = height;
    
    // Draw video frame to canvas
    const context = canvasElement.getContext('2d');
    context.drawImage(videoElement, 0, 0, width, height);
    
    // Get image data
    photoData = canvasElement.toDataURL('image/jpeg', 0.9);
    
    // Show photo preview
    videoElement.style.display = 'none';
    canvasElement.style.display = 'block';
    guideOverlayElement.style.display = 'none';
    
    // Update buttons
    document.getElementById('take-photo').classList.add('d-none');
    document.getElementById('retake-photo').classList.remove('d-none');
    document.getElementById('upload-photo').classList.remove('d-none');
}

/**
 * Retake photo
 */
function retakePhoto() {
    // Clear photo data
    photoData = null;
    
    // Show video preview
    videoElement.style.display = 'block';
    canvasElement.style.display = 'none';
    guideOverlayElement.style.display = 'block';
    
    // Update buttons
    document.getElementById('take-photo').classList.remove('d-none');
    document.getElementById('retake-photo').classList.add('d-none');
    document.getElementById('upload-photo').classList.add('d-none');
}

/**
 * Upload photo
 */
function uploadPhoto() {
    if (!photoData) {
        showError('写真が撮影されていません');
        return;
    }
    
    // Show loading spinner
    document.getElementById('loading').classList.remove('d-none');
    
    // Disable buttons
    document.getElementById('retake-photo').disabled = true;
    document.getElementById('upload-photo').disabled = true;
    
    // Resize image before uploading to reduce file size
    resizeImage(photoData, 1280, 720, function(resizedImageData) {
        console.info('Image resized for upload. Original size vs. New size (bytes):', 
                    photoData.length, resizedImageData.length);
        
        // Create form data
        const formData = new FormData();
        
        // Convert data URL to blob
        const blob = dataURLtoBlob(resizedImageData);
        
        // Add to form data
        formData.append('image', blob, 'photo.jpg');
        formData.append('userId', document.getElementById('userId').value);
        formData.append('shokudoId', document.getElementById('shokudo-name').dataset.shokudoId || '');
        
        // Upload to server with timeout and retry logic
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
        
        // Check if response is ok
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        return response.json();
    })
    .then(data => {
        // Hide loading spinner
        document.getElementById('loading').classList.add('d-none');
        
        if (data.success) {
            // Show results
            showResults(data.counts);
            
            // Close LIFF browser after 5 seconds if in LINE
            if (liff.isInClient()) {
                setTimeout(() => {
                    liff.closeWindow();
                }, 5000);
            }
        } else {
            showError(data.error || 'アップロードに失敗しました');
            
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
            showError(`アップロードエラー: ${error.message}。ネットワーク接続を確認してください。`);
            
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
    // Get result container
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    
    // Clear previous results
    resultContent.innerHTML = '';
    
    // Create result HTML
    let html = '<h5>集計結果</h5>';
    
    // Get quadrant names and answers
    const quadrantNames = {
        'UL': '左上',
        'UR': '右上',
        'LL': '左下',
        'LR': '右下'
    };
    
    const quadrantAnswers = {
        'UL': document.getElementById('quadrant-ul').textContent,
        'UR': document.getElementById('quadrant-ur').textContent,
        'LL': document.getElementById('quadrant-ll').textContent,
        'LR': document.getElementById('quadrant-lr').textContent
    };
    
    // Get color names and attributes
    const colorNames = {
        'red': '赤',
        'green': '緑',
        'blue': '青',
        'yellow': '黄'
    };
    
    const colorAttributes = {
        'red': document.getElementById('color-red').textContent,
        'green': document.getElementById('color-green').textContent,
        'blue': document.getElementById('color-blue').textContent,
        'yellow': document.getElementById('color-yellow').textContent
    };
    
    // Create table
    html += '<table class="table table-bordered">';
    html += '<thead><tr><th>回答</th><th>属性</th><th>数</th></tr></thead>';
    html += '<tbody>';
    
    // Add rows for each quadrant and color
    for (const quadrant in counts) {
        const quadrantName = quadrantNames[quadrant] || quadrant;
        const answer = quadrantAnswers[quadrant] || '';
        
        for (const color in counts[quadrant]) {
            const count = counts[quadrant][color];
            
            // Skip if count is 0
            if (count === 0) continue;
            
            const colorName = colorNames[color] || color;
            const attribute = colorAttributes[color] || '';
            
            html += `<tr>
                <td>${answer} (${quadrantName})</td>
                <td>${attribute} (${colorName})</td>
                <td>${count}</td>
            </tr>`;
        }
    }
    
    html += '</tbody></table>';
    
    // Set result HTML
    resultContent.innerHTML = html;
    
    // Show result container
    resultContainer.classList.remove('d-none');
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
