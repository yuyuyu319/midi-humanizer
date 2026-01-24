import os
import io
import time
import random
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1100">
    <title>MIDI Tools</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent-green: #00e676; --accent-blue: #00b0ff; --accent-orange: #ff9100; --accent-purple: #d500f9; --accent-red: #ff5252; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin:0; line-height: 1.6; }
        .page-wrapper { display: flex; justify-content: center; align-items: flex-start; gap: 20px; padding: 40px 0; margin: 0 auto; width: 1080px; }
        .side-ad-left, .side-ad-right { width: 120px; }
        .main-content { flex: 1; max-width: 850px; min-width: 320px; }
        .card { background: var(--card); padding: 40px; border-radius: 24px; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        .tabs { display: flex; justify-content: center; gap: 8px; margin-bottom: 25px; }
        .tab-btn { padding: 12px 20px; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: #94a3b8; cursor: pointer; font-weight: bold; }
        .tab-btn.active.humanizer { background: var(--accent-green); color: black; }
        .tab-btn.active.normalizer { background: var(--accent-blue); color: white; }
        .tab-btn.active.limiter { background: var(--accent-orange); color: white; }
        .tab-btn.active.compressor { background: var(--accent-purple); color: white; }
        .tab-btn.active.expander { background: var(--accent-red); color: white; }
        .tool-panel, .info-panel { display: none; }
        .tool-panel.active, .info-panel.active { display: block; }
        h1 { font-size: 2.5rem; margin-bottom: 5px; font-weight: 800; text-align: center; }
        .subtitle { color: #94a3b8; margin-bottom: 25px; font-size: 1rem; text-align: center; }
        .form-group { margin: 20px auto; text-align: left; max-width: 400px; }
        label { display: block; font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 10px; font-size: 1.1rem; box-sizing: border-box; }
        button.process-btn { border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; max-width: 400px; font-size: 1.1rem; margin: 10px auto; display: block; transition: 0.2s; }
        
        .small-ad-row { display: flex; justify-content: center; gap: 8px; margin: 30px auto 15px; }
        .a8-large-banner-main { margin: 20px auto; text-align: center; }
        .a8-large-banner-main img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }

        .content-section { margin: 40px auto; text-align: left; background: rgba(30, 41, 59, 0.5); padding: 40px; border-radius: 20px; border: 1px solid #1e293b; }
        .content-section h2 { border-bottom: 2px solid #334155; padding-bottom: 10px; margin-top: 0; }
        
        .policy-section { margin: 60px auto 0; text-align: left; padding: 40px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.85rem; background: #0f172a; border-radius: 0 0 24px 24px; }
        .policy-section h2 { color: #f8fafc; font-size: 1.2rem; margin-top: 20px; border-left: 4px solid var(--accent-blue); padding-left: 10px; }
        
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; padding-bottom: 40px; text-align: center; }
        #preview-container { margin-top: 25px; display: none; text-align: left; }
        .scroll-wrapper { width: 100%; overflow-x: auto; background: #0f172a; border: 1px solid #334155; border-radius: 8px; }
        canvas { display: block; }
    </style>
</head>
<body>
<div class="page-wrapper">
    <aside class="side-ad-left">
        <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BFZZEA+2PEO+1I7QCH" rel="nofollow"><img border="0" width="120" height="600" src="https://www23.a8.net/svt/bgt?aid=260124628692&wid=001&eno=01&mid=s00000012624009106000&mc=1"></a>
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
                </div>
                <div id="normalizer-panel" class="tool-panel">
                    <h1>Normalizer</h1><p class="subtitle">平均化と目標値への調整</p>
                    <div class="form-group" style="text-align: center;"><label><input type="checkbox" name="n_use_target" checked> 目標値を指定</label><input type="number" name="n_target_v" value="80"></div>
                </div>
                <div class="form-group"><label id="param1-label">設定項目1</label><input type="number" name="p1" value="20"></div>
                <div class="form-group"><label id="param2-label">設定項目2</label><input type="number" name="p2" value="5"></div>

                <div class="small-ad-row">
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A2L06Q+5IT8+5ZMCH" rel="nofollow"><img border="0" width="120" height="60" src="https://www28.a8.net/svt/bgt?aid=260124628609&wid=001&eno=01&mid=s00000025766001006000&mc=1"></a>
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BPIX2Q+55QO+609HT" rel="nofollow"><img border="0" width="120" height="60" src="https://www26.a8.net/svt/bgt?aid=260124628708&wid=001&eno=01&mid=s00000024072001009000&mc=1"></a>
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BFEJSI+4VFA+5ZEMP" rel="nofollow"><img border="0" width="120" height="60" src="https://www25.a8.net/svt/bgt?aid=260124628691&wid=001&eno=01&mid=s00000022735001005000&mc=1"></a>
                </div>

                <button type="submit" class="process-btn" id="dl-btn" style="background: var(--accent-green); color: black;">PROCESS & DOWNLOAD</button>

                <div class="a8-large-banner-main">
                    <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+A6R1F6+5KFA+63OY9" rel="nofollow">
                    <img border="0" width="936" height="120" src="https://www26.a8.net/svt/bgt?aid=260124628616&wid=001&eno=01&mid=s00000025975001025000&mc=1"></a>
                </div>

                <div id="preview-container">
                    <div class="scroll-wrapper" id="scroll-wrapper"><canvas id="piano-roll-canvas"></canvas></div>
                </div>
            </form>
        </div>

        <div class="content-section">
            <div id="humanizer-info" class="info-panel active"><h2>Humanizer の効果</h2><p>微細なタイミングと強弱の揺らぎを加え、生命感を生成します。</p></div>
            <div id="normalizer-info" class="info-panel"><h2>Normalizer の効果</h2><p>全体の平均音量を算出し、ダイナミクスを整えます。</p></div>
            </div>

        <div style="margin: 20px auto; text-align: center; opacity: 0.5;">
            <script src="https://adm.shinobi.jp/s/475f193df1f880db04b8d1f6299d0192"></script>
        </div>

        <div class="policy-section">
            <h2>プライバシーポリシー</h2>
            <p>当サイトはユーザーのプライバシーを保護します。MIDIファイルはメモリ内でのみ処理され保存されません。忍者AdMax、A8.net等の広告配信事業者がCookieを使用することがあります。</p>
        </div>
        <div class="footer-copy">&copy; 2026 MIDI Tools.</div>
    </main>

    <aside class="side-ad-right">
        <a href="https://px.a8.net/svt/ejp?a8mat=4AVDG4+BOC1V6+F14+6AC5D" rel="nofollow"><img border="0" width="120" height="600" src="https://www21.a8.net/svt/bgt?aid=260124628706&wid=001&eno=01&mid=s00000001948001056000&mc=1"></a>
    </aside>
</div>
<script>
    // JSロジック省略（前回の正常動作分を維持）
    function switchTab(type){
        document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
        document.querySelectorAll('.tool-panel').forEach(p=>p.classList.remove('active'));
        document.querySelectorAll('.info-panel').forEach(p=>p.classList.remove('active'));
        document.querySelector('.tab-btn.'+type).classList.add('active');
        document.getElementById(type+'-panel').classList.add('active');
        document.getElementById(type+'-info').classList.add('active');
        document.getElementById('tool_type').value=type;
        const colors={humanizer:'#00e676',normalizer:'#00b0ff',limiter:'#ff9100',compressor:'#d500f9',expander:'#ff5252'};
        const btn=document.getElementById('dl-btn');
        btn.style.background=colors[type];
        btn.style.color=(type==='humanizer')?'black':'white';
        
        // パラメータラベル変更
        const labels = {
            humanizer: ['ベロシティ揺れ幅 (± 0-50)', 'タイミング揺れ幅 (%)'],
            normalizer: ['圧縮率 (%)', ''],
            limiter: ['最小値 (Min)', '最大値 (Max)'],
            compressor: ['スレッショルド', 'レシオ'],
            expander: ['スレッショルド', 'レシオ']
        };
        document.getElementById('param1-label').innerText = labels[type][0];
        document.getElementById('param2-label').innerText = labels[type][1];
    }
    // ...描画ロジック等...
</script>
</body>
</html>
"""

@app.route('/')
def index(): return make_response(HTML_PAGE)

@app.route('/process', methods=['POST'])
def process():
    # サーバーサイド処理（前回同様）
    return "Dummy Output" # 実際はsend_file等

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
