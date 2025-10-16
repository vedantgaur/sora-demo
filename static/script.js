/**
 * Frontend JavaScript for Sora Director
 * Handles UI interactions and API calls
 */

// Global state
let currentPromptHash = null;
let currentPrompt = null;
let selectedVideoPath = null;
let currentAssetPath = null;
let currentFrameCount = 3;
let viewer3D = null;
let useRealAPI = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
    
    // Initialize 3D viewer
    viewer3D = new Viewer3D('viewer3D');
});

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Mode toggle
    document.getElementById('modeToggle').addEventListener('change', handleModeToggle);
    
    // Generate button
    document.getElementById('generateBtn').addEventListener('click', handleGenerate);
    
    // Initialize mock mode UI
    const promptInput = document.getElementById('promptInput');
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const videoSourceSelector = document.getElementById('videoSourceSelector');
    
    if (!useRealAPI) {
        promptInput.disabled = true;
        promptInput.style.opacity = '0.5';
        promptInput.value = 'A ball moving left to right';
        btnText.textContent = 'Show Video';
        videoSourceSelector.style.display = 'block';  // Show video selector in mock mode
    } else {
        videoSourceSelector.style.display = 'none';  // Hide video selector in real mode
    }
    
    // Run agent button
    document.getElementById('runAgentBtn').addEventListener('click', handleRunAgent);
    
    // Regenerate button
    document.getElementById('regenerateBtn').addEventListener('click', handleRegenerate);
    
    // Video source selector (update prompt when changing)
    document.querySelectorAll('input[name="videoSource"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (!useRealAPI) {
                const promptInput = document.getElementById('promptInput');
                if (e.target.value === 'sora') {
                    promptInput.value = 'A man walking through trees';
                } else {
                    promptInput.value = 'A ball moving left to right';
                }
            }
        });
    });
    
    // Enter key in prompt input
    document.getElementById('promptInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            handleGenerate();
        }
    });
}

/**
 * Handle mode toggle between mock and real API
 */
function handleModeToggle(event) {
    useRealAPI = event.target.checked;
    const modeLabel = document.getElementById('modeLabel');
    const promptInput = document.getElementById('promptInput');
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const videoSourceSelector = document.getElementById('videoSourceSelector');
    
    if (useRealAPI) {
        modeLabel.textContent = 'REAL API MODE';
        modeLabel.style.background = 'rgba(76, 175, 80, 0.3)';
        promptInput.disabled = false;
        promptInput.style.opacity = '1';
        btnText.textContent = 'Generate Video';
        videoSourceSelector.style.display = 'none';  // Hide video selector
        
        // Warning for real API
        if (confirm('Warning: Real Sora API mode will make actual API calls.\n\nAre you sure you want to enable this?')) {
            console.log('Real API mode enabled');
        } else {
            event.target.checked = false;
            useRealAPI = false;
            modeLabel.textContent = 'MOCK MODE';
            modeLabel.style.background = '';
            promptInput.disabled = true;
            promptInput.style.opacity = '0.5';
            btnText.textContent = 'Show Video';
            videoSourceSelector.style.display = 'block';  // Show video selector
        }
    } else {
        modeLabel.textContent = 'MOCK MODE';
        modeLabel.style.background = '';
        promptInput.disabled = true;
        promptInput.style.opacity = '0.5';
        btnText.textContent = 'Show Video';
        videoSourceSelector.style.display = 'block';  // Show video selector
    }
}

/**
 * Check API health
 */
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('Health check failed:', error);
        showError('Unable to connect to server. Please check if the backend is running.');
    }
}

/**
 * Generate SHA256 hash of prompt (matches backend implementation)
 */
async function generatePromptHash(prompt) {
    const encoder = new TextEncoder();
    const data = encoder.encode(prompt);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16);  // First 16 characters, like backend
}

/**
 * Poll for generation progress
 */
