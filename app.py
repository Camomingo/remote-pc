import io
from flask import Flask, render_template_string, Response, request
import pyautogui
from mss import mss
from PIL import Image

app = Flask(__name__)

# Désactive le frein de sécurité PyAutoGUI
pyautogui.FAILSAFE = False

# Flux vidéo de l'écran en direct
def generate_screen():
    with mss() as sct:
        monitor = sct.monitors[1]
        while True:
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.thumbnail((800, 600))
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=45)
            frame = buffer.getvalue()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Télécommande PC + Touchpad</title>
    <style>
        * { box-sizing: border-box; touch-action: manipulation; user-select: none; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: #121212; 
            color: #ffffff; 
            margin: 0; 
            padding: 10px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
        }
        
        .screen-container {
            width: 100%;
            max-width: 500px;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            border: 2px solid #333;
            margin-bottom: 10px;
        }
        .screen-container img { width: 100%; height: auto; display: block; }

        .container { width: 100%; max-width: 500px; display: flex; flex-direction: column; gap: 10px; }
        .section-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 3px; }
        
        /* Zone Tactile / Touchpad */
        #touchpad {
            width: 100%;
            height: 140px;
            background: #1e1e1e;
            border: 2px dashed #444;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 0.9rem;
            touch-action: none; /* Empêche le défilement de la page */
        }

        .grid { display: flex; flex-direction: column; gap: 6px; }
        .row { display: flex; justify-content: center; gap: 6px; width: 100%; }
        
        button { 
            flex: 1; 
            height: 42px; 
            font-size: 0.9rem; 
            font-weight: bold; 
            border-radius: 8px; 
            border: none; 
            background: #2a2a2a; 
            color: #ffffff; 
            display: flex;
            align-items: center;
            justify-content: center;
        }
        button:active { background: #007bff; }
        .btn-win { background: #0078d4; }
        .btn-action { background: #3a3a3a; }
        .btn-danger { background: #d9534f; }
        .btn-space { flex: 2; }
    </style>
</head>
<body>

    <!-- Écran en direct -->
    <div class="screen-container">
        <img src="/video_feed" alt="Écran PC">
    </div>

    <div class="container">
        
        <!-- Pavé Tactile -->
        <div>
            <div class="section-title">Pavé Tactile (Souris)</div>
            <div id="touchpad">Glissez pour bouger la souris | Tapez pour cliquer</div>
            <div class="row" style="margin-top: 5px;">
                <button class="btn-action" onclick="sendMouseClick('left')">Clic Gauche</button>
                <button class="btn-action" onclick="sendMouseClick('right')">Clic Droit</button>
            </div>
        </div>

        <!-- Navigation -->
        <div>
            <div class="section-title">Clavier & Navigation</div>
            <div class="grid">
                <div class="row">
                    <button class="btn-win" onclick="send('win')">❖ Win</button>
                    <button onclick="send('up')">▲</button>
                    <button class="btn-danger" onclick="send('backspace')">⌫</button>
                </div>
                <div class="row">
                    <button onclick="send('left')">◀</button>
                    <button class="btn-action" onclick="send('enter')">⏎ OK</button>
                    <button onclick="send('right')">▶</button>
                </div>
                <div class="row">
                    <button class="btn-action" onclick="send('esc')">Esc</button>
                    <button onclick="send('down')">▼</button>
                    <button class="btn-space" onclick="send('space')">Espace</button>
                </div>
            </div>
        </div>

        <!-- Clavier AZERTY -->
        <div>
            <div class="grid">
                <div class="row">
                    <button onclick="send('a')">A</button><button onclick="send('z')">Z</button>
                    <button onclick="send('e')">E</button><button onclick="send('r')">R</button>
                    <button onclick="send('t')">T</button><button onclick="send('y')">Y</button>
                    <button onclick="send('u')">U</button><button onclick="send('i')">I</button>
                    <button onclick="send('o')">O</button><button onclick="send('p')">P</button>
                </div>
                <div class="row">
                    <button onclick="send('q')">Q</button><button onclick="send('s')">S</button>
                    <button onclick="send('d')">D</button><button onclick="send('f')">F</button>
                    <button onclick="send('g')">G</button><button onclick="send('h')">H</button>
                    <button onclick="send('j')">J</button><button onclick="send('k')">K</button>
                    <button onclick="send('l')">L</button><button onclick="send('m')">M</button>
                </div>
                <div class="row">
                    <button onclick="send('w')">W</button><button onclick="send('x')">X</button>
                    <button onclick="send('c')">C</button><button onclick="send('v')">V</button>
                    <button onclick="send('b')">B</button><button onclick="send('n')">N</button>
                </div>
            </div>
        </div>

    </div>

    <script>
        function send(key) {
            fetch('/press/' + key);
            if (navigator.vibrate) navigator.vibrate(15);
        }

        function sendMouseClick(btn) {
            fetch('/click/' + btn);
            if (navigator.vibrate) navigator.vibrate(20);
        }

        // Logique du Pavé Tactile (Touchpad)
        const pad = document.getElementById('touchpad');
        let lastX = 0, lastY = 0;
        let isMoving = false;
        let hasMoved = false;

        pad.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            lastX = touch.clientX;
            lastY = touch.clientY;
            isMoving = true;
            hasMoved = false;
        });

        pad.addEventListener('touchmove', (e) => {
            if (!isMoving) return;
            const touch = e.touches[0];
            const dx = (touch.clientX - lastX) * 1.8; // Sensibilité X
            const dy = (touch.clientY - lastY) * 1.8; // Sensibilité Y

            if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
                hasMoved = true;
                fetch(`/move?dx=${dx}&dy=${dy}`);
                lastX = touch.clientX;
                lastY = touch.clientY;
            }
        });

        pad.addEventListener('touchend', () => {
            isMoving = false;
            // Si le doigt n'a presque pas bougé, on considère cela comme un clic rapide
            if (!hasMoved) {
                sendMouseClick('left');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_screen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/press/<key>')
def press_key(key):
    special_keys = {
        'win': 'win', 'enter': 'enter', 'space': 'space', 
        'backspace': 'backspace', 'esc': 'esc',
        'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right'
    }
    if key in special_keys:
        pyautogui.press(special_keys[key])
    elif len(key) == 1 and key.isalnum():
        pyautogui.press(key)
    return '', 204

@app.route('/move')
def move_mouse():
    dx = float(request.args.get('dx', 0))
    dy = float(request.args.get('dy', 0))
    pyautogui.moveRel(dx, dy)
    return '', 204

@app.route('/click/<btn>')
def click_mouse(btn):
    if btn in ['left', 'right']:
        pyautogui.click(button=btn)
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
