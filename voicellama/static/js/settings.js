/**
 * TTS Settings Page JavaScript
 */

let settings = {
    engine: 'kokoro',
    voice: 'af_heart',
    speed: 1.0,
    enabled: true,
    avatar_enabled: false,
    chatter_level: 'sparse',
    custom_states: {
        question: true,
        summary: false,
        detail: false
    }
};

let avatarWindow = null;
let originalChatterLevel = null;  // Track original level for change detection

async function loadSettings() {
    try {
        const res = await fetch('/settings');
        settings = await res.json();
        applySettings();
    } catch (e) {
        console.error('Failed to load settings:', e);
    }
}

function applySettings() {
    document.getElementById('voice').value = settings.voice;
    document.getElementById('speed').value = settings.speed;
    document.getElementById('speedValue').textContent = settings.speed;

    document.querySelectorAll('.engine-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.engine === settings.engine);
    });

    const toggle = document.getElementById('enabledToggle');
    toggle.classList.toggle('active', settings.enabled);

    const avatarToggle = document.getElementById('avatarToggle');
    avatarToggle.classList.toggle('active', settings.avatar_enabled);

    // Auto-open avatar if enabled
    if (settings.avatar_enabled) {
        openAvatarPopup();
    }

    // Chatter level
    document.querySelectorAll('.chatter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === settings.chatter_level);
    });

    // Show/hide custom states panel
    const customPanel = document.getElementById('customStates');
    if (settings.chatter_level === 'custom') {
        customPanel.classList.add('visible');
    } else {
        customPanel.classList.remove('visible');
    }

    // Apply custom states checkboxes
    if (settings.custom_states) {
        document.getElementById('stateQuestion').checked = settings.custom_states.question;
        document.getElementById('stateSummary').checked = settings.custom_states.summary;
        document.getElementById('stateDetail').checked = settings.custom_states.detail;
    }

    // Store original chatter level for change detection
    if (originalChatterLevel === null) {
        originalChatterLevel = settings.chatter_level;
    }
}

function setEngine(engine) {
    settings.engine = engine;
    document.querySelectorAll('.engine-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.engine === engine);
    });
}

function toggleEnabled() {
    settings.enabled = !settings.enabled;
    document.getElementById('enabledToggle').classList.toggle('active', settings.enabled);
}

function toggleAvatar() {
    settings.avatar_enabled = !settings.avatar_enabled;
    document.getElementById('avatarToggle').classList.toggle('active', settings.avatar_enabled);
    if (settings.avatar_enabled) {
        openAvatarPopup();
    } else if (avatarWindow && !avatarWindow.closed) {
        avatarWindow.close();
    }
}

function openAvatarPopup() {
    // Check if window is already open
    if (avatarWindow && !avatarWindow.closed) {
        avatarWindow.focus();
        return;
    }
    // Open popup centered on screen
    const width = 600;
    const height = 500;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    avatarWindow = window.open(
        '/avatar',
        'TTS Avatar',
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=no`
    );
}

function setChatterLevel(level) {
    settings.chatter_level = level;
    document.querySelectorAll('.chatter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === level);
    });

    // Show/hide custom states panel
    const customPanel = document.getElementById('customStates');
    if (level === 'custom') {
        customPanel.classList.add('visible');
    } else {
        customPanel.classList.remove('visible');
    }

    // Highlight notice if level changed from original
    const notice = document.getElementById('chatterNotice');
    if (level !== originalChatterLevel) {
        notice.classList.add('changed');
    } else {
        notice.classList.remove('changed');
    }
}

function updateCustomStates() {
    settings.custom_states = {
        question: document.getElementById('stateQuestion').checked,
        summary: document.getElementById('stateSummary').checked,
        detail: document.getElementById('stateDetail').checked
    };
}

function updateSettings() {
    settings.voice = document.getElementById('voice').value;
    settings.speed = parseFloat(document.getElementById('speed').value);
    document.getElementById('speedValue').textContent = settings.speed;
}

async function saveSettings() {
    try {
        const res = await fetch('/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        showStatus('Settings saved!', 'success');

        // Update original chatter level after save
        originalChatterLevel = settings.chatter_level;
        document.getElementById('chatterNotice').classList.remove('changed');
    } catch (e) {
        showStatus('Failed to save settings', 'error');
    }
}

async function testTTS() {
    const text = document.getElementById('testText').value;
    if (!text) return;

    showStatus('Generating...', 'success');

    try {
        const res = await fetch('/tts/announce', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice: settings.voice,
                speed: settings.speed
            })
        });

        if (res.ok) {
            showStatus('Audio sent to player!', 'success');
        } else {
            showStatus('Generation failed', 'error');
        }
    } catch (e) {
        showStatus('Connection error', 'error');
    }
}

function showStatus(msg, type) {
    const status = document.getElementById('status');
    status.textContent = msg;
    status.className = 'status ' + type;
    setTimeout(() => { status.className = 'status'; }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();

    // Speed slider live update
    document.getElementById('speed').addEventListener('input', function() {
        document.getElementById('speedValue').textContent = this.value;
    });
});
