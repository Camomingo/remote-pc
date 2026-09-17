import subprocess
import sys

required_packages = ['flask', 'pyautogui', 'mss', 'pillow']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

from flask import Flask, render_template_string, request, Response, jsonify
import pyautogui
import mss
import io
import time

app = Flask(__name__)
pyautogui.FAILSAFE = False

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Remote PC Control</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #222; color: #fff; }
        img { max-width: 80%; border: 2px solid #555; margin-top: 10px; cursor: crosshair; }
        #log { margin-top: 10px; color: #0ff; font-family: monospace; }
    </style>
</head>
<body>
    <h1>Controle PC distant</h1>
    <div>
        <img id="stream" src="/screenshot" onclick="handleClick(event)">
    </div>
    <div id="log">Clique sur l'image et tape sur ton clavier...</div>

    <script>
        // Rafraichissement de l'ecran
        setInterval(() => {
            document.getElementById('stream').src = '/screenshot?t=' + new Date().getTime();
        }, 1000);

        function handleClick(event) {
            const rect = event.target.getBoundingClientRect();
            const x = Math.round((event.clientX - rect.left) * (event.target.naturalWidth / rect.width));
            const y = Math.round((event.clientY - rect.top) * (event.target.naturalHeight / rect.height));
            
            fetch('/click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x: x, y: y })
            });
        }

        // Capture des touches du clavier pour les envoyer au PC distant
        window.addEventListener('keydown', (event) => {
            // Empeche le comportement par défaut du navigateur pour certaines touches (comme Tab)
            if (['Tab', 'Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
                event.preventDefault();
            }

            fetch('/key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: event.key })
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/screenshot')
def screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        from PIL import Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        io_buf = io.BytesIO()
        img.save(io_buf, format="JPEG", quality=70)
        io_buf.seek(0)
        return Response(io_buf.getvalue(), mimetype='image/jpeg')

@app.route('/click', methods=['POST'])
def click():
    data = request.get_json()
    if data and 'x' in data and 'y' in data:
        pyautogui.click(x=data['x'], y=data['y'])
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/key', methods=['POST'])
def press_key():
    data = request.get_json()
    key = data.get('key')
    
    if key:
        # Correspondance entre les touches JS et les commandes PyAutoGUI si besoin
        key_map = {
            "Enter": "enter",
            "Backspace": "backspace",
            "Tab": "tab",
            "Escape": "esc",
            " ": "space",
            "ArrowUp": "up",
            "ArrowDown": "down",
            "ArrowLeft": "left",
            "ArrowRight": "right",
            "Control": "ctrl",
            "Alt": "alt",
            "Meta": "win"  # Touche Windows
        }
        
        target_key = key_map.get(key, key)
        
        try:
            # Si c'est un seul caractere (lettre, chiffre), on utilise press()
            if len(target_key) == 1:
                pyautogui.press(target_key)
            else:
                pyautogui.press(target_key)
            return jsonify({"status": "success", "key": target_key})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
