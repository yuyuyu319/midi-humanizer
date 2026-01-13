import os
import io
import time
import random
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

# 全5サイトを繋ぎ、デザインを統一した最終形態
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Humanizer | DAW用高精度リズム揺らぎ付加ツール</title>
    <meta name="description" content="DAWの打ち込みに自然な人間味を与えるMIDI処理ツール。独自のスマート・クリッピング・ロジックにより、音切れを防ぎつつ音楽的なグルーヴを付加します。">
    
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4758959657594096"
     crossorigin="anonymous"></script>

    <style>
        :root { --accent: #00e676; --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; text-align: center; padding: 50px 20px; margin:0; line-height: 1.6; }
        .card { background: var(--card); padding: 40px; border-radius: 24px; max-width: 650px; margin: auto; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        h1 { color: var(--accent); font-size: 2.5rem; margin-bottom: 10px; font-weight: 800; }
        .subtitle { color: #94a3b8; margin-bottom: 30px; font-size: 1.1rem; }
        .form-group { margin-bottom: 25px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
        label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 8px; font-size: 1rem; box-sizing: border-box; transition: 0.3s; }
        input[type="number"]:focus { border-color: var(--accent); outline: none; }
        button { background: var(--accent); color: black; border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; margin-top: 20px; transition: 0.2s; box-shadow: 0 4px 6px -1px rgba(0,230,118,0.3); }
        button:hover { background: #00ff84; transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,230,118,0.4); }
        
        /* 相互リンク用スタイル：各ツールのカラーを反映 */
        .link-box { margin-top: 25px; padding-top: 20px; border-top: 1px solid #334155; font-size: 0.8rem; color: #94a3b8; }
        .link-box a { text-decoration: none; font-weight: bold; margin: 0 4px; display: inline-block; }
        .link-box a.normalizer { color: #00b0ff; } /* 青 */
        .link-box a.limiter { color: #ff9100; }    /* 橙 */
        .link-box a.compressor { color: #d500f9; } /* 紫 */
        .link-box a.expander { color: #ff5252; }   /* 赤 */

        .content-section { max-width: 700px; margin: 60px auto; text-align: left; background: rgba(30, 41, 59, 0.5); padding: 40px; border-radius: 20px; border: 1px solid #1e293b; }
        .content-section h2 { color: var(--accent); border-bottom: 2px solid #334155; padding-bottom: 10px; margin-top: 40px; }
        .tips { background: #0f172a; padding: 25px; border-radius: 12px; border-left: 5px solid var(--accent); margin: 20px 0; }
        .tips ul { padding-left: 20px; }
        
        .policy-section { max-width: 600px; margin: 80px auto 0; text-align: left; padding: 30px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.85rem; }
        .policy-section h2 { color: #f8fafc; font-size: 1.1rem; border-left: 4px solid var(--accent); padding-left: 10px; margin-bottom: 15px; }
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; padding-bottom: 40px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>MIDI Humanizer</h1>
        <p class="subtitle">打ち込みに、計算された音楽的な「揺らぎ」を。</p>
        <form action="/process" method="post" enctype="multipart/form-data">
            <div style="margin-bottom: 30px; border: 2px dashed #334155; padding: 20px; border-radius: 12px;">
                <input type="file" name="midi_file" accept=".mid,.midi" required style="color: #94a3b8;">
            </div>
            <div class="form-group">
                <label>ベロシティ揺れ幅 (± 0-50)</label>
                <input type="number" name="v_range" value="20" min="0" max="50">
            </div>
            <div class="form-group">
                <label>タイミング揺れ幅 (1拍に対する %)</label>
                <input type="number" name="t_percent" value="5" min="0" max="20">
            </div>
            <button type="submit">PROCESS & DOWNLOAD</button>
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
        <p>DAWでの完璧なグリッド入力は機械的な印象を与えます。本ツールは「強弱」と「タイミング」に微細なズレを加え、楽曲に自然なグルーヴと深みを与えます。</p>

        <h3>スマート・クリッピング・ロジック</h3>
        <p>タイミングをずらした結果、次のノートと重なってしまった場合、本ツールは先行するノートの長さを自動調整し、不自然な発音停止を防ぎます。</p>

        <div class="tips">
            <h3>推奨設定ガイド</h3>
            <ul>
                <li><strong>Kick / Snare:</strong> タイミング 2-3%, ベロシティ 15-20</li>
                <li><strong>Hi-Hats / Percussion:</strong> タイミング 4-6%, ベロシティ 25-35</li>
                <li><strong>Piano / Guitar:</strong> タイミング 3-5%, ベロシティ 20-30</li>
            </ul>
        </div>
    </div>

    <div class="policy-section">
        <h2>プライバシーポリシー</h2>
        <p><strong>データ処理：</strong>MIDIファイルはサーバーに保存されず、メモリ内で即座に処理されます。当サイトではGoogle AdSenseを利用しています。</p>
    </div>

    <div class="footer-copy">&copy; 2026 MIDI Humanizer. All rights reserved.</div>
</body>
</html>
"""

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
    file = request.files['midi_file']
    v_range = int(request.form.get('v_range', 20))
    t_percent = int(request.form.get('t_percent', 5))
    processed_midi = process_midi_logic(file, v_range, t_percent)
    filename = f"humanized_{int(time.time())}.mid"
    return send_file(processed_midi, as_attachment=True, download_name=filename, mimetype='audio/midi')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
