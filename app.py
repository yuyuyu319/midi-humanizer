HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Humanizer Pro | DAW向け高精度リズム揺らぎ付加ツール</title>
    <meta name="description" content="DAWの打ち込みに音楽的な人間味を加えるMIDI処理ツール。ノートの重なりを自動解消する独自アルゴリズム搭載。">
    <style>
        :root { --accent: #00e676; --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; margin: 0; }
        .nav { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); padding: 1rem; text-align: center; border-bottom: 1px solid #334155; position: sticky; top: 0; }
        .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .main-card { background: var(--card); border-radius: 1.5rem; padding: 2.5rem; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); border: 1px solid #334155; }
        h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; background: linear-gradient(to right, #00e676, #00b0ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .drop-zone { border: 2px dashed #475569; padding: 3rem; border-radius: 1rem; margin: 2rem 0; cursor: pointer; transition: 0.3s; }
        .drop-zone:hover { border-color: var(--accent); background: rgba(0, 230, 118, 0.05); }
        .param-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
        .param-group { text-align: left; }
        label { font-size: 0.875rem; font-weight: 600; color: #94a3b8; display: block; margin-bottom: 0.5rem; }
        input[type="number"] { width: 100%; background: #0f172a; border: 1px solid #334155; color: white; padding: 0.75rem; border-radius: 0.5rem; font-size: 1rem; }
        button { width: 100%; background: var(--accent); color: #000; padding: 1rem; border-radius: 0.75rem; font-size: 1.125rem; font-weight: 700; border: none; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 6px -1px rgba(0,230,118,0.3); }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,230,118,0.4); }
        .features { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 4rem; text-align: left; }
        .feature-item h3 { color: var(--accent); margin-bottom: 0.5rem; }
        .feature-item p { font-size: 0.9rem; color: #94a3b8; }
        footer { margin-top: 5rem; padding: 2rem; border-top: 1px solid #334155; color: #64748b; font-size: 0.8rem; text-align: center; }
    </style>
</head>
<body>
    <div class="nav"><strong>MIDI Humanizer Pro</strong></div>
    
    <div class="container">
        <div class="main-card">
            <h1>Humanize Your Beat</h1>
            <p style="color: #94a3b8;">機械的な打ち込みに、高精度な音楽的揺らぎを。</p>
            
            <form action="/process" method="post" enctype="multipart/form-data">
                <div class="drop-zone" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" name="midi_file" accept=".mid,.midi" style="display:none" required>
                    <div id="fileName">MIDIファイルをドラッグ＆ドロップ、またはクリック</div>
                </div>
                
                <div class="param-grid">
                    <div class="param-group">
                        <label>ベロシティ揺れ幅 (±0-50)</label>
                        <input type="number" name="v_range" value="20">
                    </div>
                    <div class="param-group">
                        <label>タイミング揺れ幅 (1拍に対する%)</label>
                        <input type="number" name="t_percent" value="5">
                    </div>
                </div>
                
                <button type="submit">PROCESS & DOWNLOAD</button>
            </form>
            
            <p style="font-size: 0.75rem; color: #64748b; margin-top: 1.5rem;">※アップロードされたファイルは一時的にメモリ上で処理され、サーバーには一切保存されません。</p>
        </div>

        <div class="features">
            <div class="feature-item">
                <h3>Smart Clipping</h3>
                <p>ランダマイズによってノートが重なった場合、独自のアルゴリズムで自動的に先行ノートをカット。DAWでの音切れや消失を防ぎます。</p>
            </div>
            <div class="feature-item">
                <h3>True Randomness</h3>
                <p>すべてのノートに対して独立した乱数シードを使用。周期的でない、より人間に近い自然なグルーヴを生み出します。</p>
            </div>
            <div class="feature-item">
                <h3>Resolution Independent</h3>
                <p>MIDIファイルの解像度（TPQN）を自動判別。BPMや設定を問わず、常に意図した通りの揺らぎを付加します。</p>
            </div>
            <div class="feature-item">
                <h3>No Installation</h3>
                <p>ブラウザ完結型。プラグインやソフトウェアのインストールは不要。スマホからでも利用可能です。</p>
            </div>
        </div>

        <footer>
            &copy; 2026 MIDI Humanizer Pro. All Rights Reserved.<br>
            当サイトはMIDIの標準仕様に基づき、安全にファイルを処理します。
        </footer>
    </div>

    <script>
        const fileInput = document.getElementById('fileInput');
        const fileNameDisplay = document.getElementById('fileName');
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                fileNameDisplay.innerText = "選択済み: " + e.target.files[0].name;
                fileNameDisplay.style.color = "#00e676";
            }
        });
    </script>
</body>
</html>
"""