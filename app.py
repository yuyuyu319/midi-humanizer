import os
import io
import time
import random
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

# --- デザイン & コンテンツ & ピアノロールプレビュー統合HTML ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Humanizer | ピアノロール・プレビュー付リズム揺らぎ付加ツール</title>
    <meta name="description" content="DAWの打ち込みに自然な人間味を与えるMIDI処理ツール。ピアノロールとベロシティレーンのダブルプレビューで、揺らぎの具合をリアルタイムに確認できます。">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4758959657594096" crossorigin="anonymous"></script>
    <style>
        :root { --accent: #00e676; --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; text-align: center; padding: 50px 20px; margin:0; line-height: 1.6; }
        .card { background: var(--card); padding: 40px; border-radius: 24px; max-width: 750px; margin: auto; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        h1 { color: var(--accent); font-size: 2.5rem; margin-bottom: 10px; font-weight: 800; }
        .subtitle { color: #94a3b8; margin-bottom: 30px; font-size: 1.1rem; }
        .form-group { margin: 25px 0; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
        label { display: block; font-size: 0.9rem; color: #94a3b8; margin-bottom: 10px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 15px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 10px; font-size: 1.2rem; box-sizing: border-box; transition: 0.3s; }
        button { background: var(--accent); color: black; border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; margin-top: 20px; transition: 0.2s; }
        button:hover { background: #00ff84; transform: translateY(-2px); }

        /* プレビューエリア */
        #preview-container { margin-top: 30px; display: none; text-align: left; }
        .scroll-wrapper { width: 100%; overflow-x: auto; background: #0f172a; border: 1px solid #334155; border-radius: 8px; }
        canvas { display: block; }
        .legend { display: flex; justify-content: center; gap: 20px; font-size: 0.8rem; margin: 15px 0; color: #94a3b8; }
        .legend-item span { display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 5px; }
        
        .link-box { margin-top: 25px; padding-top: 20px; border-top: 1px solid #334155; font-size: 0.8rem; color: #94a3b8; }
        .link-box a { text-decoration: none; font-weight: bold; margin: 0 4px; display: inline-block; }
        .link-box a.normalizer { color: #00b0ff; } .link-box a.limiter { color: #ff9100; }
        .link-box a.compressor { color: #d500f9; } .link-box a.expander { color: #ff5252; }

        .content-section { max-width: 850px; margin: 60px auto; text-align: left; background: rgba(30, 41, 59, 0.5); padding: 40px; border-radius: 20px; border: 1px solid #1e293b; }
        .content-section h2 { color: var(--accent); border-bottom: 2px solid #334155; padding-bottom: 10px; margin-top: 40px; }
        .policy-section { max-width: 850px; margin: 80px auto 0; text-align: left; padding: 30px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.85rem; }
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; padding-bottom: 40px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>MIDI Humanizer</h1>
        <p class="subtitle">打ち込みに、自然な人間味を。</p>
        <form action="/process" method="post" enctype="multipart/form-data">
            <div style="margin-bottom: 25px; border: 2px dashed #334155; padding: 20px; border-radius: 12px;">
                <input type="file" id="file-input" name="midi_file" accept=".mid,.midi" required style="color: #94a3b8;">
            </div>
            <div class="form-group">
                <label>ベロシティ揺れ幅 (± 0-50)</label>
                <input type="number" name="v_range" id="v_range" value="20" min="0" max="50">
            </div>
            <div class="form-group">
                <label>タイミング揺れ幅 (1拍に対する %)</label>
                <input type="number" name="t_percent" id="t_percent" value="5" min="0" max="20">
            </div>

            <div id="preview-container">
                <div class="legend">
                    <div class="legend-item"><span style="background: #475569;"></span>元の位置/強さ</div>
                    <div class="legend-item"><span style="background: var(--accent);"></span>Humanize後</div>
                </div>
                <div class="scroll-wrapper" id="scroll-wrapper">
                    <canvas id="piano-roll-canvas"></canvas>
                </div>
            </div>

            <button type="submit">HUMANIZE & DOWNLOAD</button>
        </form>
        <div class="link-box">
            関連ツール: 
            <a href="https://midi-normalizer.onrender.com/" class="normalizer">Normalizer</a> | 
            <a href="https://midi-limiter.onrender.com/" class="limiter">Limiter</a> | 
            <a href="https://midi-compressor.onrender.com/" class="compressor">Compressor</a> | 
            <a href="https://midi-expander.onrender.com/" class="expander">Expander</a>
        </div>
    </div>

    <div class="content-section">
        <h2>なぜMIDIヒューマナイズが必要なのか？</h2>
        <p>完璧すぎるリズムと一定の音量は、楽曲に機械的な印象を与えます。本ツールは、人間が演奏した際に生じる微細な「ズレ」をシミュレートし、自然なグルーヴを付加します。</p>
        <h3>ビジュアル・プレビュー</h3>
        <p>上段にはノートの音程、下段にはベロシティを表示。設定を動かすと、ノートが左右に揺れ、音量が上下する様子をリアルタイムに確認できます。</p>
    </div>

    <div class="policy-section">
        <h2>プライバシーポリシー</h2>
        <p><strong>データ処理：</strong>アップロードされたファイルはメモリ内で即座に処理され、保存されません。プライバシーは完全に守られます。</p>
        <p><strong>広告配信：</strong>Google AdSense等により広告を配信する場合があります。</p>
    </div>
    <div class="footer-copy">&copy; 2026 MIDI Humanizer. All rights reserved.</div>

    <script>
        const fileInput = document.getElementById('file-input');
        const canvas = document.getElementById('piano-roll-canvas');
        const ctx = canvas.getContext('2d');
        const vRangeInput = document.getElementById('v_range');
        const tPercentInput = document.getElementById('t_percent');
        let notes = []; // {pitch, vel, randomV, randomT}

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
                    if (vel > 0) {
                        notes.push({
                            pitch, vel,
                            randomV: Math.random() * 2 - 1, // -1 to 1
                            randomT: Math.random() * 2 - 1  // -1 to 1
                        });
                    }
                }
            }
            document.getElementById('preview-container').style.display = 'block';
            draw();
        });

        [vRangeInput, tPercentInput].forEach(el => el.addEventListener('input', draw));

        function draw() {
            if (notes.length === 0) return;
            const barWidth = 12;
            const pianoRollHeight = 120;
            const velocityLaneHeight = 80;
            const margin = 10;
            
            canvas.width = Math.max(document.getElementById('scroll-wrapper').clientWidth, notes.length * barWidth);
            canvas.height = pianoRollHeight + velocityLaneHeight + margin;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const vRange = parseInt(vRangeInput.value);
            const tRange = parseInt(tPercentInput.value) * 0.5; // 可視化用に調整

            notes.forEach((n, i) => {
                // タイミングのズレをX軸に反映
                const offsetX = n.randomT * tRange;
                const xOrig = i * barWidth;
                const xNew = xOrig + offsetX;
                
                // 上段: ピアノロール
                const yPitch = pianoRollHeight - (n.pitch / 127) * pianoRollHeight;
                ctx.fillStyle = '#334155';
                ctx.fillRect(xOrig, yPitch, barWidth - 2, 4); // 元の位置
                ctx.fillStyle = '#00e676';
                ctx.fillRect(xNew, yPitch, barWidth - 2, 4);  // ズレた位置

                // 下段: ベロシティ
                const laneBaseY = canvas.height;
                const hOrig = (n.vel / 127) * velocityLaneHeight;
                ctx.fillStyle = '#475569';
                ctx.fillRect(xOrig, laneBaseY - hOrig, barWidth - 2, hOrig);

                const newV = Math.max(1, Math.min(127, n.vel + (n.randomV * vRange)));
                const hNew = (newV / 127) * velocityLaneHeight;
                ctx.fillStyle = '#00e676';
                ctx.fillRect(xNew, laneBaseY - hNew, barWidth - 2, hNew);
            });

            ctx.strokeStyle = '#334155';
            ctx.setLineDash([]);
            ctx.beginPath(); ctx.moveTo(0, pianoRollHeight); ctx.lineTo(canvas.width, pianoRollHeight); ctx.stroke();
        }
    </script>
</body>
</html>
"""

# --- サーバーサイド処理 ---
def process_midi_logic(midi_file_stream, v_range, t_percent):
    midi_file_stream.seek(0)
    input_data = io.BytesIO(midi_file_stream.read())
    try:
        mid = mido.MidiFile(file=input_data)
    except: return None
    new_mid = mido.MidiFile()
    new_mid.ticks_per_beat = mid.ticks_per_beat
    max_tick_shift = int(mid.ticks_per_beat * (t_percent / 100.0))
    MIN_GAP = 1 
    for track in mid.tracks:
        abs_time = 0
        pending = {}; notes_by_key = {}; others = []
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.channel, msg.note)
                ts, vs = random.randint(-max_tick_shift, max_tick_shift), random.randint(-v_range, v_range)
                if key not in pending: pending[key] = []
                pending[key].append({'t': abs_time, 'ts': ts, 'vs': vs, 'm': msg.copy()})
            elif msg.type in ['note_off'] or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in pending and pending[key]:
                    p = pending[key].pop(0)
                    if key not in notes_by_key: notes_by_key[key] = []
                    notes_by_key[key].append({'orig_on': p['t'], 'on': p['t'] + p['ts'], 'off': abs_time + p['ts'], 'vs': p['vs'], 'm_on': p['m'], 'm_off': msg.copy()})
                else: others.append({'abs': abs_time, 'm': msg.copy()})
            else: others.append({'abs': abs_time, 'm': msg.copy()})
        final_events = []
        for key, note_list in notes_by_key.items():
            note_list.sort(key=lambda x: x['orig_on'])
            for i in range(len(note_list)):
                n = note_list[i]
                n['m_on'].velocity = max(1, min(127, n['m_on'].velocity + n['vs']))
                if i + 1 < len(note_list):
                    next_on = note_list[i+1]['on']
                    if n['off'] >= next_on: n['off'] = next_on - MIN_GAP
                if n['off'] <= n['on']: n['off'] = n['on'] + 2
                final_events.append({'abs': int(n['on']), 'pri': 1, 'm': n['m_on']})
                final_events.append({'abs': int(n['off']), 'pri': 0, 'm': n['m_off']})
        for o in others: final_events.append({'abs': int(o['abs']), 'pri': 2, 'm': o['m']})
        final_events.sort(key=lambda x: (x['abs'], x['pri']))
        new_track = mido.MidiTrack()
        cur = 0
        for e in final_events:
            e['m'].time = int(max(0, e['abs'] - cur))
            new_track.append(e['m'])
            cur = e['abs']
        new_mid.tracks.append(new_track)
    output = io.BytesIO()
    new_mid.save(file=output)
    output.seek(0)
    return output

@app.route('/')
def index():
    response = make_response(HTML_PAGE)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/process', methods=['POST'])
def process():
    file = request.files.get('midi_file')
    v_range = int(request.form.get('v_range', 20))
    t_percent = int(request.form.get('t_percent', 5))
    processed_midi = process_midi_logic(file, v_range, t_percent)
    filename = f"humanized_{int(time.time())}.mid"
    return send_file(processed_midi, as_attachment=True, download_name=filename, mimetype='audio/midi')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
