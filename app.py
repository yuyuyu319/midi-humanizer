import os
import io
import time
import random
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

# --- デザイン & コンテンツ & 広告入れ替えHTML ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1100">
    <title>MIDI Tools</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent-green: #00e676; --accent-blue: #00b0ff; --accent-orange: #ff9100; --accent-purple: #d500f9; --accent-red: #ff5252; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin:0; line-height: 1.6; }
        .page-wrapper { display: flex; justify-content: center; align-items: flex-start; gap: 20px; padding: 40px 0; margin: 0 auto; width: 1080px; }
        .side-ad-left, .side-ad-right { width: 120px; }
        .main-content { width: 700px; }
        .card { background: var(--card); padding: 30px; border-radius: 24px; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        .tabs { display: flex; justify-content: center; gap: 8px; margin-bottom: 25px; }
        .tab-btn { padding: 10px 15px; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: #94a3b8; cursor: pointer; font-weight: bold; }
        .tab-btn.active.humanizer { background: var(--accent-green); color: black; }
        .tab-btn.active.normalizer { background: var(--accent-blue); color: white; }
        .tab-btn.active.limiter { background: var(--accent-orange); color: white; }
        .tab-btn.active.compressor { background: var(--accent-purple); color: white; }
        .tab-btn.active.expander { background: var(--accent-red); color: white; }
        .tool-panel { display: none; }
        .tool-panel.active { display: block; }
        h1 { font-size: 2.2rem; margin-bottom: 5px; font-weight: 800; text-align: center; }
        .subtitle { color: #94a3b8; margin-bottom: 25px; font-size: 1rem; text-align: center; }
        .form-group { margin: 20px auto; text-align: left; max-width: 400px; }
        label { display: block; font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 10px; font-size: 1.1rem; box-sizing: border-box; }
        button.process-btn { border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; max-width: 400px; font-size: 1.1rem; margin: 10px auto; display: block; transition: 0.2s; }
        
        /* ボタンの真上に小さいやつ3つ */
        .small-ad-row { display: flex; justify-content: center; gap: 8px; margin: 30px auto 15px; }
        .small-ad-row img { border-radius: 4px; border: 1px solid #334155; }
        
        /* ボタンの真下にでかいやつ */
        .a8-large-banner-main { margin: 20px auto; text-align: center; }
        .a8-large-banner-main img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }

        #preview-container { margin-top: 25px; display: none; text-align: left; }
        .scroll-wrapper { width: 100%; overflow-x: auto; background: #0f172a; border: 1px solid #334155; border-radius: 8px; }
        canvas { display: block; }
        .footer-copy { margin-top: 30px; font-size: 0.75rem; color: #475569; padding-bottom: 30px; text-align: center; }
    </style>
</head>
<body>
<div class="page-wrapper">
    <aside class="side-ad-left">
        <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BFZZEA+2PEO+1I7QCH" rel="nofollow">
        <img border="0" width="120" height="600" src="https://www23.a8.net/svt/bgt?aid=260124628692&wid=001&eno=01&mid=s00000012624009106000&mc=1" alt=""></a>
    </aside>

    <main class="main-content">
        <div class="card">
            <div class="tabs">
                <button class="tab-btn active humanizer" onclick="switchTab('humanizer')">Humanizer</button>
                <button class="tab-btn normalizer" onclick="switchTab('normalizer')">Normalizer</button>
                <button class="tab-btn limiter" onclick="switchTab('limiter')">Limiter</button>
                <button class="tab-btn compressor" onclick="switchTab('compressor')">Compressor</button>
                <button class="tab-btn expander" onclick="switchTab('expander')">Expander</button>
            </div>
            <form action="/process" method="post" enctype="multipart/form-data">
                <input type="hidden" name="tool_type" id="tool_type" value="humanizer">
                <div style="margin-bottom: 20px; border: 2px dashed #334155; padding: 20px; border-radius: 12px; text-align: center;">
                    <input type="file" id="file-input" name="midi_file" accept=".mid,.midi" required style="color: #94a3b8;">
                </div>
                
                <div id="humanizer-panel" class="tool-panel active">
                    <h1>Humanizer</h1><p class="subtitle">自然なリズムの揺らぎと強弱を付加</p>
                    <div class="form-group"><label>ベロシティ揺れ幅 (± 0-50)</label><input type="number" name="h_v_range" value="20"></div>
                    <div class="form-group"><label>タイミング揺れ幅 (%)</label><input type="number" name="h_t_percent" value="5"></div>
                </div>
                <div id="normalizer-panel" class="tool-panel">
                    <h1>Normalizer</h1><p class="subtitle">平均化と目標値への調整</p>
                    <div class="form-group" style="text-align: center;"><label><input type="checkbox" name="n_use_target" checked> 目標値を指定</label><input type="number" name="n_target_v" value="80"></div>
                    <div class="form-group"><label>圧縮率 (%)</label><input type="number" name="n_norm_rate" value="50"></div>
                </div>
                <div id="limiter-panel" class="tool-panel">
                    <h1>Limiter</h1><p class="subtitle">ベロシティを一定範囲内に制限</p>
                    <div class="form-group"><label>最小値 (Min)</label><input type="number" name="l_min" value="40"></div>
                    <div class="form-group"><label>最大値 (Max)</label><input type="number" name="l_max" value="100"></div>
                </div>
                <div id="compressor-panel" class="tool-panel">
                    <h1>Compressor</h1><p class="subtitle">大きい音を比率で圧縮</p>
                    <div class="form-group"><label>スレッショルド (1-127)</label><input type="number" name="c_thresh" value="80"></div>
                    <div class="form-group"><label>レシオ (比率 1.0-10.0)</label><input type="number" name="c_ratio" value="2.0" step="0.1"></div>
                </div>
                <div id="expander-panel" class="tool-panel">
                    <h1>Expander</h1><p class="subtitle">小さい音をさらに減衰</p>
                    <div class="form-group"><label>スレッショルド (1-127)</label><input type="number" name="e_thresh" value="60"></div>
                    <div class="form-group"><label>レシオ (比率 1.0-10.0)</label><input type="number" name="e_ratio" value="1.5" step="0.1"></div>
                </div>

                <div class="small-ad-row">
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A2L06Q+5IT8+5ZMCH" rel="nofollow"><img border="0" width="120" height="60" src="https://www28.a8.net/svt/bgt?aid=260124628609&wid=001&eno=01&mid=s00000025766001006000&mc=1"></a>
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BPIX2Q+55QO+609HT" rel="nofollow"><img border="0" width="120" height="60" src="https://www26.a8.net/svt/bgt?aid=260124628708&wid=001&eno=01&mid=s00000024072001009000&mc=1"></a>
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BFEJSI+4VFA+5ZEMP" rel="nofollow"><img border="0" width="120" height="60" src="https://www25.a8.net/svt/bgt?aid=260124628691&wid=001&eno=01&mid=s00000022735001005000&mc=1"></a>
                </div>

                <button type="submit" class="process-btn" id="dl-btn" style="background: var(--accent-green); color: black;">PROCESS & DOWNLOAD</button>

                <div class="a8-large-banner-main">
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A6R1F6+5KFA+63OY9" rel="nofollow">
                    <img border="0" width="936" height="120" src="https://www26.a8.net/svt/bgt?aid=260124628616&wid=001&eno=01&mid=s00000025975001025000&mc=1" alt=""></a>
                </div>

                <div id="preview-container">
                    <div class="scroll-wrapper" id="scroll-wrapper"><canvas id="piano-roll-canvas"></canvas></div>
                </div>
            </form>
        </div>
        <div style="margin: 20px auto; text-align: center; opacity: 0.5;"><script src="https://adm.shinobi.jp/s/475f193df1f880db04b8d1f6299d0192"></script></div>
        <div class="footer-copy">&copy; 2026 MIDI Tools.</div>
    </main>

    <aside class="side-ad-right">
        <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BOC1V6+F14+6AC5D" rel="nofollow">
        <img border="0" width="120" height="600" src="https://www21.a8.net/svt/bgt?aid=260124628706&wid=001&eno=01&mid=s00000001948001056000&mc=1"></a>
    </aside>
</div>

<script>
    const toolTypeInput = document.getElementById('tool_type');
    function switchTab(type) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
        document.querySelector('.tab-btn.' + type).classList.add('active');
        document.getElementById(type + '-panel').classList.add('active');
        toolTypeInput.value = type;
        const colors = { humanizer: '#00e676', normalizer: '#00b0ff', limiter: '#ff9100', compressor: '#d500f9', expander: '#ff5252' };
        const btn = document.getElementById('dl-btn');
        btn.style.background = colors[type];
        btn.style.color = (type === 'humanizer') ? 'black' : 'white';
        draw();
    }

    const fileInput = document.getElementById('file-input');
    const canvas = document.getElementById('piano-roll-canvas');
    const ctx = canvas.getContext('2d');
    let notes = [];

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const buffer = await file.arrayBuffer();
        const view = new DataView(buffer);
        notes = [];
        for (let i = 0; i < view.byteLength - 2; i++) {
            if ((view.getUint8(i) & 0xF0) === 0x90) {
                const pitch = view.getUint8(i + 1);
                const vel = view.getUint8(i + 2);
                if (vel > 0) notes.push({ pitch, vel, rV: Math.random()*2-1, rT: Math.random()*2-1 });
            }
        }
        document.getElementById('preview-container').style.display = 'block';
        draw();
    });

    window.addEventListener('input', draw);

    function draw() {
        if (notes.length === 0) return;
        const type = toolTypeInput.value;
        const barWidth = 12; const pianoRollHeight = 120; const velocityLaneHeight = 80;
        canvas.width = 640; 
        canvas.height = pianoRollHeight + velocityLaneHeight + 10;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const colors = { humanizer: '#00e676', normalizer: '#00b0ff', limiter: '#ff9100', compressor: '#d500f9', expander: '#ff5252' };
        notes.forEach((n, i) => {
            let newV = n.vel; let offsetX = 0;
            if (type === 'humanizer') {
                newV += n.rV * (parseInt(document.querySelector('#humanizer-panel input[name="h_v_range"]').value) || 0);
                offsetX = n.rT * (parseInt(document.querySelector('#humanizer-panel input[name="h_t_percent"]').value) || 0) * 0.5;
            } else if (type === 'normalizer') {
                const rate = (parseInt(document.querySelector('#normalizer-panel input[name="n_norm_rate"]').value) || 0) / 100;
                const avg = notes.reduce((s, x) => s + x.vel, 0) / notes.length;
                newV = n.vel + (avg - n.vel) * rate;
                if (document.querySelector('#normalizer-panel input[name="n_use_target"]').checked) newV += (parseInt(document.querySelector('#normalizer-panel input[name="n_target_v"]').value) - avg);
            } else if (type === 'limiter') {
                newV = Math.max(parseInt(document.querySelector('#limiter-panel input[name="l_min"]').value), Math.min(parseInt(document.querySelector('#limiter-panel input[name="l_max"]').value), newV));
            } else if (type === 'compressor') {
                const th = parseInt(document.querySelector('#compressor-panel input[name="c_thresh"]').value);
                if (newV > th) newV = th + (newV - th) / parseFloat(document.querySelector('#compressor-panel input[name="c_ratio"]').value);
            } else if (type === 'expander') {
                const th = parseInt(document.querySelector('#expander-panel input[name="e_thresh"]').value);
                if (newV < th) newV = th - (th - newV) * parseFloat(document.querySelector('#expander-panel input[name="e_ratio"]').value);
            }
            newV = Math.max(1, Math.min(127, newV));
            const x = i * barWidth;
            ctx.fillStyle = '#334155'; ctx.fillRect(x, pianoRollHeight - (n.pitch/127)*pianoRollHeight, barWidth-2, 4);
            ctx.fillStyle = colors[type]; ctx.fillRect(x + offsetX, pianoRollHeight - (n.pitch/127)*pianoRollHeight, barWidth-2, 4);
            ctx.fillStyle = '#475569'; ctx.fillRect(x, canvas.height - (n.vel/127)*velocityLaneHeight, barWidth-2, (n.vel/127)*velocityLaneHeight);
            ctx.fillStyle = colors[type]; ctx.fillRect(x + offsetX, canvas.height - (newV/127)*velocityLaneHeight, barWidth-2, (newV/127)*velocityLaneHeight);
        });
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return make_response(HTML_PAGE)

@app.route('/process', methods=['POST'])
def process():
    tool = request.form.get('tool_type')
    file = request.files.get('midi_file')
    if not file: return "File missing", 400
    midi_stream = io.BytesIO(file.read())
    try: mid = mido.MidiFile(file=midi_stream)
    except: return "Invalid MIDI", 400
    if tool == 'humanizer':
        v_range = int(request.form.get('h_v_range', 20))
        t_percent = int(request.form.get('h_t_percent', 5))
        max_tick_shift = int(mid.ticks_per_beat * (t_percent / 100.0))
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    msg.velocity = max(1, min(127, msg.velocity + random.randint(-v_range, v_range)))
                    msg.time = max(0, msg.time + random.randint(-max_tick_shift, max_tick_shift))
    elif tool == 'normalizer':
        rate = int(request.form.get('n_norm_rate', 50)) / 100.0
        use_target = request.form.get('n_use_target') == 'on'
        target_v = int(request.form.get('n_target_v', 80))
        vels = [m.velocity for t in mid.tracks for m in t if m.type == 'note_on' and m.velocity > 0]
        if vels:
            avg_v = sum(vels) / len(vels)
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        cv = msg.velocity + (avg_v - msg.velocity) * rate
                        fv = cv + (target_v - avg_v) if use_target else cv
                        msg.velocity = max(1, min(127, int(fv)))
    elif tool == 'limiter':
        min_v, max_v = int(request.form.get('l_min', 40)), int(request.form.get('l_max', 100))
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    msg.velocity = max(min_v, min(max_v, msg.velocity))
    elif tool == 'compressor':
        th, ra = int(request.form.get('c_thresh', 80)), float(request.form.get('c_ratio', 2.0))
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.velocity > th: msg.velocity = int(th + (msg.velocity - th) / ra)
    elif tool == 'expander':
        th, ra = int(request.form.get('e_thresh', 60)), float(request.form.get('e_ratio', 1.5))
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.velocity < th: msg.velocity = max(1, int(th - (th - msg.velocity) * ra))
    out = io.BytesIO(); mid.save(file=out); out.seek(0)
    return send_file(out, as_attachment=True, download_name=f"{tool}_output.mid", mimetype='audio/midi')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
