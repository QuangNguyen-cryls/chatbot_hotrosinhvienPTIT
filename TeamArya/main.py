from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import json
import subprocess
import sys
import os
import atexit
import signal
sys.path.append('.')
from spelling import normalize_text
from precise_chatbot import PreciseHandbookChatbot

app = Flask(__name__)

# --- Tự động khởi động Rasa server và action server ---
rasa_server = None
rasa_action = None
precise_bot: PreciseHandbookChatbot | None = None

def start_backend():
    global rasa_server, rasa_action
    rasa_data_dir = os.path.join(os.getcwd(), "RasaData")
    # Khởi động Rasa server
    rasa_server = subprocess.Popen(
        [sys.executable, "-m", "rasa", "run", "--enable-api", "--cors", "*", "--port", "5002"],
        cwd=rasa_data_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    # Khởi động action server
    rasa_action = subprocess.Popen(
        [sys.executable, "-m", "rasa", "run", "actions", "--port", "5055"],
        cwd=rasa_data_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

def stop_backend():
    if rasa_server:
        rasa_server.terminate()
    if rasa_action:
        rasa_action.terminate()

start_backend()
atexit.register(stop_backend)

# --- Khởi tạo SentenceTransformer chatbot (precise) một lần ---
def init_precise_bot():
    global precise_bot
    try:
        precise_bot = PreciseHandbookChatbot()
        precise_bot.load_model()
        # Thử nạp index có sẵn hoặc build từ data_processor output
        if not precise_bot.load_index():
            # Fallback cuối cùng: parse từ handbook_summary.txt nếu chưa có gì
            chunks = precise_bot.parse_handbook_precise("handbook_summary.txt")
            precise_bot.create_embeddings(chunks)
    except Exception as e:
        precise_bot = None

init_precise_bot()

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        engine = (data.get('engine') or 'rasa').lower()  # 'rasa' | 'st'
        
        # Chuẩn hóa input chung
        processed_message = normalize_text(user_message)

        if engine == 'st' and precise_bot is not None:
            # Trả lời bằng SentenceTransformer precise bot
            answer = precise_bot.answer_question_precise(processed_message)
            bot_response = answer
        else:
            # Mặc định: chuyển sang Rasa
            rasa_response = requests.post(
                'http://localhost:5002/webhooks/rest/webhook',
                json={'sender': 'user', 'message': processed_message}
            )
            if rasa_response.status_code == 200:
                rasa_data = rasa_response.json()
                bot_response = rasa_data[0]['text'] if rasa_data else "Xin lỗi, tôi chưa hiểu câu hỏi."
            else:
                bot_response = "Xin lỗi, có lỗi khi xử lý tin nhắn."
            
        return jsonify({'response': bot_response})
        
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

# Run Server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)