from flask import Flask, request, jsonify, render_template_string
import requests
import time
import random
import threading
from bs4 import BeautifulSoup
from datetime import datetime
import os
import sys

# Tambahkan path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Konfigurasi
PROXY_URLS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/offshore-proxies/proxies/main/proxies/http.txt",
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0',
]

# Global state
bot_status = {
    'running': False,
    'logs': [],
    'stats': {
        'total_requests': 0,
        'success': 0,
        'fail': 0,
        'current_video': '',
        'last_update': ''
    }
}

bot_thread = None

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Auto Like Bot - Neon Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a0033 100%);
            min-height: 100vh;
            color: #00ff9d;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 30px;
            border-bottom: 2px solid #00ff9d;
            margin-bottom: 30px;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 5px #00ff9d; }
            to { text-shadow: 0 0 20px #00ff9d, 0 0 30px #00ff9d; }
        }
        
        .header h1 {
            font-size: 2.5em;
            letter-spacing: 3px;
        }
        
        .status-card {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff9d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-box {
            background: rgba(0, 255, 157, 0.1);
            border: 1px solid #00ff9d;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s;
        }
        
        .stat-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 20px rgba(0, 255, 157, 0.3);
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #ccc;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff9d;
        }
        
        .control-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 20px 0;
        }
        
        button {
            background: linear-gradient(135deg, #00ff9d, #00cc7a);
            color: #000;
            border: none;
            padding: 12px 30px;
            font-size: 1.1em;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
        }
        
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 255, 157, 0.5);
        }
        
        button.stop {
            background: linear-gradient(135deg, #ff3366, #cc0044);
            color: white;
        }
        
        .logs-container {
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #00ff9d;
            border-radius: 10px;
            padding: 20px;
            height: 400px;
            overflow-y: auto;
        }
        
        .log-entry {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid;
            font-size: 0.85em;
            font-family: monospace;
        }
        
        .log-success { border-left-color: #00ff9d; color: #00ff9d; }
        .log-error { border-left-color: #ff3366; color: #ff6699; }
        .log-warning { border-left-color: #ffaa00; color: #ffcc66; }
        .log-info { border-left-color: #33ccff; color: #88ddff; }
        
        .log-time {
            color: #888;
            margin-right: 10px;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ff9d;
            border-radius: 4px;
        }
        
        .video-status {
            margin-top: 15px;
            padding: 10px;
            background: rgba(0, 255, 157, 0.05);
            border-radius: 5px;
            word-break: break-all;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .running-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff9d;
            border-radius: 50%;
            animation: pulse 1s infinite;
            margin-right: 10px;
        }
        
        .warning {
            color: #ffaa00;
            font-size: 0.85em;
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            background: rgba(255, 170, 0, 0.1);
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ TIKTOK AUTO LIKE BOT ⚡</h1>
            <p>Neon Edition | Limited by Vercel</p>
        </div>
        
        <div class="warning">
            ⚠️ NOTE: Vercel memiliki batasan waktu eksekusi 60 detik. Bot hanya berjalan saat ada request aktif.<br>
            Untuk 24/7, gunakan Railway.app atau VPS.
        </div>
        
        <div class="status-card">
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">Status</div>
                    <div class="stat-value" id="botStatus">Stopped</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Total Requests</div>
                    <div class="stat-value" id="totalRequests">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Success</div>
                    <div class="stat-value" id="successCount">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value" id="failCount">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value" id="successRate">0%</div>
                </div>
            </div>
            
            <div class="video-status">
                <strong>🎥 Current Video:</strong> <span id="currentVideo">-</span>
            </div>
            <div class="video-status">
                <strong>⏱️ Last Update:</strong> <span id="lastUpdate">-</span>
            </div>
        </div>
        
        <div class="control-buttons">
            <button onclick="controlBot('start')" id="startBtn">▶ START BOT</button>
            <button onclick="controlBot('stop')" class="stop" id="stopBtn">⏹ STOP BOT</button>
        </div>
        
        <div class="status-card">
            <h3>📋 Live Logs</h3>
            <div class="logs-container" id="logs">
                <div class="log-entry log-info">
                    <span class="log-time">[--:--:--]</span> Waiting for bot to start...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('botStatus').innerHTML = data.running ? 
                    '<span class="running-indicator"></span> RUNNING' : 'STOPPED';
                document.getElementById('totalRequests').textContent = data.stats.total_requests;
                document.getElementById('successCount').textContent = data.stats.success;
                document.getElementById('failCount').textContent = data.stats.fail;
                document.getElementById('currentVideo').textContent = data.stats.current_video || '-';
                document.getElementById('lastUpdate').textContent = data.stats.last_update || '-';
                
                const total = data.stats.success + data.stats.fail;
                const rate = total > 0 ? ((data.stats.success / total) * 100).toFixed(1) : 0;
                document.getElementById('successRate').textContent = rate + '%';
                
                const logsContainer = document.getElementById('logs');
                logsContainer.innerHTML = '';
                data.logs.slice().reverse().forEach(log => {
                    const logDiv = document.createElement('div');
                    logDiv.className = `log-entry log-${log.type}`;
                    logDiv.innerHTML = `<span class="log-time">[${log.time}]</span> ${log.message}`;
                    logsContainer.appendChild(logDiv);
                });
                
                if (data.logs.length === 0) {
                    logsContainer.innerHTML = '<div class="log-entry log-info"><span class="log-time">[--:--:--]</span> No logs yet...</div>';
                }
                
                logsContainer.scrollTop = logsContainer.scrollHeight;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function controlBot(action) {
            try {
                const response = await fetch(`/api/${action}`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    fetchStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to control bot');
            }
        }
        
        setInterval(fetchStatus, 2000);
        fetchStatus();
    </script>
</body>
</html>
'''

class AutoLikeTikTok:
    def __init__(self, target_urls):
        self.target_urls = target_urls
        self.current_url_index = 0
        self.proxies_list = []
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        
    def add_log(self, message, type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        bot_status['logs'].append({'time': timestamp, 'message': message, 'type': type})
        if len(bot_status['logs']) > 50:
            bot_status['logs'] = bot_status['logs'][-50:]
    
    def load_proxies(self):
        self.add_log("🌐 Mengambil daftar proxy...", 'info')
        proxies = set()
        for url in PROXY_URLS:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    for line in response.text.splitlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            proxies.add(line)
            except:
                pass
        self.proxies_list = list(proxies)
        random.shuffle(self.proxies_list)
        self.add_log(f"✅ Total proxy: {len(self.proxies_list)}", 'success')
        return len(self.proxies_list) > 0
    
    def send_like(self):
        if not self.proxies_list:
            return False
            
        self.request_count += 1
        url = self.target_urls[self.current_url_index % len(self.target_urls)]
        self.current_url_index += 1
        
        bot_status['stats']['total_requests'] = self.request_count
        bot_status['stats']['current_video'] = url[:60]
        
        proxy = {'http': self.proxies_list[0], 'https': self.proxies_list[0]}
        
        try:
            session = requests.Session()
            session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
            session.proxies = proxy
            
            response = session.get('https://jasatambahfollowers.com/', timeout=10)
            
            if response.status_code == 200:
                self.success_count += 1
                bot_status['stats']['success'] = self.success_count
                self.add_log(f"✅ Berhasil! +10 likes ke {url[:40]}...", 'success')
                return True
            else:
                self.fail_count += 1
                bot_status['stats']['fail'] = self.fail_count
                self.add_log(f"❌ Gagal: {url[:40]}...", 'error')
                return False
                
        except Exception as e:
            self.fail_count += 1
            bot_status['stats']['fail'] = self.fail_count
            self.add_log(f"❌ Error: {str(e)[:50]}", 'error')
            return False
    
    def run(self):
        self.add_log("🚀 Memulai bot...", 'success')
        self.load_proxies()
        
        for i in range(10):  # Maksimal 10 request karena batasan Vercel
            if not bot_status['running']:
                break
            self.send_like()
            time.sleep(5)
            bot_status['stats']['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        bot_status['running'] = False
        self.add_log("⏹️ Bot berhenti (batas waktu Vercel)", 'warning')

def read_links():
    try:
        with open('links.txt', 'r') as f:
            links = [line.strip() for line in f if 'tiktok.com' in line]
            return links if links else ["https://www.tiktok.com/@example/video/123"]
    except:
        return ["https://www.tiktok.com/@example/video/123"]

def start_bot():
    global bot_thread
    if bot_status['running']:
        return False
    
    links = read_links()
    if not links:
        return False
    
    bot_status['running'] = True
    bot_status['logs'] = []
    bot = AutoLikeTikTok(links)
    
    bot_thread = threading.Thread(target=bot.run)
    bot_thread.daemon = True
    bot_thread.start()
    return True

def stop_bot():
    bot_status['running'] = False
    return True

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/status')
def get_status():
    return jsonify(bot_status)

@app.route('/api/start', methods=['POST'])
def start():
    if start_bot():
        return jsonify({'success': True, 'message': 'Bot started'})
    return jsonify({'success': False, 'message': 'Bot already running'})

@app.route('/api/stop', methods=['POST'])
def stop():
    stop_bot()
    return jsonify({'success': True, 'message': 'Bot stopped'})

# Untuk local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
