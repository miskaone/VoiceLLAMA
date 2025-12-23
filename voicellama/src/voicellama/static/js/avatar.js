/**
 * TTS Avatar Visualization JavaScript
 * Uses Three.js for 3D waveform visualization
 */

// Three.js setup
const canvas = document.getElementById('canvas');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Waveform bars
const barCount = 64;
const bars = [];
const barWidth = 0.15;
const barSpacing = 0.2;
const totalWidth = barCount * barSpacing;

const barGeometry = new THREE.BoxGeometry(barWidth, 1, barWidth);

for (let i = 0; i < barCount; i++) {
    const hue = (i / barCount) * 0.1 + 0.08; // Gold to orange gradient
    const material = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setHSL(hue, 0.9, 0.5),
        transparent: true,
        opacity: 0.6
    });
    const bar = new THREE.Mesh(barGeometry, material);
    bar.position.x = (i - barCount / 2) * barSpacing;
    bar.position.y = 0;
    bar.scale.y = 0.1;
    scene.add(bar);
    bars.push(bar);
}

// Ring visualization - gold theme
const ringGeometry = new THREE.RingGeometry(2, 2.2, 64);
const ringMaterial = new THREE.MeshBasicMaterial({
    color: 0xffc800,
    transparent: true,
    opacity: 0.3,
    side: THREE.DoubleSide
});
const ring = new THREE.Mesh(ringGeometry, ringMaterial);
ring.rotation.x = Math.PI / 2;
ring.position.y = -1;
scene.add(ring);

camera.position.z = 8;
camera.position.y = 2;
camera.lookAt(0, 0, 0);

// Audio analysis
let audioContext = null;
let analyser = null;
let dataArray = null;
let gainNode = null;
let isPlaying = false;
let currentAudio = null;
let audioEnabled = false;

function initAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        dataArray = new Uint8Array(analyser.frequencyBinCount);

        // Create a silent gain node - audio must flow to destination for analysis to work
        gainNode = audioContext.createGain();
        gainNode.gain.value = 0; // Silent - Python player handles actual audio
        analyser.connect(gainNode);
        gainNode.connect(audioContext.destination);
    }
    // Resume if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
        audioContext.resume().then(() => {
            audioEnabled = true;
            hideAudioPrompt();
            console.log('AudioContext resumed');
        });
    } else {
        audioEnabled = true;
        hideAudioPrompt();
    }
}

