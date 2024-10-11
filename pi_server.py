from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO
import cv2
import numpy as np
import threading
import requests

app = Flask(__name__)
socketio = SocketIO(app)

# Frame buffer to store the latest frame
frame_buffer = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    global frame_buffer
    while True:
        with frame_lock:
            if frame_buffer is not None:
                frame = frame_buffer.copy()
            else:
                continue
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)