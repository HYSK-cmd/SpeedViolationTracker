let uploadedFilename = null;
let eventSource = null;
let livestreamActive = false;

// --- ROI state ---
let roiPoints = [];
let roiImage = null;
const ROI_MAX_POINTS = 4;

// --- SSE log stream ---
function connectLogs() {
    if (eventSource) return;
    eventSource = new EventSource('/api/logs/stream');
    eventSource.onmessage = (e) => {
        if (!e.data) return;
        appendLog(e.data);
    };
}

function appendLog(text) {
    const output = document.getElementById('log-output');
    const line = document.createElement('div');
    line.className = 'log-line';
    if (text.includes('[WARNING]')) line.classList.add('warn');
    else if (text.includes('[ERROR]')) line.classList.add('error');
    else if (text.includes('[INFO]')) line.classList.add('info');
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function clearLogs() {
    document.getElementById('log-output').innerHTML = '';
}

// --- Validation ---
const VALID_EXTENSIONS = ['.mp4', '.webm'];

function isValidVideoFilename(name) {
    return VALID_EXTENSIONS.some(ext => name.toLowerCase().endsWith(ext));
}

function checkReady() {
    const outputVideo = document.getElementById('output-video').value.trim();
    const model = document.getElementById('model-select').value;
    const realW = parseFloat(document.getElementById('real-width').value);
    const realH = parseFloat(document.getElementById('real-height').value);
    const roiOk = roiPoints.length === ROI_MAX_POINTS && realW > 0 && realH > 0;
    document.getElementById('btn-run').disabled = !(uploadedFilename && isValidVideoFilename(outputVideo) && model && roiOk);
}

let saveVideo = false;

function checkLivestreamReady() {
    if (livestreamActive) return;
    const model = document.getElementById('ls-model-select').value;
    if (!model) {
        document.getElementById('btn-livestream-toggle').disabled = true;
        return;
    }
    if (saveVideo) {
        const outputVideo = document.getElementById('ls-output-video').value.trim();
        document.getElementById('btn-livestream-toggle').disabled = !isValidVideoFilename(outputVideo);
    } else {
        document.getElementById('btn-livestream-toggle').disabled = false;
    }
}

function toggleSaveVideo(on) {
    saveVideo = on;
    document.getElementById('save-yes').classList.toggle('active', on);
    document.getElementById('save-no').classList.toggle('active', !on);
    const input = document.getElementById('ls-output-video');
    const label = input.closest('.form-group').querySelector('label');
    input.disabled = !on;
    if (on) {
        input.placeholder = 'i.e) output.mp4';
        label.classList.remove('disabled-label');
    } else {
        input.value = '';
        input.placeholder = '';
        label.classList.add('disabled-label');
    }
    checkLivestreamReady();
}

// --- Mode switching ---
function switchMode(mode) {
    if (mode === 'video' && livestreamActive) {
        document.getElementById('modal-overlay').classList.remove('hidden');
        return;
    }
    applyMode(mode);
}

function applyMode(mode) {
    document.getElementById('btn-video').classList.toggle('active', mode === 'video');
    document.getElementById('btn-livestream').classList.toggle('active', mode === 'livestream');
    document.getElementById('panel-video').classList.toggle('hidden', mode !== 'video');
    document.getElementById('panel-livestream').classList.toggle('hidden', mode !== 'livestream');
}

// --- Modal ---
function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

async function confirmStopAndSwitch() {
    closeModal();
    await stopLivestream();
    applyMode('video');
}

// --- Video upload ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFile(fileInput.files[0]);
    }
});

function handleFile(file) {
    document.getElementById('file-name').textContent = file.name;
    uploadFile(file);
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('video', file);
    appendLog(`Uploading ${file.name}...`);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            uploadedFilename = data.filename;
            appendLog(`Upload complete: ${data.filename}`);
            loadFirstFrame(data.filename);
        } else {
            appendLog(`Upload failed: ${data.error}`);
        }
    } catch (err) {
        appendLog(`Upload error: ${err.message}`);
    }
}

