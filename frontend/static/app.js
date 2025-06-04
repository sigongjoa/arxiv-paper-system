class ArxivToShortsWeb {
    constructor() {
        this.currentTab = 'HomeTab';
        this.setupEventListeners();
        this.loadRecentPapers();
        this.setupLogStream();
        this.loadVideos();
        this.initializePublishTab();
    }

    setupEventListeners() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        document.getElementById('ProcessButton').addEventListener('click', () => {
            this.processPaper();
        });

        document.getElementById('SaveSettingsButton').addEventListener('click', () => {
            this.saveSettings();
        });
        
        document.getElementById('ClearLogButton').addEventListener('click', () => {
            this.clearLog();
        });
        
        document.getElementById('RefreshVideosButton').addEventListener('click', () => {
            this.loadVideos();
        });
        
        document.getElementById('VideoSelect').addEventListener('change', (e) => {
            this.selectVideo(e.target.value);
        });
    }

    initializePublishTab() {
        // Video selection in publish tab
        document.getElementById('RefreshPublishVideos').addEventListener('click', () => {
            this.loadPublishVideos();
        });
        
        document.getElementById('PublishVideoSelect').addEventListener('change', (e) => {
            this.selectPublishVideo(e.target.value);
        });

        // Character counters
        this.setupCharacterCounters();

        // Schedule toggle
        document.querySelectorAll('input[name="publishSchedule"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.toggleScheduleOptions();
            });
        });

        // Publish button
        document.getElementById('PublishButton').addEventListener('click', () => {
            this.publishVideo();
        });

        // Save draft button
        document.getElementById('SaveDraftButton').addEventListener('click', () => {
            this.saveDraft();
        });

        // Clear history
        document.getElementById('ClearHistoryButton').addEventListener('click', () => {
            this.clearUploadHistory();
        });

        // YouTube authentication
        document.getElementById('YoutubeLoginButton').addEventListener('click', () => {
            this.loginToYoutube();
        });

        // Load videos for publish tab
        this.loadPublishVideos();
        
        // Check YouTube auth status
        this.checkYoutubeAuth();
        
        // Set default datetime
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById('ScheduledTime').value = now.toISOString().slice(0, 16);
    }

    setupCharacterCounters() {
        const titleInput = document.getElementById('VideoTitle');
        const descInput = document.getElementById('VideoDescription');

        titleInput.addEventListener('input', () => {
            this.updateCharCount(titleInput, 100);
        });

        descInput.addEventListener('input', () => {
            this.updateCharCount(descInput, 5000);
        });
    }

    updateCharCount(element, maxLength) {
        const currentLength = element.value.length;
        const counter = element.parentElement.querySelector('.char-count');
        counter.textContent = `${currentLength}/${maxLength}`;
        
        if (currentLength > maxLength * 0.9) {
            counter.style.color = '#F44336';
        } else if (currentLength > maxLength * 0.8) {
            counter.style.color = '#FF9800';
        } else {
            counter.style.color = '#888';
        }
    }

    toggleScheduleOptions() {
        const scheduleDateTime = document.getElementById('ScheduleDateTime');
        const publishNow = document.querySelector('input[name="publishSchedule"][value="now"]').checked;
        
        if (publishNow) {
            scheduleDateTime.style.display = 'none';
        } else {
            scheduleDateTime.style.display = 'block';
        }
    }

    async loadPublishVideos() {
        try {
            const response = await fetch('/api/videos');
            const result = await response.json();
            
            const videoSelect = document.getElementById('PublishVideoSelect');
            videoSelect.innerHTML = '<option value="">Choose a video to upload...</option>';
            
            if (result.videos && result.videos.length > 0) {
                result.videos.forEach(video => {
                    const option = document.createElement('option');
                    option.value = video.url;
                    option.textContent = video.filename;
                    option.dataset.filename = video.filename;
                    option.dataset.path = video.path;
                    videoSelect.appendChild(option);
                });
            } else {
                videoSelect.innerHTML = '<option value="">No videos available</option>';
            }
        } catch (error) {
            console.error('Failed to load videos for publish:', error);
        }
    }

    selectPublishVideo(videoUrl) {
        const preview = document.getElementById('SelectedVideoPreview');
        const player = document.getElementById('PreviewPlayer');
        
        if (videoUrl) {
            player.src = videoUrl;
            preview.style.display = 'block';
            
            // Auto-populate title if empty
            const titleInput = document.getElementById('VideoTitle');
            if (!titleInput.value.trim()) {
                const select = document.getElementById('PublishVideoSelect');
                const filename = select.options[select.selectedIndex].dataset.filename;
                const baseName = filename.replace(/\.[^/.]+$/, "").replace(/_/g, " ");
                titleInput.value = `${baseName} - Research Summary #shorts`;
                this.updateCharCount(titleInput, 100);
            }
        } else {
            preview.style.display = 'none';
        }
    }

    validatePublishForm() {
        const videoSelect = document.getElementById('PublishVideoSelect');
        const title = document.getElementById('VideoTitle').value.trim();
        const platforms = this.getSelectedPlatforms();
        
        if (!videoSelect.value) {
            this.showError('Please select a video to upload');
            return false;
        }
        
        if (!title) {
            this.showError('Please enter a video title');
            return false;
        }
        
        if (platforms.length === 0) {
            this.showError('Please select at least one platform');
            return false;
        }
        
        // Check YouTube authentication
        if (platforms.includes('youtube')) {
            const youtubeStatus = document.getElementById('YoutubeStatusIcon');
            if (!youtubeStatus.classList.contains('connected')) {
                this.showError('Please connect to YouTube first');
                return false;
            }
        }
        
        return true;
    }

    getSelectedPlatforms() {
        const platforms = [];
        if (document.getElementById('YoutubeCheck').checked) platforms.push('youtube');
        if (document.getElementById('InstagramCheck').checked) platforms.push('instagram');
        if (document.getElementById('TiktokCheck').checked) platforms.push('tiktok');
        return platforms;
    }

    async publishVideo() {
        if (!this.validatePublishForm()) return;

        const publishButton = document.getElementById('PublishButton');
        const originalText = publishButton.textContent;
        publishButton.textContent = '🔄 Publishing...';
        publishButton.disabled = true;

        try {
            const publishData = this.getPublishData();
            const response = await fetch('/api/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(publishData)
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showSuccess('Upload started successfully!');
                this.addHistoryItem(publishData, 'processing');
                this.showUploadProgress(publishData.platforms);
                
                // Monitor upload progress
                this.monitorUploadProgress(result.upload_id);
            } else {
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Publish error:', error);
            this.showError('Upload failed: ' + error.message);
        } finally {
            publishButton.textContent = originalText;
            publishButton.disabled = false;
        }
    }

    getPublishData() {
        const videoSelect = document.getElementById('PublishVideoSelect');
        const selectedOption = videoSelect.options[videoSelect.selectedIndex];
        
        return {
            video_path: selectedOption.dataset.path,
            video_url: videoSelect.value,
            title: document.getElementById('VideoTitle').value.trim(),
            description: document.getElementById('VideoDescription').value.trim(),
            tags: document.getElementById('VideoTags').value.trim(),
            category: document.getElementById('VideoCategory').value,
            privacy: document.getElementById('VideoPrivacy').value,
            platforms: this.getSelectedPlatforms(),
            schedule: document.querySelector('input[name="publishSchedule"]:checked').value,
            scheduled_time: document.getElementById('ScheduledTime').value
        };
    }

    showUploadProgress(platforms) {
        const progressSection = document.querySelector('.UploadProgressSection');
        const progressContainer = document.querySelector('.upload-progress');
        
        progressSection.style.display = 'block';
        progressContainer.innerHTML = '';
        
        platforms.forEach(platform => {
            const progressItem = document.createElement('div');
            progressItem.className = 'progress-item';
            progressItem.innerHTML = `
                <span class="platform-name">${platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                <div class="progress-bar">
                    <div class="progress-fill ${platform}-progress" style="width: 0%"></div>
                </div>
                <span class="progress-status">Starting...</span>
            `;
            progressContainer.appendChild(progressItem);
        });
    }

    async monitorUploadProgress(uploadId) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/upload/status/${uploadId}`);
                const status = await response.json();
                
                this.updateUploadProgress(status);
                
                if (status.completed) {
                    clearInterval(interval);
                    this.handleUploadComplete(status);
                }
            } catch (error) {
                console.error('Progress monitoring error:', error);
                clearInterval(interval);
            }
        }, 2000);
    }

    updateUploadProgress(status) {
        Object.keys(status.platforms).forEach(platform => {
            const platformStatus = status.platforms[platform];
            const progressFill = document.querySelector(`.${platform}-progress`);
            const statusSpan = document.querySelector(`.progress-item:has(.${platform}-progress) .progress-status`);
            
            if (progressFill) {
                progressFill.style.width = `${platformStatus.progress}%`;
            }
            
            if (statusSpan) {
                statusSpan.textContent = platformStatus.status;
            }
        });
    }

    handleUploadComplete(status) {
        const platforms = Object.keys(status.platforms);
        const successCount = platforms.filter(p => status.platforms[p].success).length;
        
        if (successCount === platforms.length) {
            this.showSuccess(`Upload completed successfully to all ${platforms.length} platform(s)!`);
        } else if (successCount > 0) {
            this.showWarning(`Upload completed to ${successCount}/${platforms.length} platforms`);
        } else {
            this.showError('Upload failed for all platforms');
        }
        
        // Update history
        this.updateHistoryItem(status);
        
        // Hide progress after 5 seconds
        setTimeout(() => {
            document.querySelector('.UploadProgressSection').style.display = 'none';
        }, 5000);
    }

    addHistoryItem(publishData, status) {
        const historyContainer = document.getElementById('UploadHistory');
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-info">
                <div class="history-title">${publishData.title}</div>
                <div class="history-meta">
                    <span class="history-date">${new Date().toLocaleString()}</span>
                    <span class="history-platforms">${publishData.platforms.join(', ')}</span>
                </div>
            </div>
            <div class="history-status ${status}">
                ${this.getStatusIcon(status)} ${status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
        `;
        
        // Remove sample item if exists
        const sampleItem = historyContainer.querySelector('.sample');
        if (sampleItem) {
            sampleItem.remove();
        }
        
        historyContainer.insertBefore(historyItem, historyContainer.firstChild);
    }

    updateHistoryItem(status) {
        const firstItem = document.querySelector('#UploadHistory .history-item:first-child');
        if (firstItem) {
            const statusEl = firstItem.querySelector('.history-status');
            const platforms = Object.keys(status.platforms);
            const successCount = platforms.filter(p => status.platforms[p].success).length;
            
            if (successCount === platforms.length) {
                statusEl.className = 'history-status success';
                statusEl.innerHTML = '✅ Success';
            } else if (successCount > 0) {
                statusEl.className = 'history-status error';
                statusEl.innerHTML = `⚠️ Partial (${successCount}/${platforms.length})`;
            } else {
                statusEl.className = 'history-status error';
                statusEl.innerHTML = '❌ Failed';
            }
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'processing': return '🔄';
            default: return '⏳';
        }
    }

    saveDraft() {
        const draftData = this.getPublishData();
        localStorage.setItem('publish_draft', JSON.stringify(draftData));
        this.showSuccess('Draft saved successfully!');
    }

    loadDraft() {
        const draft = localStorage.getItem('publish_draft');
        if (draft) {
            const data = JSON.parse(draft);
            
            // Populate form fields
            document.getElementById('VideoTitle').value = data.title || '';
            document.getElementById('VideoDescription').value = data.description || '';
            document.getElementById('VideoTags').value = data.tags || '';
            document.getElementById('VideoCategory').value = data.category || '27';
            document.getElementById('VideoPrivacy').value = data.privacy || 'public';
            
            // Update character counters
            this.updateCharCount(document.getElementById('VideoTitle'), 100);
            this.updateCharCount(document.getElementById('VideoDescription'), 5000);
            
            this.showSuccess('Draft loaded successfully!');
        }
    }

    clearUploadHistory() {
        if (confirm('Are you sure you want to clear the upload history?')) {
            const historyContainer = document.getElementById('UploadHistory');
            historyContainer.innerHTML = `
                <div class="history-item sample">
                    <div class="history-info">
                        <div class="history-title">No upload history</div>
                        <div class="history-meta">
                            <span class="history-date">-</span>
                            <span class="history-platforms">-</span>
                        </div>
                    </div>
                    <div class="history-status">-</div>
                </div>
            `;
            this.showSuccess('Upload history cleared');
        }
    }

    async checkYoutubeAuth() {
        try {
            const response = await fetch('/api/youtube/status');
            const result = await response.json();
            this.updateYoutubeAuthUI(result.authenticated);
        } catch (error) {
            console.error('YouTube auth check failed:', error);
            this.updateYoutubeAuthUI(false);
        }
    }

    updateYoutubeAuthUI(isAuthenticated) {
        const loginButton = document.getElementById('YoutubeLoginButton');
        const statusIcon = document.getElementById('YoutubeStatusIcon');
        const checkbox = document.getElementById('YoutubeCheck');
        
        if (isAuthenticated) {
            loginButton.textContent = '✓ YouTube Connected';
            loginButton.className = 'youtube-login-btn connected';
            loginButton.disabled = true;
            statusIcon.textContent = '✓';
            statusIcon.className = 'platform-status connected';
            checkbox.disabled = false;
        } else {
            loginButton.textContent = '🔗 Connect YouTube';
            loginButton.className = 'youtube-login-btn';
            loginButton.disabled = false;
            statusIcon.textContent = '⚠';
            statusIcon.className = 'platform-status';
            checkbox.disabled = true;
            checkbox.checked = false;
        }
    }

    async loginToYoutube() {
        try {
            const response = await fetch('/api/youtube/auth');
            const result = await response.json();
            
            if (result.auth_url) {
                const popup = window.open(
                    result.auth_url,
                    'youtube_auth',
                    'width=500,height=600,scrollbars=yes,resizable=yes'
                );
                
                // Check if popup is closed
                const checkClosed = setInterval(() => {
                    if (popup.closed) {
                        clearInterval(checkClosed);
                        // Recheck auth status
                        setTimeout(() => this.checkYoutubeAuth(), 1000);
                    }
                }, 1000);
            } else {
                this.showError('Failed to get YouTube authentication URL');
            }
        } catch (error) {
            console.error('YouTube login error:', error);
            this.showError('YouTube login failed: ' + error.message);
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            max-width: 400px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        `;
        
        switch (type) {
            case 'success':
                notification.style.background = '#4CAF50';
                break;
            case 'error':
                notification.style.background = '#F44336';
                break;
            case 'warning':
                notification.style.background = '#FF9800';
                break;
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    switchTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
        document.getElementById(tabId).classList.add('active');
        this.currentTab = tabId;
        
        // Load videos when switching to preview or publish tab
        if (tabId === 'PreviewTab') {
            this.loadVideos();
        } else if (tabId === 'PublishTab') {
            this.loadPublishVideos();
        }
    }

    async processPaper() {
        const arxivId = document.getElementById('ArxivIdInput').value.trim();
        if (!arxivId) {
            this.setStatus('Please enter arXiv ID', 'error');
            return;
        }

        this.setStatus('Processing...', 'processing');
        this.switchTab('ProcessTab');
        this.startProgressMonitoring(arxivId);

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ arxiv_id: arxivId })
            });

            const result = await response.json();
            this.handleProcessingComplete(result);
        } catch (error) {
            console.error('Processing error:', error);
            this.setStatus('Processing failed', 'error');
            this.updateStepStatus('error', 'error');
        }
    }

    startProgressMonitoring(arxivId) {
        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/pipeline/status/${arxivId}`);
                const status = await response.json();
                this.updateProgress(status);
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 2000);
    }

    updateProgress(status) {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        
        progressFill.style.width = `${status.progress}%`;
        progressText.textContent = `${status.progress}%`;

        status.steps.forEach(step => {
            this.updateStepStatus(step.name, step.status);
        });
    }

    updateStepStatus(stepName, status) {
        const stepElement = document.querySelector(`[data-step="${stepName}"]`);
        if (!stepElement) return;

        stepElement.className = `step-item ${status}`;
        const statusElement = stepElement.querySelector('.step-status');
        statusElement.textContent = status;
        statusElement.className = `step-status ${status}`;
    }

    handleProcessingComplete(result) {
        clearInterval(this.progressInterval);
        this.setStatus('Processing completed', 'ready');
        
        // 비디오 URL 가져오기
        const arxivId = document.getElementById('ArxivIdInput').value.trim();
        this.loadVideoFromAPI(arxivId);
        
        // 프리뷰 탭으로 이동
        this.switchTab('PreviewTab');
    }
    
    async loadVideoFromAPI(arxivId) {
        try {
            console.log(`비디오 로드 시도: ${arxivId}`);
            
            // 먼저 생성된 파일 목록 확인
            const debugResponse = await fetch('/api/debug/files');
            if (debugResponse.ok) {
                const debugData = await debugResponse.json();
                console.log('생성된 파일 목록:', debugData);
            }
            
            const response = await fetch(`/api/video/${arxivId}`);
            const result = await response.json();
            
            if (response.ok) {
                console.log('비디오 찾음:', result);
                this.loadVideoPreview(result.video_url);
            } else {
                console.error('비디오 없음:', result);
                this.showVideoError(`비디오 파일을 찾을 수 없습니다.<br>
                                    찾는 ID: ${result.searched_for || arxivId}<br>
                                    사용 가능한 파일: ${(result.available_files || []).join(', ')}`);
            }
        } catch (error) {
            console.error('비디오 로드 에러:', error);
            this.showVideoError('비디오 로드 중 오류가 발생했습니다.');
        }
    }
    
    loadVideoPreview(videoUrl) {
        const videoElement = document.querySelector('#VideoPreview video');
        if (videoElement && videoUrl) {
            videoElement.src = videoUrl;
            videoElement.load(); // 비디오 다시 로드
            console.log('비디오 로드됨:', videoUrl);
        }
    }
    
    showVideoError(message) {
        const videoPreview = document.getElementById('VideoPreview');
        videoPreview.innerHTML = `
            <div class="video-error">
                <p>🚨 비디오 로드 오류</p>
                <div>${message}</div>
                <p><small>비디오 파일이 생성되었지만 로드할 수 없습니다.</small></p>
                <p><small>파일 위치: output/videos/ 디렉토리</small></p>
                <button onclick="app.loadVideoFromAPI(document.getElementById('ArxivIdInput').value)" class="primary-btn">다시 시도</button>
            </div>
        `;
    }

    setStatus(message, type = 'ready') {
        const indicator = document.getElementById('StatusIndicator');
        const statusBar = document.getElementById('StatusBar');
        
        indicator.className = `status-${type}`;
        indicator.textContent = `● ${message}`;
        statusBar.textContent = message;
    }

    updateProcessingStatus(result) {
        const stepsContainer = document.getElementById('ProcessingSteps');
        const progressFill = document.querySelector('.progress-fill');
        
        // Update progress and steps based on result
        progressFill.style.width = '25%';
        
        stepsContainer.innerHTML = `
            <div class="step-item active">Processing arXiv paper: ${result.arxiv_id}</div>
            <div class="step-item">Extracting content...</div>
            <div class="step-item">Generating script...</div>
            <div class="step-item">Creating video...</div>
        `;
    }

    saveSettings() {
        const settings = {
            openai_key: document.getElementById('OpenaiApiKey').value,
            anthropic_key: document.getElementById('AnthropicApiKey').value,
            tts_voice: document.getElementById('TtsVoiceSelect').value,
            script_style: document.getElementById('ScriptStyleSelect').value,
            visual_theme: document.getElementById('VisualThemeSelect').value,
            video_duration: document.getElementById('VideoDurationSelect').value
        };
        
        Object.keys(settings).forEach(key => {
            localStorage.setItem(key, settings[key]);
        });
        
        // 서버에 설정 저장
        fetch('/api/pipeline/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        this.setStatus('Settings saved');
    }

    loadRecentPapers() {
        const recentPapers = JSON.parse(localStorage.getItem('recent_papers') || '[]');
        const paperList = document.querySelector('.paper-list');
        
        paperList.innerHTML = recentPapers.map(paper => `
            <div class="paper-item" onclick="app.loadPaper('${paper.id}')">
                <strong>${paper.id}</strong> - ${paper.title || 'Processing...'}
            </div>
        `).join('');
    }

    loadPaper(arxivId) {
        document.getElementById('ArxivIdInput').value = '2301.07041';  // 유효한 arXiv ID로 기본값 설정
        this.switchTab('HomeTab');
    }
    
    setupLogStream() {
        this.logContainer = document.getElementById('ProcessLog');
        
        // EventSource for real-time logs
        this.eventSource = new EventSource('/api/logs/stream');
        this.eventSource.onmessage = (event) => {
            const logData = JSON.parse(event.data);
            this.addLogEntry(logData);
        };
        
        this.eventSource.onerror = (error) => {
            console.error('Log stream error:', error);
        };
        
        // Load existing logs
        this.loadExistingLogs();
    }
    
    async loadExistingLogs() {
        try {
            const response = await fetch('/api/logs');
            const result = await response.json();
            
            result.logs.forEach(log => {
                this.addLogEntry(log);
            });
        } catch (error) {
            console.error('Failed to load existing logs:', error);
        }
    }
    
    addLogEntry(logData) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${logData.level}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">[${logData.timestamp}]</span>
            <span class="log-message">${logData.message}</span>
        `;
        
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }
    
    clearLog() {
        this.logContainer.innerHTML = '';
    }
    
    async loadVideos() {
        try {
            const response = await fetch('/api/videos');
            const result = await response.json();
            
            const videoSelect = document.getElementById('VideoSelect');
            videoSelect.innerHTML = '<option value="">Select a video...</option>';
            
            if (result.videos && result.videos.length > 0) {
                result.videos.forEach(video => {
                    const option = document.createElement('option');
                    option.value = video.url;
                    option.textContent = video.filename;
                    option.dataset.filename = video.filename;
                    option.dataset.size = video.size;
                    option.dataset.created = video.created;
                    videoSelect.appendChild(option);
                });
            } else {
                videoSelect.innerHTML = '<option value="">No videos available</option>';
            }
        } catch (error) {
            console.error('Failed to load videos:', error);
            const videoSelect = document.getElementById('VideoSelect');
            videoSelect.innerHTML = '<option value="">Error loading videos</option>';
        }
    }
    
    selectVideo(videoUrl) {
        const videoPlayer = document.getElementById('VideoPlayer');
        const noVideoMessage = document.getElementById('NoVideoMessage');
        const videoInfo = document.getElementById('VideoInfo');
        const videoSelect = document.getElementById('VideoSelect');
        
        if (videoUrl) {
            const selectedOption = videoSelect.options[videoSelect.selectedIndex];
            
            // Show video player
            videoPlayer.src = videoUrl;
            videoPlayer.style.display = 'block';
            noVideoMessage.style.display = 'none';
            
            // Show video info
            videoInfo.style.display = 'block';
            document.getElementById('VideoFilename').textContent = selectedOption.dataset.filename;
            document.getElementById('VideoSize').textContent = this.formatFileSize(selectedOption.dataset.size);
            document.getElementById('VideoCreated').textContent = new Date(selectedOption.dataset.created * 1000).toLocaleString();
        } else {
            // Hide video player
            videoPlayer.style.display = 'none';
            noVideoMessage.style.display = 'block';
            videoInfo.style.display = 'none';
        }
    }
    
    formatFileSize(bytes) {
        const mb = bytes / (1024 * 1024);
        return `${mb.toFixed(2)} MB`;
    }
}

const app = new ArxivToShortsWeb();
