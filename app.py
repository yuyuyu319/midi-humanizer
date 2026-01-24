import os
import io
import time
import random
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

# --- デザイン & コンテンツ & A8優先レイアウトHTML ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Tools</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent-green: #00e676; --accent-blue: #00b0ff; --accent-orange: #ff9100; --accent-purple: #d500f9; --accent-red: #ff5252; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; text-align: center; padding: 50px 20px; margin:0; line-height: 1.6; }
        .card { background: var(--card); padding: 40px; border-radius: 24px; max-width: 850px; margin: auto; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        .tabs { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 30px; }
        .tab-btn { padding: 12px 20px; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: #94a3b8; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .tab-btn.active.humanizer { background: var(--accent-green); color: black; border-color: var(--accent-green); }
        .tab-btn.active.normalizer { background: var(--accent-blue); color: white; border-color: var(--accent-blue); }
        .tab-btn.active.limiter { background: var(--accent-orange); color: white; border-color: var(--accent-orange); }
        .tab-btn.active.compressor { background: var(--accent-purple); color: white; border-color: var(--accent-purple); }
        .tab-btn.active.expander { background: var(--accent-red); color: white; border-color: var(--accent-red); }
        .tool-panel, .info-panel { display: none; }
        .tool-panel.active, .info-panel.active { display: block; }
        h1 { font-size: 2.5rem; margin-bottom: 10px; font-weight: 800; }
        .subtitle { color: #94a3b8; margin-bottom: 30px; font-size: 1.1rem; }
        .form-group { margin: 25px 0; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
        label { display: block; font-size: 0.9rem; color: #94a3b8; margin-bottom: 10px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 15px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 10px; font-size: 1.2rem; box-sizing: border-box; }
        
        /* メインのダウンロードボタン */
        button.process-btn { border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; max-width: 400px; font-size: 1.1rem; margin-top: 10px; transition: 0.2s; }
        button.process-btn:hover { transform: translateY(-2px); opacity: 0.9; }

        /* A8大バナー（目立たせる） */
        .a8-large-banner { margin: 50px auto; max-width: 936px; width: 100%; border: 2px solid #334155; border-radius: 12px; padding: 10px; background: rgba(255,255,255,0.05); }
        .a8-large-banner img { max-width: 100%; height: auto; display: block; margin: 0 auto; }

        /* A8小バナー（ボタンの上に配置） */
        .a8-small-banner { margin: 25px auto 10px; display: block; }
        .a8-small-banner img { border-radius: 4px; }

        /* 忍者AdMax（控えめにフッター上へ） */
        .ninja-area { margin: 40px auto; opacity: 0.6; transition: 0.3s; }
        .ninja-area:hover { opacity: 1; }

        #preview-container { margin-top: 30px; display: none; text-align: left; }
        .scroll-wrapper { width: 100%; overflow-x: auto; background: #0f172a; border: 1px solid #334155; border-radius: 8px; }
        canvas { display: block; }
        .legend { display: flex; justify-content: center; gap: 20px; font-size: 0.8rem; margin: 15px 0; color: #94a3b8; }
        .legend-item span { display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 5px; }
        .content-section { max-width: 850px; margin: 40px auto; text-align: left; background: rgba(30, 41, 59, 0.5); padding: 40px; border-radius: 20px; border: 1px solid #1e293b; }
        .policy-section { max-width: 850px; margin: 60px auto 0; text-align: left; padding: 30px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.85rem; }
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; padding-bottom: 40px; }
    </style>
</head>
<body>
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
            <div style="margin-bottom: 25px; border: 2px dashed #334155; padding: 20px; border-radius: 12px;"><input type="file" id="file-input" name="midi_file" accept=".mid,.midi" required style="color: #94a3b8;"></div>
            
            <div id="humanizer-panel" class="tool-panel active">
                <h1>Humanizer</h1><p class="subtitle">自然なリズムの揺らぎと強弱を付加。</p>
                <div class="form-group"><label>ベロシティ揺れ幅 (± 0-50)</label><input type="number" name="h_v_range" value="20"></div>
                <div class="form-group"><label>タイミング揺れ幅 (%)</label><input type="number" name="h_t_percent" value="5"></div>
            </div>
            <div id="normalizer-panel" class="tool-panel">
                <h1>Normalizer</h1><p class="subtitle">平均化と目標値への調整。</p>
                <div class="form-group" style="text-align: center;"><label><input type="checkbox" name="n_use_target" checked> 目標値を指定</label><input type="number" name="n_target_v" value="80"></div>
                <div class="form-group"><label>圧縮率 (%)</label><input type="number" name="n_norm_rate" value="50"></div>
            </div>
            <div id="limiter-panel" class="tool-panel">
                <h1>Limiter</h1><p class="subtitle">ベロシティを一定範囲内に制限。</p>
                <div class="form-group"><label>最小値 (Min)</label><input type="number" name="l_min" value="40"></div>
                <div class="form-group"><label>最大値 (Max)</label><input type="number" name="l_max" value="100"></div>
            </div>
            <div id="compressor-panel" class="tool-panel">
                <h1>Compressor</h1><p class="subtitle">大きい音を比率で圧縮。</p>
                <div class="form-group"><label>スレッショルド (1-127)</label><input type="number" name="c_thresh" value="80"></div>
                <div class="form-group"><label>レシオ (比率 1.0-10.0)</label><input type="number" name="c_ratio" value="2.0" step="0.1"></div>
            </div>
            <div id="expander-panel" class="tool-panel">
                <h1>Expander</h1><p class="subtitle">小さい音をさらに減衰。</p>
                <div class="form-group"><label>スレッショルド (1-127)</label><input type="number" name="e_thresh" value="60"></div>
                <div class="form-group"><label>レシオ (比率 1.0-10.0)</label><input type="number" name="e_ratio" value="1.5" step="0.1"></div>
            </div>

            <div class="a8-small-banner">
                <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A2L06Q+5IT8+5ZMCH" rel="nofollow">
                <img border="0" width="120" height="60" alt="" src="https://www28.a8.net/svt/bgt?aid=260124628609&wid=001&eno=01&mid=s00000025766001006000&mc=1"></a>
                <img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4AVDG4+A2L06Q+5IT8+5ZMCH" alt="">
            </div>

            <button type="submit" class="process-btn" style="background: var(--accent-green); color: black;">PROCESS & DOWNLOAD</button>

            <div id="preview-container">
                <div class="legend">
                    <div class="legend-item"><span style="background: #475569;"></span>元の値</div>
                    <div class="legend-item"><span id="legend-after-color" style="background: var(--accent-green);"></span>処理後</div>
                </div>
                <div class="scroll-wrapper" id="scroll-wrapper"><canvas id="piano-roll-canvas"></canvas></div>
            </div>
        </form>
    </div>

    <div class="a8-large-banner">
        <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A6R1F6+5KFA+63OY9" rel="nofollow">
        <img border="0" width="936" height="120" alt="" src="https://www26.a8.net/svt/bgt?aid=260124628616&wid=001&eno=01&mid=s00000025975001025000&mc=1"></a>
        <img border="0" width="1" height="1" src="https://www19.a8.net/0.gif?a8mat=4AVDG4+A6R1F6+5KFA+63OY9" alt="">
    </div>

    <div class="content-section">
        <div id="humanizer-info" class="info-panel active"><h2>Humanizer の効果</h2><p>微細な「強弱のムラ」と「タイミングのズレ」をシミュレートし、自然な生命力を付加します。</p></div>
        <div id="normalizer-info" class="info-panel"><h2>Normalizer の効果</h2><p>全体の平均値を算出し、音楽的なニュアンスを保ったまま音量を整えます。</p></div>
        <div id="limiter-info" class="info-panel"><h2>Limiter の効果</h2><p>強すぎる音を抑え、弱すぎる音を底上げしてミックスを安定させます。</p></div>
        <div id="compressor-info" class="info-panel"><h2>Compressor の効果</h2><p>超過分を「比率」で減衰させ、演奏のニュアンスを守りつつピークを抑えます。</p></div>
        <div id="expander-info" class="info-panel"><h2>Expander の効果</h2><p>小さい音をさらに減衰させ、トラックにキレとメリハリを与えます。</p></div>
    </div>

    <div class="ninja-area">
        <script src="https://adm.shinobi.jp/s/475f193df1f880db04b8d1f6299d0192"></script>
    </div>

    <div class="policy-section">
        <h2>プライバシーポリシー</h2>
        <p>MIDIファイルはサーバーに保存されず、メモリ内で即座に処理されます。</p>
        <p>当サイトでは第三者配信事業者がCookieを利用して広告を配信する場合があります。</p>
    </div>
    <div class="footer-copy">&copy; 2026 MIDI Tools.</div>

    <script>
        const fileInput = document.getElementById('file-input');
        const canvas = document.getElementById('piano-roll-canvas');
        const ctx = canvas.getContext('2d');
        const toolTypeInput = document.getElementById('tool_type');
        let notes = [];
        function switchTab(type) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.info-panel').forEach(p => p.classList.remove('active'));
            document.querySelector('.tab-btn.' + type).classList.add('active');
            document.getElementById(type + '-panel').classList.add('active');
            document.getElementById(type + '-info').classList.add('active');
            toolTypeInput.value = type;
            const colors = { humanizer: '#00e676', normalizer: '#00b0ff', limiter: '#ff9100', compressor: '#d500f9', expander: '#ff5252' };
            const btn = document.querySelector('.process-btn');
            btn.style.background = colors[type];
            btn.style.color = (type === 'humanizer') ? 'black' : 'white';
            document.getElementById('legend-after-color').style.background = colors[type];
            draw();
        }
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
            canvas.width = Math.max(document.getElementById('scroll-wrapper').clientWidth, notes.length * barWidth);
            canvas.height = pianoRollHeight + velocityLaneHeight + 10;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const colors = { humanizer: '#00e676', normalizer: '#00b0ff', limiter: '#ff9100', compressor: '#d500f9', expander: '#ff5252' };
            notes.forEach((n, i) => {
                let newV = n.vel; let offsetX = 0;
                if (type === 'humanizer') {
                    newV += n.rV * parseInt(document.querySelector('#humanizer-panel input[name="h_v_range"]').value);
                    offsetX = n.rT * parseInt(document.querySelector('#humanizer-panel input[name="h_t_percent"]').value) * 0.5;
                } else if (type === 'normalizer') {
                    const rate = parseInt(document.querySelector('#normalizer-panel input[name="n_norm_rate"]').value) / 100;
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
            ctx.strokeStyle = '#334155'; ctx.beginPath(); ctx.moveTo(0, pianoRollHeight); ctx.lineTo(canvas.width, pianoRollHeight); ctx.stroke();
        }
    </script>
</body>
</html>
"""

# --- 以下、Flask処理ロジックは変更なし ---
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
