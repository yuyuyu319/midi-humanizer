HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Humanizer Pro | DAW用高精度リズム揺らぎ付加ツール</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 50px 20px; margin:0; }
        .card { background: #1e293b; padding: 40px; border-radius: 24px; max-width: 600px; margin: auto; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        h1 { color: #00e676; font-size: 2.5rem; margin-bottom: 10px; }
        p.subtitle { color: #94a3b8; margin-bottom: 30px; }
        .form-group { margin-bottom: 25px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
        label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px; }
        input[type="number"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }
        button { background: #00e676; color: black; border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; margin-top: 20px; transition: 0.2s; }
        button:hover { background: #00ff84; transform: translateY(-2px); }
        
        /* ポリシーセクション */
        .policy-section { max-width: 600px; margin: 60px auto 0; text-align: left; padding: 30px; border-top: 1px solid #334155; color: #94a3b8; font-size: 0.85rem; line-height: 1.8; }
        .policy-section h2 { color: #f8fafc; font-size: 1.1rem; margin-bottom: 15px; border-left: 4px solid #00e676; padding-left: 10px; }
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; }
    </style>
</head>
<body>
    <div class="card">
        <h1>MIDI Humanizer Pro</h1>
        <p class="subtitle">打ち込みに、計算された音楽的な「揺らぎ」を。</p>
        
        <form action="/process" method="post" enctype="multipart/form-data">
            <div style="margin-bottom: 30px;">
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
    </div>

    <div class="policy-section">
        <h2>プライバシーポリシー</h2>
        <p>
            <strong>データ処理について：</strong><br>
            当ツールでアップロードされたMIDIファイルは、サーバー上のメモリ内で一時的に処理され、即座にユーザーへ返送されます。当サーバー内にファイルが保存されたり、第三者へ提供されたりすることは一切ありません。
        </p>
        <p>
            <strong>広告について：</strong><br>
            当サイトでは、Google等の第三者配信事業者がCookieを使用して、ユーザーが当サイトや他のサイトに過去にアクセスした際の情報に基づいて広告を配信する場合があります。ユーザーは、Googleの広告設定でパーソナライズ広告を無効にできます。
        </p>
        <p>
            <strong>免責事項：</strong><br>
            当ツールの利用により生じた直接的、間接的な損害について、開発者は一切の責任を負いません。
        </p>
    </div>

    <div class="footer-copy">
        &copy; 2026 MIDI Humanizer Pro. All rights reserved.
    </div>
</body>
</html>
"""
