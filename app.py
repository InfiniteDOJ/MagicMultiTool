import sqlite3
import os
import logging
from flask import Flask, request, jsonify, render_template_string
from waitress import serve
from pythonosc import udp_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MagicMultiTool - %(levelname)s - %(message)s')

app = Flask(__name__)
DB_NAME = "presets.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT, 
                content TEXT, 
                type TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MagicMultiTool ✨</title>
    <style>
        :root {
            --bg-main: #0d0d12;
            --bg-card: #1a1a24;
            --bg-input: #232330;
            --accent-cyan: #00e5ff;
            --accent-purple: #8a2be2;
            --accent-green: #1DB954;
            --accent-red: #ff4d4d;
            --text-main: #e0e0e0;
            --text-muted: #888;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-main); color: var(--text-main); margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 550px; background: var(--bg-card); padding: 25px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.5); }
        h2 { margin-top: 0; text-align: center; color: white; letter-spacing: 1px; }
        
        input[type="text"], textarea { width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; background: var(--bg-input); border: 1px solid #333; color: white; box-sizing: border-box; font-family: inherit; transition: border 0.3s; resize: vertical; }
        input[type="text"]:focus, textarea:focus { outline: none; border-color: var(--accent-cyan); }
        
        button { padding: 12px; margin: 5px 0; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; width: 100%; transition: transform 0.1s, filter 0.2s; font-size: 14px; }
        button:active { transform: scale(0.98); }
        button:hover { filter: brightness(1.1); }
        .btn-green { background: var(--accent-green); color: white; }
        .btn-cyan { background: var(--accent-cyan); color: #000; }
        .btn-purple { background: var(--accent-purple); color: white; }
        .btn-red { background: var(--accent-red); color: white; }
        .btn-outline { background: transparent; border: 1px solid var(--accent-cyan); color: var(--accent-cyan); }
        
        .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 12px; background: var(--bg-input); color: var(--text-muted); border-radius: 8px; margin: 0; }
        .tab-btn.active { background: var(--accent-cyan); color: #000; box-shadow: 0 0 10px rgba(0, 229, 255, 0.2); }
        .tab-content { display: none; animation: fadeIn 0.3s; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        
        .list-container { max-height: 200px; overflow-y: auto; padding-right: 5px; margin-top: 10px; }
        .list-container::-webkit-scrollbar { width: 6px; }
        .list-container::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
        .preset-item { background: var(--bg-input); padding: 10px 15px; margin: 6px 0; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; font-size: 0.95em; border-left: 3px solid var(--accent-cyan); }
        .preset-actions { display: flex; gap: 5px; }
        .preset-actions button { width: auto; padding: 6px 12px; margin: 0; }
        
        #toast { position: fixed; bottom: -50px; left: 50%; transform: translateX(-50%); background: var(--accent-green); color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; transition: bottom 0.3s; z-index: 1000; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        #toast.show { bottom: 20px; }
        #toast.error { background: var(--accent-red); }
        
        hr { border: 0; height: 1px; background: #333; margin: 20px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>MagicMultiTool ✨</h2>
    
    <label style="font-size: 0.85em; color: var(--text-muted); margin-bottom: 5px; display: block;">Target Quest IP Address</label>
    <input type="text" id="ip" placeholder="e.g. 192.168.1.50" onchange="saveIP()">

    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('manual')">Manual</button>
        <button class="tab-btn" onclick="showTab('auto')">Auto</button>
        <button class="tab-btn" onclick="showTab('voice')">Voice</button>
        <button class="tab-btn" onclick="showTab('icons')">Icons</button>
    </div>

    <div id="manual" class="tab-content active">
        <textarea id="manual-msg" rows="3" placeholder="Type your message here..."></textarea>
        <button class="btn-green" onclick="sendOSC('manual-msg')">Send Message Once</button>
        <button class="btn-outline" onclick="savePreset('manual')">+ Save as Manual Preset</button>
        <div class="list-container" id="manual-list"></div>
    </div>

    <div id="auto" class="tab-content">
        <textarea id="auto-msg" rows="3" placeholder="Type a message to loop or save..."></textarea>
        
        <div style="display: flex; gap: 10px;">
            <button class="btn-red" id="single-toggle" onclick="toggleLoop()">Loop This Message</button>
            <button class="btn-outline" onclick="savePreset('auto')">+ Save Static</button>
        </div>
        <div class="list-container" id="auto-list" style="max-height: 120px;"></div>
        
        <hr>
        
        <div style="display: flex; gap: 10px;">
            <button class="btn-purple" id="cycle-toggle" onclick="toggleCycle()">▶ Start Cycle List</button>
            <button class="btn-outline" onclick="savePreset('cycle')">+ Add to Cycle</button>
        </div>
        <div class="list-container" id="cycle-list" style="max-height: 120px;"></div>
    </div>

    <div id="voice" class="tab-content">
        <div style="text-align: center; padding: 20px 0;">
            <p id="voice-status" style="color: var(--text-muted); margin-bottom: 20px;">Requires microphone permissions.</p>
            <button class="btn-purple" id="voice-btn" onclick="toggleVoice()" style="padding: 20px; font-size: 1.2em; border-radius: 50px;">🎙️ Start Voice Input</button>
        </div>
    </div>

    <div id="icons" class="tab-content">
        <p style="color: var(--text-muted); font-size: 0.9em; text-align: center;">Click to append to current textboxes</p>
        <div id="emoji-grid" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:8px;"></div>
    </div>
</div>

<div id="toast">Message Sent!</div>

<script>
    let loopId = null;
    let cycleIndex = 0;
    
    const ipInput = document.getElementById('ip');
    if (localStorage.getItem('magic_quest_ip')) ipInput.value = localStorage.getItem('magic_quest_ip');

    function saveIP() { localStorage.setItem('magic_quest_ip', ipInput.value); }
    
    function showTab(id) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        event.target.classList.add('active');
    }

    function showToast(message, isError = false) {
        const toast = document.getElementById('toast');
        toast.innerText = message;
        toast.className = isError ? 'error show' : 'show';
        setTimeout(() => toast.className = '', 3000);
    }

    async function sendOSC(textElementId = null, rawText = null) {
        const text = rawText !== null ? rawText : document.getElementById(textElementId).value;
        if (!text.trim()) { showToast("Cannot send empty message", true); return; }
        if (!ipInput.value) { showToast("Please enter a Quest IP", true); return; }

        try {
            const res = await fetch('/send', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ip: ipInput.value, msg: text}) 
            });
            if (res.ok) { showToast("Message Sent!"); } 
            else { showToast("Failed to send", true); }
        } catch (error) {
            showToast("Network Error", true);
        }
    }

    function stopAllLoops() {
        if (loopId) clearInterval(loopId);
        loopId = null;
        document.getElementById('single-toggle').innerText = "Loop This Message";
        document.getElementById('cycle-toggle').innerText = "▶ Start Cycle List";
    }

    function toggleLoop() {
        if (loopId) { stopAllLoops(); }
        else { 
            stopAllLoops(); 
            const msg = document.getElementById('auto-msg').value;
            if(!msg) return showToast("Enter a message to loop", true);
            sendOSC(null, msg); 
            loopId = setInterval(() => sendOSC(null, msg), 5000); 
            document.getElementById('single-toggle').innerText = "🛑 Stop Looping"; 
        }
    }

    async function toggleCycle() {
        if (loopId) { stopAllLoops(); }
        else {
            stopAllLoops(); 
            const res = await fetch('/presets');
            const data = await res.json();
            const cyclePresets = data.filter(p => p.type === 'cycle');
            
            if(cyclePresets.length === 0) {
                showToast("Cycle List is empty!", true);
                return;
            }
            
            sendOSC(null, cyclePresets[cycleIndex].content);
            cycleIndex = (cycleIndex + 1) % cyclePresets.length;

            loopId = setInterval(() => {
                sendOSC(null, cyclePresets[cycleIndex].content);
                cycleIndex = (cycleIndex + 1) % cyclePresets.length;
            }, 5000);
            document.getElementById('cycle-toggle').innerText = "🛑 Stop Cycling";
        }
    }

    async function loadPresets() {
        const res = await fetch('/presets');
        const data = await res.json();
        
        ['manual', 'auto', 'cycle'].forEach(t => document.getElementById(t+'-list').innerHTML = '');
        
        data.forEach(p => {
            const div = document.createElement('div');
            div.className = 'preset-item';
            div.innerHTML = `
                <span style="font-weight:bold; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width: 60%;">${p.name}</span>
                <div class="preset-actions">
                    <button class="btn-cyan" onclick="document.getElementById('${p.type === 'cycle' ? 'auto' : p.type}-msg').value=\`${p.content.replace(/`/g, '\\`')}\`">Load</button>
                    <button class="btn-red" onclick="deletePreset(${p.id})">X</button>
                </div>`;
            document.getElementById(p.type + '-list').appendChild(div);
        });
    }

    async function savePreset(type) {
        const contentId = type === 'cycle' ? 'auto-msg' : type + '-msg';
        const content = document.getElementById(contentId).value.trim();
        
        if (!content) return showToast("Cannot save empty message", true);
        
        const name = prompt("Enter a name for this preset:");
        if(name) {
            await fetch('/save_preset', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, content, type}) 
            });
            loadPresets();
            showToast("Preset saved!");
        }
    }

    async function deletePreset(id) {
        if(confirm("Delete this preset?")) {
            await fetch('/delete_preset', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id}) 
            });
            loadPresets();
        }
    }

    let recognition = null;
    let isListening = false;
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = (e) => { 
            const text = e.results[e.results.length - 1][0].transcript;
            document.getElementById('manual-msg').value = text; 
            document.getElementById('auto-msg').value = text;
        };
    } else {
        document.getElementById('voice-status').innerText = "Speech Recognition not supported in this browser.";
        document.getElementById('voice-btn').style.display = "none";
    }

    function toggleVoice() {
        if (!recognition) return;
        if (!isListening) { 
            recognition.start(); 
            isListening = true; 
            document.getElementById('voice-btn').innerText = "🛑 Stop Listening"; 
            document.getElementById('voice-btn').className = "btn-red";
            document.getElementById('voice-status').innerText = "Listening... speak now.";
        } else { 
            recognition.stop(); 
            isListening = false; 
            document.getElementById('voice-btn').innerText = "🎙️ Start Voice Input"; 
            document.getElementById('voice-btn').className = "btn-purple";
            document.getElementById('voice-status').innerText = "Click to start speaking";
        }
    }

    const emojis = ['✨','🎵','🔥','💀','🌸','⚡','🌀','🎮','❤️','👽','💤','🛑','☢️','💎','🚀','🌌','🤡','🌈','🧊','🦊','🐈','『','』','♫'];
    const grid = document.getElementById('emoji-grid');
    emojis.forEach(e => {
        const b = document.createElement('button'); 
        b.className = 'btn-input'; 
        b.style = "background: var(--bg-input); color: white; padding: 10px; border-radius: 5px; border: 1px solid #333; cursor: pointer;";
        b.innerText = e;
        b.onclick = () => { 
            document.getElementById('manual-msg').value += e; 
            document.getElementById('auto-msg').value += e; 
        };
        grid.appendChild(b);
    });

    loadPresets();