async function pollProgress(promptHash, interval = 2000) {
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    const progressMessage = document.getElementById('progressMessage');
    
    // Show progress container
    progressContainer.style.display = 'block';
    
    let pollCount = 0;
    const maxPolls = 300; // Max 10 minutes (300 * 2 seconds)
    
    return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
            try {
                pollCount++;
                
                if (pollCount > maxPolls) {
                    clearInterval(pollInterval);
                    reject(new Error('Progress polling timed out'));
                    return;
                }
                
                const response = await fetch(`/api/progress/${promptHash}`);
                
                if (!response.ok) {
                    clearInterval(pollInterval);
                    reject(new Error('Failed to fetch progress'));
                    return;
                }
                
                const progress = await response.json();
                
                // Update UI
                progressBar.style.width = `${progress.progress}%`;
                progressPercent.textContent = `${progress.progress}%`;
                progressStatus.textContent = progress.status === 'queued' ? 'Queued' : 
                                            progress.status === 'in_progress' ? 'Generating' :
                                            progress.status === 'completed' ? 'Complete' : 
                                            progress.status === 'failed' ? 'Failed' : progress.status;
                progressMessage.textContent = progress.message || '';
                
                // Update color based on status
                if (progress.status === 'completed') {
                    progressBar.style.background = 'linear-gradient(90deg, #4ade80, #22c55e)';
                } else if (progress.status === 'failed') {
                    progressBar.style.background = 'linear-gradient(90deg, #f87171, #ef4444)';
                }
                
                // Stop polling if completed or failed
                if (progress.status === 'completed' || progress.status === 'failed') {
                    clearInterval(pollInterval);
                    // Hide progress bar after a delay
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                        progressBar.style.width = '0%';
                        progressPercent.textContent = '0%';
                        progressStatus.textContent = 'Queued...';
                        progressMessage.textContent = '';
                        progressBar.style.background = 'linear-gradient(90deg, #fafafa, #d4d4d8)';
                    }, 2000);
                    resolve(progress);
                }
            } catch (error) {
                console.error('Progress polling error:', error);
                clearInterval(pollInterval);
                reject(error);
            }
        }, interval);
    });
}

/**
 * Handle video generation
 */
async function handleGenerate() {
    const promptInput = document.getElementById('promptInput');
    const generateBtn = document.getElementById('generateBtn');
    
    const prompt = promptInput.value.trim();
    
    // Mock mode: Just show selected video directly
    if (!useRealAPI) {
        setButtonLoading(generateBtn, true);
        hideSection('viewerSection');
        hideSection('agentResultsSection');
        
        try {
            // Get selected video source
            const videoSource = document.querySelector('input[name="videoSource"]:checked')?.value || 'demo';
            
            let videoPath, videoPrompt;
            
            if (videoSource === 'sora') {
                // Use the most recent Sora-generated video
                videoPath = '/data/generations/796b6b5a7803e5aa/take_1.mp4';
                videoPrompt = 'A man walking through trees';
                currentPromptHash = '796b6b5a7803e5aa';
            } else {
                // Use demo video
                videoPath = '/data/samples/demo.mp4';
                videoPrompt = 'A ball moving left to right';
                currentPromptHash = 'sample';
            }
            
            currentPrompt = videoPrompt;
            
            // Add timestamp to bust browser cache
            const timestamp = Date.now();
            displayResults([{
                take_id: currentPromptHash,
                video_path: videoPath,
                video_url: `${videoPath}?t=${timestamp}`,
                rank: 1,
                scores: {
                    overall: 0.95,
                    identity_persistence: 0.95,
                    motion_smoothness: 0.92,
                    path_realism: 0.94,
                    physics_plausibility: 0.93,
                    visual_quality: 0.96,
                    temporal_coherence: 0.91
                }
            }]);
        } catch (error) {
            console.error('Sample video error:', error);
            showError('Failed to load sample video.');
        } finally {
            setButtonLoading(generateBtn, false);
        }
        return;
    }
    
    // Real API mode
    if (!prompt) {
        showError('Please enter a prompt');
        return;
    }
    
    // Update UI
    setButtonLoading(generateBtn, true);
    hideSection('resultsContainer');
    hideSection('viewerSection');
    hideSection('agentResultsSection');
    
    // Show results container to display progress
    showSection('resultsContainer');
    
    // Generate prompt hash (same algorithm as backend)
    const promptHash = await generatePromptHash(prompt);
    
    try {
        // Start progress polling in parallel with generation (only for real API)
        if (useRealAPI) {
            pollProgress(promptHash).catch(err => {
                console.warn('Progress polling ended:', err.message);
            });
        }
        
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                prompt, 
                num_takes: 1,  // Always generate 1 video
                use_real_api: useRealAPI 
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentPromptHash = data.prompt_hash;
            currentPrompt = data.prompt;
            
            // Show warning if real API was requested but fell back to mock
            if (useRealAPI && data.mode === 'MOCK') {
                console.warn('⚠️  Real Sora API unavailable - generated mock video instead');
                showError('Note: Sora API is not available (limited beta access). Using mock video instead.', 'warning');
            }
            
            displayResults(data.takes);
        } else {
            showError(data.error || 'Generation failed');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showError('Failed to generate videos. Please try again.');
    } finally {
        setButtonLoading(generateBtn, false);
    }
}