// --- ROI Canvas ---
function loadFirstFrame(filename) {
    const img = new Image();
    img.onload = () => {
        roiImage = img;
        roiPoints = [];
        const section = document.getElementById('roi-section');
        section.classList.remove('hidden');
        const canvas = document.getElementById('roi-canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        drawCanvas();
        checkReady();
    };
    img.src = `/api/video/first-frame/${filename}`;
}

function drawCanvas() {
    const canvas = document.getElementById('roi-canvas');
    const ctx = canvas.getContext('2d');
    ctx.drawImage(roiImage, 0, 0);

    if (roiPoints.length === 0) return;

    // draw filled polygon with transparency
    if (roiPoints.length >= 3) {
        ctx.beginPath();
        ctx.moveTo(roiPoints[0][0], roiPoints[0][1]);
        for (let i = 1; i < roiPoints.length; i++) {
            ctx.lineTo(roiPoints[i][0], roiPoints[i][1]);
        }
        if (roiPoints.length === ROI_MAX_POINTS) ctx.closePath();
        ctx.fillStyle = 'rgba(153, 255, 255, 0.2)';
        ctx.fill();
    }

    // draw lines
    ctx.strokeStyle = '#ff3333';
    ctx.lineWidth = 2;
    for (let i = 0; i < roiPoints.length - 1; i++) {
        ctx.beginPath();
        ctx.moveTo(roiPoints[i][0], roiPoints[i][1]);
        ctx.lineTo(roiPoints[i + 1][0], roiPoints[i + 1][1]);
        ctx.stroke();
    }
    // close shape
    if (roiPoints.length === ROI_MAX_POINTS) {
        ctx.beginPath();
        ctx.moveTo(roiPoints[3][0], roiPoints[3][1]);
        ctx.lineTo(roiPoints[0][0], roiPoints[0][1]);
        ctx.stroke();
    }

    // draw points with labels
    const labels = ['A', 'B', 'C', 'D'];
    roiPoints.forEach((p, i) => {
        ctx.beginPath();
        ctx.arc(p[0], p[1], 5, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(labels[i], p[0] + 10, p[1] - 10);
    });
}

function resetROI() {
    roiPoints = [];
    drawCanvas();
    checkReady();
}

// canvas click handler
document.getElementById('roi-canvas').addEventListener('click', (e) => {
    if (!roiImage || roiPoints.length >= ROI_MAX_POINTS) return;
    const canvas = e.target;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    roiPoints.push([x, y]);
    drawCanvas();
    checkReady();
});

// --- Run video detection ---
async function runVideo() {
    const outputVideo = document.getElementById('output-video').value.trim();
    const model = document.getElementById('model-select').value;
    const realW = parseFloat(document.getElementById('real-width').value);
    const realH = parseFloat(document.getElementById('real-height').value);
    if (!uploadedFilename || !outputVideo || !model || roiPoints.length !== ROI_MAX_POINTS) return;

    document.getElementById('btn-run').disabled = true;

    try {
        const res = await fetch('/api/video/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: uploadedFilename,
                output_video: outputVideo,
                model: model,
                roi: { points: roiPoints, real_w: realW, real_h: realH },
            }),
        });
        const data = await res.json();
        appendLog(data.message);
    } catch (err) {
        appendLog(`Error: ${err.message}`);
    }
}

// --- Livestream ---
function setLivestreamUI(active) {
    livestreamActive = active;
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('livestream-text');
    const btn = document.getElementById('btn-livestream-toggle');

    if (active) {
        dot.classList.add('live');
        text.textContent = 'Livestream active';
        btn.textContent = 'Stop Livestream';
        btn.classList.add('stop');
        btn.disabled = false;
    } else {
        dot.classList.remove('live');
        text.textContent = 'Livestream ready';
        btn.textContent = 'Start Livestream';
        btn.classList.remove('stop');
        checkLivestreamReady();
    }
}

async function toggleLivestream() {
    if (livestreamActive) {
        await stopLivestream();
    } else {
        await startLivestream();
    }
}

async function startLivestream() {
    const outputVideo = document.getElementById('ls-output-video').value.trim();
    const model = document.getElementById('ls-model-select').value;
    if (!model) return;
    if (saveVideo && !isValidVideoFilename(outputVideo)) return;

    try {
        const res = await fetch('/api/livestream/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ output_video: outputVideo, model: model }),
        });
        const data = await res.json();
        setLivestreamUI(true);
        appendLog(data.message);
    } catch (err) {
        appendLog(`Livestream error: ${err.message}`);
    }
}

async function stopLivestream() {
    try {
        const res = await fetch('/api/livestream/stop', { method: 'POST' });
        const data = await res.json();
        setLivestreamUI(false);
        appendLog(data.message);
    } catch (err) {
        appendLog(`Livestream stop error: ${err.message}`);
    }
}

// --- Init ---
document.getElementById('output-video').addEventListener('input', checkReady);
document.getElementById('model-select').addEventListener('change', checkReady);
document.getElementById('real-width').addEventListener('input', checkReady);
document.getElementById('real-height').addEventListener('input', checkReady);
document.getElementById('ls-output-video').addEventListener('input', checkLivestreamReady);
document.getElementById('ls-model-select').addEventListener('change', checkLivestreamReady);
connectLogs();
