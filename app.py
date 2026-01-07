from flask import Flask, request, send_file, make_response
import mido
import io
import random
import time

app = Flask(__name__)

# --- デザイン（HTML）をここに内蔵 ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>MIDI Humanizer Online</title>
    <style>
        body { background: #1a1a1a; color: #e0e0e0; font-family: sans-serif; text-align: center; padding: 50px; }
        .container { background: #2d2d2d; border-radius: 15px; padding: 40px; width: 400px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .box { border: 2px dashed #555; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .param { margin: 15px 0; text-align: left; }
        label { display: block; font-size: 0.9em; color: #aaa; }
        input[type="number"] { background: #444; border: 1px solid #555; color: white; padding: 8px; border-radius: 5px; width: 100%; box-sizing: border-box; }
        button { background: #81C995; color: #121212; border: none; border-radius: 8px; padding: 15px 30px; font-weight: bold; cursor: pointer; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MIDI Humanizer</h1>
        <form action="/process" method="post" enctype="multipart/form-data">
            <div class="box"><input type="file" name="midi_file" required></div>
            <div class="param">
                <label>ベロシティ揺れ幅 (0-50):</label>
                <input type="number" name="v_range" value="20">
            </div>
            <div class="param">
                <label>タイミング揺れ幅 (1拍に対する%):</label>
                <input type="number" name="t_percent" value="5">
            </div>
            <button type="submit">ランダマイズして保存</button>
        </form>
    </div>
</body>
</html>
"""

def process_midi_logic(midi_file_stream, v_range, t_percent):
    midi_file_stream.seek(0)
    input_data = io.BytesIO(midi_file_stream.read())
    try:
        mid = mido.MidiFile(file=input_data)
    except:
        return None
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
    # ファイルを介さず文字列としてHTMLを返す
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
    # ポートを少し変えて、古いキャッシュから逃げます
    app.run(debug=True, port=5001)