/**
 * Display generated video results
 */
function displayResults(takes) {
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsGrid = document.getElementById('results');
    
    // Clear previous results
    resultsGrid.innerHTML = '';
    
    // Create video cards
    takes.forEach((take, index) => {
        const card = createVideoCard(take);
        resultsGrid.appendChild(card);
    });
    
    // Show results
    showSection('resultsContainer');
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Create a video card element
 */
function createVideoCard(take) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.takeId = take.take_id;
    
    // Create scores HTML
    const scoresHtml = Object.entries(take.scores)
        .filter(([key]) => key !== 'overall')
        .slice(0, 3)
        .map(([key, value]) => `
            <div class="score-item">
                <span>${formatScoreName(key)}:</span>
                <span>${(value * 100).toFixed(0)}%</span>
            </div>
        `).join('');
    
    card.innerHTML = `
        <video controls loop>
            <source src="${take.video_url}" type="video/mp4">
            Your browser does not support video playback.
        </video>
        <div class="video-card-content">
            <h4>Take ${take.take_id}</h4>
            <div class="scores">
                <div class="score-item">
                    <strong>Overall Score:</strong>
                    <strong>${(take.scores.overall * 100).toFixed(0)}%</strong>
                </div>
                ${scoresHtml}
            </div>
            <div class="frame-slider-container" style="margin: 16px 0;">
                <label for="frameCount-${take.take_id}" style="display: block; margin-bottom: 8px; font-size: 14px; color: #a1a1aa;">
                    Number of frames for GPT-4 Vision: <span id="frameValue-${take.take_id}">2</span>
                </label>
                <input type="range" id="frameCount-${take.take_id}" min="2" max="10" value="2" 
                       style="width: 100%;" 
                       oninput="document.getElementById('frameValue-${take.take_id}').textContent = this.value">
            </div>
            <button class="select-btn" onclick="reconstructVideo('${take.video_path}', '${take.take_id}')">
                Reconstruct 3D World
            </button>
        </div>
    `;
    
    return card;
}

/**
 * Handle video reconstruction directly
 */