</script>
</body>
</html>
"""

@app.route('/')
def home(): 
    return render_template_string(HTML_TEMPLATE)

@app.route('/presets', methods=['GET'])
def get_presets():
    try:
        conn = sqlite3.connect(DB_NAME)
        rows = conn.execute("SELECT id, name, content, type FROM presets").fetchall()
        conn.close()
        return jsonify([{"id": r[0], "name": r[1], "content": r[2], "type": r[3]} for r in rows])
    except Exception as e:
        logging.error(f"Error fetching presets: {e}")
        return jsonify({"error": "Failed to fetch"}), 500

@app.route('/save_preset', methods=['POST'])
def save_preset():
    try:
        data = request.json
        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO presets (name, content, type) VALUES (?, ?, ?)", 
                    (data['name'], data['content'], data['type']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error saving preset: {e}")
        return jsonify({"error": "Failed to save"}), 500

@app.route('/delete_preset', methods=['POST'])
def delete_preset():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM presets WHERE id = ?", (request.json['id'],))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error deleting preset: {e}")
        return jsonify({"error": "Failed to delete"}), 500

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    ip = data.get('ip')
    msg = data.get('msg')
    
    if not ip or not msg:
        return jsonify({"status": "error", "message": "Missing IP or message"}), 400

    try:
        client = udp_client.SimpleUDPClient(ip, 9000)
        client.send_message("/chatbox/input", [msg, True, False])
        logging.info(f"Sent OSC message to {ip}: {msg}")
        return jsonify({"status": "sent"})
    except Exception as e:
        logging.error(f"Failed to send OSC message: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    init_db()
    logging.info("Starting MagicMultiTool server on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)