function showAudioPrompt() {
    let prompt = document.getElementById('audio-prompt');
    if (!prompt) {
        prompt = document.createElement('div');
        prompt.id = 'audio-prompt';
        prompt.innerHTML = '<span>Click anywhere to enable audio visualization</span>';
        prompt.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 200, 0, 0.9);
            color: #000;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            z-index: 1000;
            cursor: pointer;
            animation: pulse 2s infinite;
        `;
        document.body.appendChild(prompt);
    }
    prompt.style.display = 'block';
}

function hideAudioPrompt() {
    const prompt = document.getElementById('audio-prompt');
    if (prompt) {
        prompt.style.display = 'none';
    }
}

// Enable audio on any user gesture
function enableAudioOnGesture() {
    if (!audioEnabled) {
        initAudio();
    }
}

// Add click listener to enable audio
document.addEventListener('click', enableAudioOnGesture, { once: false });
document.addEventListener('touchstart', enableAudioOnGesture, { once: false });
document.addEventListener('keydown', enableAudioOnGesture, { once: false });

// Show prompt on page load
document.addEventListener('DOMContentLoaded', () => {
    showAudioPrompt();
});

async function playAudio(base64Audio) {
    initAudio();

    // Stop current audio if playing
    if (currentAudio) {
        try { currentAudio.stop(); } catch(e) {}
    }

    // Decode base64 to array buffer
    const binaryString = atob(base64Audio);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    try {
        const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(analyser);
        // Analyser connects to silent gain node -> destination (set up in initAudio)

        currentAudio = source;
        isPlaying = true;
        console.log('Audio started, duration:', audioBuffer.duration);

        source.onended = () => {
            isPlaying = false;
            currentAudio = null;
            document.getElementById('text-display').classList.remove('visible');
            console.log('Audio ended');
        };

        source.start();
    } catch (e) {
        console.error('Error playing audio:', e);
        isPlaying = false;
        currentAudio = null;
    }
}

// Animation
let time = 0;
const avatarLogo = document.getElementById('avatar-logo');
let wasPlaying = false;  // Track state changes to avoid constant DOM updates

function animate() {
    requestAnimationFrame(animate);
    time += 0.02;

    try {
    const currentlyPlaying = analyser && isPlaying;

    if (currentlyPlaying) {
        analyser.getByteFrequencyData(dataArray);

        // Update bars based on audio
        for (let i = 0; i < barCount; i++) {
            const index = Math.floor(i / barCount * dataArray.length);
            const value = dataArray[index] / 255;
            const targetScale = Math.max(0.1, value * 4);
            bars[i].scale.y += (targetScale - bars[i].scale.y) * 0.3;
            bars[i].position.y = bars[i].scale.y / 2;

            // Color intensity based on amplitude - gold/orange theme
            const hue = (i / barCount) * 0.1 + 0.08; // Gold to orange
            bars[i].material.color.setHSL(hue, 0.9, 0.4 + value * 0.4);
            bars[i].material.opacity = 0.5 + value * 0.5;
        }

        // Update glow based on average amplitude
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255;
        const glow = document.getElementById('glow');
        const scale = 1 + avg * 0.5;
        glow.style.transform = `translate(-50%, -50%) scale(${scale})`;
        glow.style.opacity = 0.3 + avg * 0.7;

        // Ring pulse
        ring.scale.set(1 + avg * 0.3, 1 + avg * 0.3, 1);
        ringMaterial.opacity = 0.2 + avg * 0.4;

        // Avatar logo audio-reactive effects (only update classes on state change)
        if (!wasPlaying) {
            avatarLogo.classList.remove('idle');
            avatarLogo.classList.add('speaking');
        }
        const logoScale = 1 + avg * 0.15;
        const glowIntensity = 20 + avg * 40;
        const glowOpacity = 0.3 + avg * 0.5;
        avatarLogo.style.transform = `translate(-50%, -50%) scale(${logoScale})`;
        avatarLogo.style.filter = `drop-shadow(0 0 ${glowIntensity}px rgba(255, 200, 0, ${glowOpacity}))`;

    } else {
        // Idle animation for bars
        for (let i = 0; i < barCount; i++) {
            const idleValue = Math.sin(time + i * 0.2) * 0.1 + 0.15;
            bars[i].scale.y += (idleValue - bars[i].scale.y) * 0.1;
            bars[i].position.y = bars[i].scale.y / 2;
            // Keep gold color during idle
            const hue = (i / barCount) * 0.1 + 0.08;
            bars[i].material.color.setHSL(hue, 0.9, 0.5);
            bars[i].material.opacity = 0.4;
        }

        const glow = document.getElementById('glow');
        glow.style.transform = `translate(-50%, -50%) scale(1)`;
        glow.style.opacity = 0.3;

        // Avatar logo idle state - only update on state change to let CSS animation work
        if (wasPlaying) {
            avatarLogo.classList.remove('speaking');
            avatarLogo.classList.add('idle');
            avatarLogo.style.transform = '';
            avatarLogo.style.filter = '';
        }
    }

    wasPlaying = currentlyPlaying;
    } catch (e) {
        console.error('Animation error:', e);
    }

    // Subtle camera movement
    camera.position.x = Math.sin(time * 0.3) * 0.5;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
}
animate();

// Context window pie chart
function updateContextPie(percentage) {
    const pie = document.getElementById('context-pie');
    const percentLabel = document.getElementById('context-percentage');

    // Update percentage text
    percentLabel.textContent = Math.round(percentage) + '%';

    // Update pie chart fill
    const degrees = (percentage / 100) * 360;
    pie.style.background = `conic-gradient(
        #ffc800 0deg,
        #ffc800 ${degrees}deg,
        rgba(255,255,255,0.1) ${degrees}deg,
        rgba(255,255,255,0.1) 360deg
    )`;

    // Update color based on level
    pie.classList.remove('warning', 'critical');
    if (percentage >= 90) {
        pie.classList.add('critical');
        pie.style.background = `conic-gradient(
            #ff3c3c 0deg,
            #ff3c3c ${degrees}deg,
            rgba(255,255,255,0.1) ${degrees}deg,
            rgba(255,255,255,0.1) 360deg
        )`;
    } else if (percentage >= 70) {
        pie.classList.add('warning');
        pie.style.background = `conic-gradient(
            #ff9800 0deg,
            #ff9800 ${degrees}deg,
            rgba(255,255,255,0.1) ${degrees}deg,
            rgba(255,255,255,0.1) 360deg
        )`;
    }
}

// Fetch initial context state
fetch('/context')
    .then(r => r.json())
    .then(data => updateContextPie(data.percentage))
    .catch(e => console.log('Could not fetch context:', e));

// Poll for context updates every 5 seconds
setInterval(() => {
    fetch('/context')
        .then(r => r.json())
        .then(data => updateContextPie(data.percentage))
        .catch(() => {});
}, 5000);

// WebSocket connection
const ws = new WebSocket('ws://localhost:8333/ws/tts');

ws.onopen = () => {
    document.getElementById('status').textContent = 'Connected - Visualization only';
};

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data.type);
        if (data.type === 'audio') {
            console.log('Audio data received, length:', data.audio?.length);
            document.getElementById('status').textContent = 'Visualizing...';

            // Show text
            const textDisplay = document.getElementById('text-display');
            textDisplay.textContent = data.text || '';
            textDisplay.classList.add('visible');

            playAudio(data.audio);
        } else if (data.type === 'context') {
            // Update context pie chart
            updateContextPie(data.percentage);
        }
    } catch (e) {
        console.error('Error processing message:', e);
    }
};

ws.onclose = () => {
    document.getElementById('status').textContent = 'Disconnected - Reconnecting...';
    setTimeout(() => location.reload(), 3000);
};

ws.onerror = () => {
    document.getElementById('status').textContent = 'Connection error';
};

// Handle window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
