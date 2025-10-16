/**
 * Interactive 3D Viewer using Three.js
 * Supports zoom, pan, and rotation
 */

class Viewer3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.world = null;
        this.agent = null;
        this.agentPath = [];
        this.agentAnimating = false;
        this.violationMarkers = [];
        
        this.init();
    }
    
    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        this.scene.fog = new THREE.Fog(0x1a1a1a, 10, 50);
        
        // Get parent dimensions for proper sizing
        const parent = this.canvas.parentElement;
        const width = parent.clientWidth || 800;
        const height = 500;
        
        // Camera
        const aspect = width / height;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(5, 3, 5);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: this.canvas,
            antialias: true 
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        
        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.canvas);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 2;
        this.controls.maxDistance = 20;
        this.controls.maxPolarAngle = Math.PI / 2;
        
        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        this.scene.add(directionalLight);
        
        // Grid
        const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
        this.scene.add(gridHelper);
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation loop
        this.animate();
    }
    
    async createWorldFromVideo(videoPath, prompt, frameCount = 3) {
        try {
            // Update loading text
            const loadingSubtext = document.getElementById('loadingSubtext');
            if (loadingSubtext) {
                loadingSubtext.textContent = 'Intelligently analyzing video frames...';
            }
            
            // Use GPT-4 Vision to analyze video and generate scene
            console.log('🎬 Starting 3D scene generation...');
            console.log(`📹 Video path: ${videoPath}`);
            console.log(`🎯 Prompt: ${prompt}`);
            console.log(`🖼️  Analyzing ${frameCount} frames with GPT-4 Vision...`);
            
            const response = await fetch('/api/generate_scene', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_path: videoPath, prompt: prompt, frame_count: frameCount })
            });
            
            console.log(`📡 API Response status: ${response.status}`);
            
            // Update loading text
            if (loadingSubtext) {
                loadingSubtext.textContent = 'Building 3D scene...';
            }
            
            if (response.ok) {
                const data = await response.json();
                console.log('📦 Received data:', data);
                
                if (data.success && data.scene) {
                    console.log(`✨ Scene source: ${data.source || 'unknown'}`);
                    
                    if (data.scene.code) {
                        // GPT-4 Vision generated code - execute it
                        console.log('🤖 GPT-4 Vision analysis:', data.scene.analysis);
                        console.log('🏗️  Building 3D scene from generated code...');
                        this.executeGeneratedCode(data.scene.code);
                        console.log('✅ 3D scene generation complete!');
                    } else {
                        // Old format - use object-based scene
                        console.log('📐 Using object-based scene format');
                        this.createSceneFromData(data.scene);
                    }
                    return;
                } else {
                    console.warn('⚠️  No valid scene data in response');
                }
            } else {
                console.error(`❌ API request failed with status ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Failed to generate scene:', error);
        }
        
        // Fall back to demo world
        console.log('⚠️  Falling back to default demo world');
        this.createDemoWorld();
    }
    
    executeGeneratedCode(code) {
        // Clear existing world
        if (this.world) {
            this.scene.remove(this.world);
        }
        
        this.world = new THREE.Group();
        
        try {
            // Create a safe execution context
            const THREE = window.THREE;
            
            // Execute the generated code
            const createScene = new Function('THREE', code);
            const objects = createScene(THREE);
            
            // Add objects to world
            if (Array.isArray(objects)) {
                objects.forEach(obj => {
                    if (obj && obj.isObject3D) {
                        obj.castShadow = true;
                        obj.receiveShadow = true;
                        this.world.add(obj);
                    }
                });
            }
            
            this.scene.add(this.world);
            console.log('Successfully executed GPT-generated scene code');
            
        } catch (error) {
            console.error('Failed to execute generated code:', error);
            console.error('Code was:', code);
            // Fall back to demo world
            this.createDemoWorld();
        }
    }
    
    createSceneFromData(sceneData) {
        // Clear existing world
        if (this.world) {
            this.scene.remove(this.world);
        }
        
        this.world = new THREE.Group();
        
        // Floor (always present)
        const floorGeometry = new THREE.PlaneGeometry(20, 20);
        const floorMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x333333,
            roughness: 0.8,
            metalness: 0.2
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.world.add(floor);
        
        // Add objects from scene data
        if (sceneData.objects) {
            sceneData.objects.forEach(obj => {
                let geometry;
                const color = parseInt(obj.color);
                const [scaleX, scaleY, scaleZ] = obj.scale;
                const [posX, posY, posZ] = obj.position;
                
                switch (obj.type) {
                    case 'box':
                        geometry = new THREE.BoxGeometry(scaleX, scaleY, scaleZ);
                        break;
                    case 'sphere':
                        geometry = new THREE.SphereGeometry(scaleX, 32, 32);
                        break;
                    case 'cylinder':
                        geometry = new THREE.CylinderGeometry(scaleX, scaleX, scaleY, 32);
                        break;
                    default:
                        geometry = new THREE.BoxGeometry(scaleX, scaleY, scaleZ);
                }
                
                const material = new THREE.MeshStandardMaterial({
                    color: color,
                    roughness: 0.7,
                    metalness: 0.3
                });
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(posX, posY, posZ);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                this.world.add(mesh);
            });
        }
        
        this.scene.add(this.world);
    }
    
    createDemoWorld() {
        // Clear existing world
        if (this.world) {
            this.scene.remove(this.world);
        }
        
        this.world = new THREE.Group();
        
        // Floor
        const floorGeometry = new THREE.PlaneGeometry(20, 20);
        const floorMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x333333,
            roughness: 0.8,
            metalness: 0.2
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.world.add(floor);
        
        // Create a hallway scene
        const wallMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4a5568,
            roughness: 0.7
        });
        
        // Left wall
        const leftWall = new THREE.Mesh(
            new THREE.BoxGeometry(0.5, 3, 15),
            wallMaterial
        );
        leftWall.position.set(-3, 1.5, 0);
        leftWall.castShadow = true;
        this.world.add(leftWall);
        
        // Right wall
        const rightWall = new THREE.Mesh(
            new THREE.BoxGeometry(0.5, 3, 15),
            wallMaterial
        );
        rightWall.position.set(3, 1.5, 0);
        rightWall.castShadow = true;
        this.world.add(rightWall);
        
        // Back wall
        const backWall = new THREE.Mesh(
            new THREE.BoxGeometry(6.5, 3, 0.5),
            wallMaterial
        );
        backWall.position.set(0, 1.5, -7.5);
        backWall.castShadow = true;
        this.world.add(backWall);
        
        // Add some objects in the hallway
        const objectMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x667eea,
            roughness: 0.5,
            metalness: 0.5
        });
        
        // Boxes
        for (let i = 0; i < 5; i++) {
            const box = new THREE.Mesh(
                new THREE.BoxGeometry(0.5, 0.5, 0.5),
                objectMaterial
            );
            box.position.set(
                (Math.random() - 0.5) * 4,
                0.25,
                -6 + i * 2.5
            );
            box.castShadow = true;
            box.receiveShadow = true;
            this.world.add(box);
        }
        
        // Spheres
        const sphereMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x764ba2,
            roughness: 0.3,
            metalness: 0.7
        });
        
        for (let i = 0; i < 3; i++) {
            const sphere = new THREE.Mesh(
                new THREE.SphereGeometry(0.3, 32, 32),
                sphereMaterial
            );
            sphere.position.set(
                (Math.random() - 0.5) * 4,
                0.3,
                -5 + i * 3
            );
            sphere.castShadow = true;
            sphere.receiveShadow = true;
            this.world.add(sphere);
        }
        
        // Add a robot (simple representation)
        const robotGroup = new THREE.Group();
        
        // Robot body
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(0.6, 0.8, 0.4),
            new THREE.MeshStandardMaterial({ color: 0xff6b6b })
        );
        body.position.y = 1;
        body.castShadow = true;
        robotGroup.add(body);
        
        // Robot head
        const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.3, 32, 32),
            new THREE.MeshStandardMaterial({ color: 0xffd93d })
        );
        head.position.y = 1.6;
        head.castShadow = true;
        robotGroup.add(head);
        
        robotGroup.position.set(0, 0, 5);
        this.world.add(robotGroup);
        
        this.scene.add(this.world);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        this.controls.update();
        
        // Update agent animation
        this.updateAgentAnimation();
        
        // Render
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        const parent = this.canvas.parentElement;
        const width = parent.clientWidth || 800;
        const height = 500;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    show() {
        this.canvas.classList.add('active');
        // Force resize after showing
        setTimeout(() => this.onWindowResize(), 100);
    }
    
    hide() {
        this.canvas.classList.remove('active');
    }
    
    /**
     * Create an animated agent that moves through the scene
     */
    createAgent() {
        // Create agent (glowing sphere)
        const agentGeometry = new THREE.SphereGeometry(0.3, 32, 32);
        const agentMaterial = new THREE.MeshStandardMaterial({
            color: 0x00ff88,
            emissive: 0x00ff88,
            emissiveIntensity: 0.5,
            metalness: 0.8,
            roughness: 0.2
        });
        
        this.agent = new THREE.Mesh(agentGeometry, agentMaterial);
        this.agent.position.set(0, 0.5, 5);
        this.agent.castShadow = true;
        
        // Add glow effect
        const glowGeometry = new THREE.SphereGeometry(0.5, 32, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff88,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        this.agent.add(glow);
        
        this.scene.add(this.agent);
        
        return this.agent;
    }
    
    /**
     * Animate the agent along a path
     */
    animateAgent(violations = []) {
        if (!this.agent) {
            this.createAgent();
        }
        
        // Clear old violation markers
        this.violationMarkers.forEach(marker => this.scene.remove(marker));
        this.violationMarkers = [];
        
        // Define test path through the scene
        this.agentPath = [
            { x: 0, y: 0.5, z: 5 },
            { x: -2, y: 0.5, z: 3 },
            { x: -2, y: 0.5, z: 0 },
            { x: 0, y: 0.5, z: -2 },
            { x: 2, y: 0.5, z: -4 },
            { x: 2, y: 0.5, z: -6 },
            { x: 0, y: 0.5, z: -6 }
        ];
        
        // Add violation markers at random points
        violations.forEach((violation, index) => {
            const markerGeometry = new THREE.SphereGeometry(0.4, 16, 16);
            const markerMaterial = new THREE.MeshBasicMaterial({
                color: 0xff0000,
                transparent: true,
                opacity: 0.7
            });
            const marker = new THREE.Mesh(markerGeometry, markerMaterial);
            
            // Place at random path position
            const pathIndex = Math.floor((index + 1) * this.agentPath.length / (violations.length + 1));
            const pos = this.agentPath[pathIndex];
            marker.position.set(pos.x, pos.y + 1, pos.z);
            
            this.scene.add(marker);
            this.violationMarkers.push(marker);
        });
        
        // Start animation
        this.agentAnimating = true;
        this.currentPathIndex = 0;
        this.pathProgress = 0;
        
        return new Promise((resolve) => {
            this.agentAnimationResolve = resolve;
        });
    }
    
    /**
     * Update agent position during animation
     */
    updateAgentAnimation() {
        if (!this.agentAnimating || !this.agent) return;
        
        const speed = 0.02; // Movement speed
        this.pathProgress += speed;
        
        if (this.pathProgress >= 1) {
            this.pathProgress = 0;
            this.currentPathIndex++;
            
            if (this.currentPathIndex >= this.agentPath.length - 1) {
                // Animation complete
                this.agentAnimating = false;
                if (this.agentAnimationResolve) {
                    this.agentAnimationResolve();
                }
                return;
            }
        }
        
        // Interpolate between current and next point
        const current = this.agentPath[this.currentPathIndex];
        const next = this.agentPath[this.currentPathIndex + 1];
        
        this.agent.position.x = current.x + (next.x - current.x) * this.pathProgress;
        this.agent.position.y = current.y + (next.y - current.y) * this.pathProgress;
        this.agent.position.z = current.z + (next.z - current.z) * this.pathProgress;
        
        // Bob up and down slightly
        this.agent.position.y += Math.sin(Date.now() * 0.005) * 0.1;
        
        // Pulse violation markers
        this.violationMarkers.forEach((marker, index) => {
            const scale = 1 + Math.sin(Date.now() * 0.003 + index) * 0.2;
            marker.scale.set(scale, scale, scale);
        });
    }
    
    /**
     * Stop agent animation
     */
    stopAgentAnimation() {
        this.agentAnimating = false;
        if (this.agent) {
            this.scene.remove(this.agent);
            this.agent = null;
        }
        this.violationMarkers.forEach(marker => this.scene.remove(marker));
        this.violationMarkers = [];
    }
}

