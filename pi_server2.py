from flask import Flask, render_template, request
from flask_socketio import SocketIO
import cv2
import numpy as np
import threading
import base64

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Frame buffer to store the latest frame
frame_buffer = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def send_frame_to_clients():
    global frame_buffer
    while True:
        with frame_lock:
            if frame_buffer is not None:
                frame = frame_buffer.copy()
            else:
                continue
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('frame_update', {'frame': frame_bytes})
        socketio.sleep(0.033)  # Aim for about 30 FPS

@app.route('/update_frame', methods=['POST'])
def update_frame():
    global frame_buffer
    frame_data = request.files['frame'].read()
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    with frame_lock:
        frame_buffer = frame
    
    return 'Frame updated', 200

if __name__ == '__main__':
    socketio.start_background_task(send_frame_to_clients)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)