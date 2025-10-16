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
// Always use Sora API for new generations (no mock mode toggle)
let useRealAPI = true;

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
    // Generate button
    document.getElementById('generateBtn').addEventListener('click', handleGenerate);
    
    // Demo button
    document.getElementById('demoBtn').addEventListener('click', handleDemo);
    
    // Run agent button
    document.getElementById('runAgentBtn').addEventListener('click', handleRunAgent);
    
    // Regenerate 3D scene button
    document.getElementById('regenerate3DBtn').addEventListener('click', handleRegenerate3D);
    
    // Regenerate button (for video regeneration)
    if (document.getElementById('regenerateBtn')) {
        document.getElementById('regenerateBtn').addEventListener('click', handleRegenerate);
    }
    
    // Enter key in prompt input
    document.getElementById('promptInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            handleGenerate();
        }
    });
    
    // Cached prompts dropdown
    const cachedPromptsDropdown = document.getElementById('cachedPromptsDropdown');
    if (cachedPromptsDropdown) {
        // Load cached prompts (includes demo videos)
        loadCachedPrompts();
        
        // Handle selection
        cachedPromptsDropdown.addEventListener('change', async (e) => {
            if (e.target.value) {
                const selectedOption = cachedPromptsDropdown.options[cachedPromptsDropdown.selectedIndex];
                const videoPath = selectedOption.dataset.path;
                const promptHash = selectedOption.dataset.hash;
                
                if (videoPath && promptHash) {
                    // This is a cached/demo video - load it directly
                    currentPromptHash = promptHash;
                    currentPrompt = e.target.value;
                    selectedVideoPath = videoPath;
                    
                    displayResults([{
                        take_id: 1,
                        video_url: videoPath,
                        video_path: videoPath,
                        scores: {
                            overall: 0.95
                        },
                        rank: 1
                    }]);
                } else {
                    // Just a prompt - fill input
                    document.getElementById('promptInput').value = e.target.value;
                }
                
                // Reset dropdown
                cachedPromptsDropdown.value = '';
            }
        });
    }
}

/**
 * Load cached prompts from backend (includes demo videos and cached generations)
 */
async function loadCachedPrompts() {
    try {
        const response = await fetch('/api/cached_prompts');
        const data = await response.json();
        
        const dropdown = document.getElementById('cachedPromptsDropdown');
        if (!dropdown) return;
        
        // Clear existing options except the first one
        dropdown.innerHTML = '<option value="">Or load cached...</option>';
        
        // Add demo videos as separate section
        const demos = [
            {
                prompt: 'Demo: Cube Animation',
                path: '/data/samples/demo.mp4',
                hash: 'demo_cube',
                isDemo: true
            },
            {
                prompt: 'Demo: Man Walking Through Trees',
                path: '/data/generations/796b6b5a7803e5aa/take_1.mp4',
                hash: '796b6b5a7803e5aa',
                isDemo: true
            },
            {
                prompt: 'Demo: Catapult Launching',
                path: '/data/generations/fec980cf43d9b057/take_1.mp4',
                hash: 'fec980cf43d9b057',
                isDemo: true
            }
        ];
        
        // Add demo section
        demos.forEach(demo => {
            const option = document.createElement('option');
            option.value = demo.prompt;
            option.dataset.path = demo.path;
            option.dataset.hash = demo.hash;
            option.textContent = demo.prompt;
            option.style.color = '#22c55e'; // Green for demos
            dropdown.appendChild(option);
        });
        
        // Add separator if there are cached prompts
        if (data.prompts && data.prompts.length > 0) {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '──────────';
            dropdown.appendChild(separator);
            
            // Add cached prompts
            data.prompts.forEach(item => {
                const option = document.createElement('option');
                option.value = item.prompt;
                option.dataset.hash = item.hash;
                // Truncate long prompts for dropdown display
                const displayText = item.prompt.length > 45 
                    ? item.prompt.substring(0, 42) + '...' 
                    : item.prompt;
                option.textContent = `${displayText} (${item.mode})`;
                option.title = item.prompt; // Full text on hover
                dropdown.appendChild(option);
            });
            
            console.log(`Loaded ${demos.length} demos + ${data.count} cached prompts`);
        } else {
            console.log(`Loaded ${demos.length} demo videos`);
        }
    } catch (error) {
        console.error('Failed to load cached prompts:', error);
    }
}

/**
 * Handle quick demo button
 */
async function handleDemo() {
    // Load the first demo (cube animation)
    const demoPath = '/data/samples/demo.mp4';
    const demoPrompt = 'Demo: Cube Animation';
    const demoHash = 'demo_cube';
    
    currentPromptHash = demoHash;
    currentPrompt = demoPrompt;
    selectedVideoPath = demoPath;
    
    displayResults([{
        take_id: 1,
        video_url: demoPath,
        video_path: demoPath,
        scores: {
            overall: 0.95
        },
        rank: 1
    }]);
    
    showError('Demo video loaded - ready for 3D reconstruction!', 'warning');
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
        // Start progress polling in parallel with generation
        pollProgress(promptHash).catch(err => {
            console.warn('Progress polling ended:', err.message);
        });
        
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                prompt, 
                num_takes: 1,  // Always generate 1 video
                use_real_api: true  // Always use real Sora API
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentPromptHash = data.prompt_hash;
            currentPrompt = data.prompt;
            
            // Show info if video was cached
            if (data.cached) {
                console.log('Using cached video from previous generation');
                showError('Using cached video - no API call needed!', 'warning');
            }
            
            // Show warning if real API was requested but fell back to mock
            if (useRealAPI && data.mode === 'MOCK') {
                console.warn('Real Sora API unavailable - generated mock video instead');
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
                
                // Get reconstruction method
                const reconstructionMethod = document.getElementById('reconstructionMethod')?.value || 'gpt';
                const useDepth = reconstructionMethod === 'depth';
                
                // Reconstruct 3D scene
                await viewer3D.createWorldFromVideo(selectedVideoPath, currentPrompt, currentFrameCount, useDepth);
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
 * Regenerate 3D scene with selected method
 */
async function handleRegenerate3D() {
    if (!selectedVideoPath) {
        showError('No video to reconstruct');
        return;
    }
    
    const regenerate3DBtn = document.getElementById('regenerate3DBtn');
    setButtonLoading(regenerate3DBtn, true);
    
    try {
        // Show loading indicator
        const loading = document.getElementById('viewerLoading');
        const loadingSubtext = document.getElementById('loadingSubtext');
        if (loading) loading.style.display = 'flex';
        
        // Get reconstruction method
        const reconstructionMethod = document.getElementById('reconstructionMethod')?.value || 'gpt';
        const useDepth = reconstructionMethod === 'depth';
        
        console.log(`Regenerating 3D scene with method: ${reconstructionMethod}`);
        
        // Regenerate scene
        await viewer3D.createWorldFromVideo(selectedVideoPath, currentPrompt, currentFrameCount, useDepth);
        
        // Hide loading indicator
        if (loading) loading.style.display = 'none';
        
        showError('3D scene regenerated successfully!', 'warning');
        
    } catch (error) {
        console.error('3D regeneration error:', error);
        showError('Failed to regenerate 3D scene. Please try again.');
        
        // Hide loading indicator
        const loading = document.getElementById('viewerLoading');
        if (loading) loading.style.display = 'none';
    } finally {
        setButtonLoading(regenerate3DBtn, false);
    }
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