async function reconstructVideo(videoPath, takeId) {
    selectedVideoPath = videoPath;
    
    // Find the button that was clicked
    const card = document.querySelector(`[data-take-id="${takeId}"]`);
    const button = card.querySelector('.select-btn');
    
    // Get the frame count from the slider
    const frameCountSlider = document.getElementById(`frameCount-${takeId}`);
    const frameCount = frameCountSlider ? parseInt(frameCountSlider.value) : 3;
    currentFrameCount = frameCount;  // Store for later use
    
    // Show loading state
    const originalText = button.innerHTML;
    button.innerHTML = 'Reconstructing...';
    button.disabled = true;
    
    hideSection('viewerSection');
    hideSection('agentResultsSection');
    
    try {
        const response = await fetch('/api/reconstruct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt_hash: currentPromptHash,
                video_path: videoPath,
                frame_count: frameCount
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentAssetPath = data.asset_path;
            displayWorldViewer(data);
        } else {
            showError(data.error || 'Reconstruction failed');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    } catch (error) {
        console.error('Reconstruction error:', error);
        showError('Failed to reconstruct 3D world. Please try again.');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

/**
 * Display 3D world viewer
 */
function displayWorldViewer(data) {
    const viewerSection = document.getElementById('viewerSection');
    const assetInfo = document.getElementById('assetInfo');
    const placeholder = document.getElementById('viewerPlaceholder');
    const loading = document.getElementById('viewerLoading');
    const loadingSubtext = document.getElementById('loadingSubtext');
    
    assetInfo.textContent = `Asset: ${data.asset_url} (${data.format})`;
    
    // Hide placeholder, show loading
    placeholder.style.display = 'none';
    loading.style.display = 'block';
    
    // Show viewer section
    showSection('viewerSection');
    viewerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Show and setup 3D viewer
    viewer3D.show();
    
    // Generate scene from video using GPT-4 Vision
    setTimeout(async () => {
        try {
            if (selectedVideoPath) {
                // Update loading text
                loadingSubtext.textContent = 'Extracting video frames...';
                
                // Use GPT-4 Vision to analyze the actual video
                await viewer3D.createWorldFromVideo(selectedVideoPath, currentPrompt, currentFrameCount);
            } else {
                viewer3D.createDemoWorld();
            }
            
            // Hide loading indicator
            loading.style.display = 'none';
        } catch (error) {
            console.error('Error generating scene:', error);
            loading.style.display = 'none';
            showError('Failed to generate 3D scene');
        }
    }, 200);
}

/**
 * Handle agent testing
 */
async function handleRunAgent() {
    if (!currentAssetPath) {
        showError('No 3D asset to test');
        return;
    }
    
    const runAgentBtn = document.getElementById('runAgentBtn');
    setButtonLoading(runAgentBtn, true);
    
    hideSection('agentResultsSection');
    
    try {
        const response = await fetch('/api/run_agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                asset_path: currentAssetPath,
                prompt: currentPrompt
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Animate agent in 3D viewer with violations
            if (viewer3D && data.violations) {
                await viewer3D.animateAgent(data.violations);
            }
            
            displayAgentResults(data);
        } else {
            showError(data.error || 'Agent test failed');
        }
    } catch (error) {
        console.error('Agent test error:', error);
        showError('Failed to run agent test. Please try again.');
    } finally {
        setButtonLoading(runAgentBtn, false);
    }
}

/**
 * Display agent test results
 */
function displayAgentResults(data) {
    const agentResultsSection = document.getElementById('agentResultsSection');
    const violationsContainer = document.getElementById('violationsContainer');
    const metricsContainer = document.getElementById('metricsContainer');
    const originalPrompt = document.getElementById('originalPrompt');
    const revisedPrompt = document.getElementById('revisedPrompt');
    const revisionExplanation = document.getElementById('revisionExplanation');
    
    // Display violations
    if (data.violations && data.violations.length > 0) {
        violationsContainer.innerHTML = `
            <div class="violations-header">
                <h3>⚠️ Issues Detected</h3>
                <span class="violation-count">${data.violations.length}</span>
            </div>
            ${data.violations.map(v => `
                <div class="violation-item">
                    <div class="violation-type">${v.type}</div>
                    <div class="violation-description">${v.description}</div>
                    <div class="violation-meta">
                        Severity: ${v.severity} | 
                        Time: ${v.timestamp ? v.timestamp.toFixed(1) + 's' : 'N/A'}
                    </div>
                </div>
            `).join('')}
        `;
    } else {
        violationsContainer.innerHTML = `
            <div class="no-violations">
                ✅ No violations detected! The 3D world passed all tests.
            </div>
        `;
    }
    
    // Display metrics
    if (data.metrics) {
        metricsContainer.innerHTML = `
            <h3>Performance Metrics</h3>
            <div class="metrics-grid">
                ${Object.entries(data.metrics).map(([key, value]) => `
                    <div class="metric-item">
                        <div class="metric-value">${formatMetricValue(value)}</div>
                        <div class="metric-label">${formatScoreName(key)}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Display prompt comparison
    originalPrompt.textContent = currentPrompt;
    revisedPrompt.textContent = data.revised_prompt;
    revisionExplanation.textContent = data.explanation;
    
    // Update current prompt for regeneration
    currentPrompt = data.revised_prompt;
    
    showSection('agentResultsSection');
    agentResultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Handle regeneration with improved prompt
 */
function handleRegenerate() {
    // Update prompt input
    document.getElementById('promptInput').value = currentPrompt;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Trigger generation
    setTimeout(() => {
        handleGenerate();
    }, 500);
}

/**
 * Utility: Set button loading state
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

/**
 * Utility: Show section
 */
function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
    }
}

/**
 * Utility: Hide section
 */
function hideSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'none';
    }
}

/**
 * Utility: Show error message
 */
function showError(message, type = 'error') {
    if (type === 'warning') {
        console.warn(message);
        // Show a less intrusive warning (you could use a toast notification here)
        alert('⚠️ ' + message);
    } else {
        console.error(message);
        alert('❌ Error: ' + message);
    }
}

/**
 * Utility: Format score name for display
 */
function formatScoreName(name) {
    return name
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Utility: Format metric value
 */
function formatMetricValue(value) {
    if (typeof value === 'number') {
        if (value < 1) {
            return (value * 100).toFixed(0) + '%';
        } else {
            return value.toFixed(2);
        }
    }
    return value;
}

