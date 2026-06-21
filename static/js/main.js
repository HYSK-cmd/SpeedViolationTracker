let uploadedFilename = null;
let eventSource = null;
let livestreamActive = false;

// --- ROI state ---
let roiPoints = [];
let roiImage = null;
const ROI_MAX_POINTS = 4;

// --- Livestream ROI state ---
let lsRoiPoints = [];
let lsRoiImage = null;

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
    const realW = parseFloat(document.getElementById('ls-real-width').value);
    const realH = parseFloat(document.getElementById('ls-real-height').value);
    const roiOk = lsRoiImage && lsRoiPoints.length === ROI_MAX_POINTS && realW > 0 && realH > 0;
    document.getElementById('btn-livestream-toggle').disabled = !(model && roiOk);
}

function toggleSaveVideo(on) {
    saveVideo = on;
    document.getElementById('save-yes').classList.toggle('active', on);
    document.getElementById('save-no').classList.toggle('active', !on);
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

// stop the browser from opening a file that's dropped anywhere outside the drop zone
['dragover', 'drop'].forEach((evt) => {
    window.addEventListener(evt, (e) => e.preventDefault());
});

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
    // NOTE: don't assign to fileInput.files here — it throws in some browsers (e.g.
    // Safari) and would abort before the upload runs. uploadFile() takes the File
    // directly, so the dropped file is all we need.
    if (e.dataTransfer.files.length) {
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

// generic ROI renderer shared by video and livestream canvases
function drawROI(canvas, image, points) {
    const ctx = canvas.getContext('2d');
    ctx.drawImage(image, 0, 0);

    if (points.length === 0) return;

    // draw filled polygon with transparency
    if (points.length >= 3) {
        ctx.beginPath();
        ctx.moveTo(points[0][0], points[0][1]);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i][0], points[i][1]);
        }
        if (points.length === ROI_MAX_POINTS) ctx.closePath();
        ctx.fillStyle = 'rgba(153, 255, 255, 0.2)';
        ctx.fill();
    }

    // draw lines
    ctx.strokeStyle = '#ff3333';
    ctx.lineWidth = 2;
    for (let i = 0; i < points.length - 1; i++) {
        ctx.beginPath();
        ctx.moveTo(points[i][0], points[i][1]);
        ctx.lineTo(points[i + 1][0], points[i + 1][1]);
        ctx.stroke();
    }
    // close shape
    if (points.length === ROI_MAX_POINTS) {
        ctx.beginPath();
        ctx.moveTo(points[3][0], points[3][1]);
        ctx.lineTo(points[0][0], points[0][1]);
        ctx.stroke();
    }

    // draw points with labels
    const labels = ['A', 'B', 'C', 'D'];
    points.forEach((p, i) => {
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

// add a clicked point to the given ROI canvas, returns true if a point was added
function addRoiPoint(canvas, points, e) {
    if (points.length >= ROI_MAX_POINTS) return false;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    points.push([x, y]);
    return true;
}

function drawCanvas() {
    drawROI(document.getElementById('roi-canvas'), roiImage, roiPoints);
}

function resetROI() {
    roiPoints = [];
    drawCanvas();
    checkReady();
}

// canvas click handler
document.getElementById('roi-canvas').addEventListener('click', (e) => {
    if (!roiImage) return;
    if (addRoiPoint(e.target, roiPoints, e)) {
        drawCanvas();
        checkReady();
    }
});

// --- Run video detection ---
async function runVideo() {
    const outputVideo = document.getElementById('output-video').value.trim();
    const model = document.getElementById('model-select').value;
    const realW = parseFloat(document.getElementById('real-width').value);
    const realH = parseFloat(document.getElementById('real-height').value);
    if (!uploadedFilename || !outputVideo || !model || roiPoints.length !== ROI_MAX_POINTS) return;

    document.getElementById('btn-run').disabled = true;
    document.getElementById('result-view').classList.add('hidden');

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
        if (!res.ok) {
            appendLog(`Error: ${data.error}`);
            document.getElementById('btn-run').disabled = false;
            return;
        }
        appendLog(data.message);

        // show the live MJPEG preview and poll until detection finishes
        const stream = document.getElementById('live-stream');
        stream.src = `/api/video/stream?t=${Date.now()}`;
        document.getElementById('detection-view').classList.remove('hidden');
        pollVideoStatus();
    } catch (err) {
        appendLog(`Error: ${err.message}`);
        document.getElementById('btn-run').disabled = false;
    }
}

async function pollVideoStatus() {
    try {
        const res = await fetch('/api/video/status');
        const data = await res.json();
        if (data.running) {
            setTimeout(pollVideoStatus, 1000);
            return;
        }
    } catch (err) {
        // transient error during processing; keep polling
        setTimeout(pollVideoStatus, 1000);
        return;
    }

    // detection finished: stop the live preview and show the saved result
    const stream = document.getElementById('live-stream');
    stream.src = '';
    document.getElementById('detection-view').classList.add('hidden');

    try {
        const res = await fetch('/api/video/status');
        const data = await res.json();
        if (data.output) {
            const url = `/api/video/result/${encodeURIComponent(data.output)}`;
            document.getElementById('result-video').src = url;
            const dl = document.getElementById('result-download');
            dl.href = url;
            dl.textContent = `Download ${data.output}`;
            document.getElementById('result-view').classList.remove('hidden');
        }
    } catch (err) {
        appendLog(`Could not load result: ${err.message}`);
    }

    document.getElementById('btn-run').disabled = false;
    checkReady();
}

// --- Livestream ROI ---
async function connectLivestream() {
    const btn = document.getElementById('btn-ls-connect');
    btn.disabled = true;
    btn.textContent = 'Connecting...';
    appendLog('Connecting to livestream camera...');

    const img = new Image();
    img.onload = () => {
        lsRoiImage = img;
        lsRoiPoints = [];
        const section = document.getElementById('ls-roi-section');
        section.classList.remove('hidden');
        const canvas = document.getElementById('ls-roi-canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        drawROI(canvas, lsRoiImage, lsRoiPoints);
        appendLog('Camera connected. Draw the ROI to continue.');
        btn.textContent = 'Reconnect to Camera';
        btn.disabled = false;
        checkLivestreamReady();
    };
    img.onerror = async () => {
        // surface the server error message if there is one
        try {
            const res = await fetch('/api/livestream/first-frame');
            const data = await res.json();
            appendLog(`Camera connection failed: ${data.error || res.statusText}`);
        } catch (err) {
            appendLog(`Camera connection failed: ${err.message}`);
        }
        btn.textContent = 'Connect to Camera';
        btn.disabled = false;
    };
    // cache-bust so a reconnect always re-fetches
    img.src = `/api/livestream/first-frame?t=${Date.now()}`;
}

function resetLsROI() {
    lsRoiPoints = [];
    drawROI(document.getElementById('ls-roi-canvas'), lsRoiImage, lsRoiPoints);
    checkLivestreamReady();
}

document.getElementById('ls-roi-canvas').addEventListener('click', (e) => {
    if (!lsRoiImage || livestreamActive) return;
    if (addRoiPoint(e.target, lsRoiPoints, e)) {
        drawROI(e.target, lsRoiImage, lsRoiPoints);
        checkLivestreamReady();
    }
});

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
        document.getElementById('btn-ls-connect').disabled = true;
    } else {
        dot.classList.remove('live');
        text.textContent = 'Livestream ready';
        btn.textContent = 'Start Livestream';
        btn.classList.remove('stop');
        document.getElementById('btn-ls-connect').disabled = false;
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
    const model = document.getElementById('ls-model-select').value;
    const realW = parseFloat(document.getElementById('ls-real-width').value);
    const realH = parseFloat(document.getElementById('ls-real-height').value);
    if (!model || lsRoiPoints.length !== ROI_MAX_POINTS || !(realW > 0) || !(realH > 0)) return;

    try {
        const res = await fetch('/api/livestream/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: model,
                save_video: saveVideo,
                roi: { points: lsRoiPoints, real_w: realW, real_h: realH },
            }),
        });
        const data = await res.json();
        if (res.ok) {
            setLivestreamUI(true);
            appendLog(data.message);
        } else {
            appendLog(`Livestream error: ${data.error}`);
        }
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
document.getElementById('ls-model-select').addEventListener('change', checkLivestreamReady);
document.getElementById('ls-real-width').addEventListener('input', checkLivestreamReady);
document.getElementById('ls-real-height').addEventListener('input', checkLivestreamReady);
connectLogs();
