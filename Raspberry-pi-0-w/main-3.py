#!/usr/bin/env python3
"""
Raspberry Pi Camera Live Streaming Server with Motor Control
Compatible with OV5647 camera and L298N motor driver on Raspberry Pi Zero W
Usage: python3 main.py ( SAME GROUND )
"""

from flask import Flask, Response, render_template_string, request, abort, jsonify
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from pyzbar import pyzbar
import cv2
import numpy as np
import io
import threading
import time
import sys
from libcamera import Transform
import RPi.GPIO as GPIO

app = Flask(__name__)

# Allowed IP range (allow entire local network)
ALLOWED_NETWORK = "192.168.1."

# Motor control GPIO pins (using BCM numbering)
# You can modify these pin numbers based on your wiring preference
MOTOR_LEFT_IN1 = 17   # GPIO 17
MOTOR_LEFT_IN2 = 27   # GPIO 27
MOTOR_RIGHT_IN3 = 22  # GPIO 22
MOTOR_RIGHT_IN4 = 23  # GPIO 23

# PWM pins for speed control (optional, comment out if not using PWM)
MOTOR_LEFT_EN = 18    # GPIO 18 (PWM)
MOTOR_RIGHT_EN = 24   # GPIO 24 (PWM)

# Motor PWM frequency and default speed
PWM_FREQUENCY = 1000  # 1kHz
DEFAULT_SPEED = 80    # 80% speed

# Global PWM objects
pwm_left = None
pwm_right = None

@app.before_request
def limit_remote_addr():
    """Restrict access to only the allowed network"""
    client_ip = request.remote_addr
    if not (client_ip.startswith(ALLOWED_NETWORK) or client_ip == "127.0.0.1"):
        print(f"✗ Access denied from: {client_ip}")
        abort(403)

# HTML template with motor controls
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera & Motor Control</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            margin-bottom: 20px;
        }
        img {
            max-width: 90%;
            height: auto;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .info {
            margin-top: 20px;
            padding: 10px;
            background-color: #2a2a2a;
            border-radius: 5px;
        }
        .motor-controls {
            margin-top: 30px;
            padding: 20px;
            background-color: #2a2a2a;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 20px;
            max-width: 300px;
            margin-left: auto;
            margin-right: auto;
        }
        .control-btn {
            padding: 20px;
            font-size: 24px;
            border: none;
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
            touch-action: manipulation;
        }
        .control-btn:hover {
            background-color: #45a049;
            transform: scale(1.05);
        }
        .control-btn:active {
            background-color: #3d8b40;
            transform: scale(0.95);
        }
        .control-btn.stop {
            background-color: #f44336;
        }
        .control-btn.stop:hover {
            background-color: #da190b;
        }
        .speed-control {
            margin-top: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .speed-slider {
            width: 200px;
            height: 8px;
            border-radius: 5px;
            background: #444;
            outline: none;
            -webkit-appearance: none;
        }
        .speed-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }
        .speed-slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
            border: none;
        }
        .speed-value {
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
            min-width: 50px;
        }
        .qr-container {
            margin-top: 20px;
            padding: 20px;
            background-color: #2a2a2a;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
        }
        .qr-result {
            background-color: #1a1a1a;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
            margin-top: 10px;
            word-wrap: break-word;
            font-family: monospace;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .qr-timestamp {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .no-qr {
            color: #888;
            font-style: italic;
        }
        .scanning {
            color: #4CAF50;
            font-weight: bold;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #4CAF50;
            animation: pulse 2s infinite;
            margin-right: 8px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .status-message {
            text-align: center;
            margin-top: 15px;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 5px;
            font-size: 14px;
            color: #888;
        }
    </style>
</head>
<body>
    <h1>🤖 Raspberry Pi Camera & Motor Control</h1>
    <img src="{{ url_for('video_feed') }}" alt="Camera Stream">
    <div class="info">
        <p>Camera: OV5647 Arducam | Resolution: 640x480 @ 30fps</p>
    </div>
    
    <div class="motor-controls">
        <h2>🎮 Motor Controls</h2>
        
        <div class="control-grid">
            <div></div>
            <button class="control-btn" 
                    onmousedown="startCommand('forward')" 
                    onmouseup="stopCommand()"
                    onmouseleave="stopCommand()" 
                    ontouchstart="startCommand('forward')" 
                    ontouchend="stopCommand()">
                ⬆️
            </button>
            <div></div>
            
            <button class="control-btn" 
                    onmousedown="startCommand('left')" 
                    onmouseup="stopCommand()"
                    onmouseleave="stopCommand()" 
                    ontouchstart="startCommand('left')" 
                    ontouchend="stopCommand()">
                ⬅️
            </button>
            <button class="control-btn stop" onclick="sendCommand('stop')">
                ⏹️
            </button>
            <button class="control-btn" 
                    onmousedown="startCommand('right')" 
                    onmouseup="stopCommand()"
                    onmouseleave="stopCommand()" 
                    ontouchstart="startCommand('right')" 
                    ontouchend="stopCommand()">
                ➡️
            </button>
            
            <div></div>
            <button class="control-btn" 
                    onmousedown="startCommand('backward')" 
                    onmouseup="stopCommand()"
                    onmouseleave="stopCommand()" 
                    ontouchstart="startCommand('backward')" 
                    ontouchend="stopCommand()">
                ⬇️
            </button>
            <div></div>
        </div>
        
        <div class="speed-control">
            <label>Speed:</label>
            <input type="range" min="0" max="100" value="80" class="speed-slider" id="speedSlider" oninput="updateSpeed(this.value)">
            <span class="speed-value" id="speedValue">80%</span>
        </div>
        
        <div class="status-message" id="motorStatus">Ready</div>
    </div>
    
    <div class="qr-container">
        <h2>🔍 QR Code Scanner</h2>
        <p class="scanning"><span class="status-indicator"></span>Scanning continuously...</p>
        <div id="qr-results">
            <p class="no-qr">Point camera at a QR code...</p>
        </div>
    </div>

    <script>
        let lastQRData = '';
        let currentSpeed = 80;
        let commandInterval = null;
        
        function sendCommand(command) {
            fetch('/motor_control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    speed: currentSpeed
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('motorStatus').textContent = data.status || 'Command sent';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('motorStatus').textContent = 'Error: ' + error.message;
            });
        }
        
        function startCommand(command) {
            // Clear any existing interval first
            if (commandInterval) {
                clearInterval(commandInterval);
                commandInterval = null;
            }
            // Send immediate command
            sendCommand(command);
            // Keep sending while button is held (for continuous movement)
            commandInterval = setInterval(() => sendCommand(command), 100);
        }
        
        function stopCommand() {
            // Clear the interval to stop repeated commands
            if (commandInterval) {
                clearInterval(commandInterval);
                commandInterval = null;
            }
            // Send stop command
            sendCommand('stop');
        }
        
        function updateSpeed(value) {
            currentSpeed = parseInt(value);
            document.getElementById('speedValue').textContent = value + '%';
            // Update speed on server
            fetch('/motor_speed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ speed: currentSpeed })
            });
        }
        
        function scanQR() {
            fetch('/scan_qr')
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('qr-results');
                    
                    if (data.qr_codes && data.qr_codes.length > 0) {
                        const currentQRData = JSON.stringify(data.qr_codes);
                        if (currentQRData !== lastQRData) {
                            lastQRData = currentQRData;
                            resultsDiv.innerHTML = '';
                            
                            data.qr_codes.forEach((qr, index) => {
                                const resultDiv = document.createElement('div');
                                resultDiv.className = 'qr-result';
                                const timestamp = new Date().toLocaleTimeString();
                                resultDiv.innerHTML = `
                                    <strong>QR Code ${index + 1}:</strong><br>
                                    <div style="margin-top: 10px; font-size: 1.1em;">${escapeHtml(qr.data)}</div>
                                    <div class="qr-timestamp">Type: ${qr.type} | Detected: ${timestamp}</div>
                                `;
                                resultsDiv.appendChild(resultDiv);
                            });
                        }
                    } else if (lastQRData !== '') {
                        lastQRData = '';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Prevent accidental page refresh
        window.addEventListener('beforeunload', function() {
            sendCommand('stop');
        });
        
        // Start QR scanning
        setInterval(scanQR, 500);
        scanQR();
    </script>
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    """Custom output class for streaming frames"""
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Initialize camera
picam2 = None
output = None

def init_gpio():
    """Initialize GPIO pins for motor control"""
    global pwm_left, pwm_right
    
    try:
        # Clean up any previous GPIO usage
        try:
            GPIO.cleanup()
        except:
            pass
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup motor control pins
        GPIO.setup(MOTOR_LEFT_IN1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(MOTOR_LEFT_IN2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(MOTOR_RIGHT_IN3, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(MOTOR_RIGHT_IN4, GPIO.OUT, initial=GPIO.LOW)
        
        # Setup PWM pins for speed control
        GPIO.setup(MOTOR_LEFT_EN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(MOTOR_RIGHT_EN, GPIO.OUT, initial=GPIO.LOW)
        
        # Initialize PWM
        pwm_left = GPIO.PWM(MOTOR_LEFT_EN, PWM_FREQUENCY)
        pwm_right = GPIO.PWM(MOTOR_RIGHT_EN, PWM_FREQUENCY)
        
        pwm_left.start(0)
        pwm_right.start(0)
        
        # Ensure motors are stopped initially
        stop_motors()
        
        print("✓ GPIO initialized successfully")
        print(f"  Left Motor: IN1={MOTOR_LEFT_IN1}, IN2={MOTOR_LEFT_IN2}, EN={MOTOR_LEFT_EN}")
        print(f"  Right Motor: IN3={MOTOR_RIGHT_IN3}, IN4={MOTOR_RIGHT_IN4}, EN={MOTOR_RIGHT_EN}")
        return True
    except Exception as e:
        print(f"✗ Error initializing GPIO: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  1. Run: sudo pkill -9 python3")
        print("  2. Run: python3 -c 'import RPi.GPIO as GPIO; GPIO.cleanup()'")
        print("  3. Try running with: sudo python3 main.py")
        return False

def set_motor_speed(speed):
    """Set PWM duty cycle for motor speed (0-100)"""
    global pwm_left, pwm_right
    speed = max(0, min(100, speed))  # Clamp between 0-100
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def stop_motors():
    """Stop all motors"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    set_motor_speed(0)

def move_forward(speed=DEFAULT_SPEED):
    """Move forward"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    set_motor_speed(speed)

def move_backward(speed=DEFAULT_SPEED):
    """Move backward"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)
    set_motor_speed(speed)

def turn_left(speed=DEFAULT_SPEED):
    """Turn left (left motor backward, right motor forward)"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    set_motor_speed(speed)

def turn_right(speed=DEFAULT_SPEED):
    """Turn right (left motor forward, right motor backward)"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)
    set_motor_speed(speed)

def check_camera_availability():
    """Check if camera is detected"""
    try:
        cameras = Picamera2.global_camera_info()
        print(f"Detected cameras: {cameras}")
        
        if len(cameras) == 0:
            print("\n✗ No cameras detected!")
            print("\nTroubleshooting steps:")
            print("1. Check camera cable connection")
            print("2. Run: libcamera-hello --list-cameras")
            print("3. Ensure legacy camera is DISABLED in raspi-config")
            print("4. Try: sudo reboot")
            return False
        return True
    except Exception as e:
        print(f"Error checking cameras: {e}")
        return False

def init_camera():
    """Initialize the camera with optimal settings for Pi Zero W"""
    global picam2, output
    
    try:
        if not check_camera_availability():
            return False
        
        picam2 = Picamera2()
        print(f"Camera model: {picam2.camera_properties.get('Model', 'Unknown')}")
        
        config = picam2.create_video_configuration(
            main={"size": (640, 480)},
            lores={"size": (320, 240)},
            display="lores",
            encode="main",
            transform=Transform(hflip=True, vflip=True)
        )
        picam2.configure(config)
        
        output = StreamingOutput()
        
        print("Starting camera...")
        picam2.start()
        time.sleep(2)
        
        print("✓ Camera initialized successfully (rotated 180°)")
        return True
    except Exception as e:
        print(f"✗ Error initializing camera: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_frames():
    """Generator function to yield MJPEG frames"""
    global output, picam2
    
    encoder = MJPEGEncoder()
    picam2.start_encoder(encoder, FileOutput(output))
    
    try:
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            yield (b'--FRAME\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except GeneratorExit:
        picam2.stop_encoder()

@app.route('/')
def index():
    """Main page with video stream and motor controls"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=FRAME')

@app.route('/motor_control', methods=['POST'])
def motor_control():
    """Handle motor control commands"""
    try:
        data = request.get_json()
        command = data.get('command', '').lower()
        speed = data.get('speed', DEFAULT_SPEED)
        
        print(f"Motor command: {command} at {speed}% speed")
        
        if command == 'forward':
            move_forward(speed)
            status = f"Moving forward at {speed}%"
        elif command == 'backward':
            move_backward(speed)
            status = f"Moving backward at {speed}%"
        elif command == 'left':
            turn_left(speed)
            status = f"Turning left at {speed}%"
        elif command == 'right':
            turn_right(speed)
            status = f"Turning right at {speed}%"
        elif command == 'stop':
            stop_motors()
            status = "Motors stopped"
        else:
            return jsonify({'success': False, 'error': 'Invalid command'}), 400
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        print(f"✗ Error in motor control: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/motor_speed', methods=['POST'])
def motor_speed():
    """Update motor speed"""
    try:
        data = request.get_json()
        speed = data.get('speed', DEFAULT_SPEED)
        print(f"Speed updated to: {speed}%")
        return jsonify({'success': True, 'speed': speed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/scan_qr')
def scan_qr():
    """Capture image and scan for QR codes"""
    global picam2
    
    try:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        qr_codes = pyzbar.decode(gray)
        
        results = []
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8')
            qr_type = qr.type
            results.append({
                'data': qr_data,
                'type': qr_type
            })
            print(f"✓ QR Code detected: {qr_data}")
        
        return jsonify({
            'success': True,
            'qr_codes': results,
            'count': len(results)
        })
    except Exception as e:
        print(f"✗ Error scanning QR code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status')
def status():
    """Health check endpoint"""
    return {"status": "running", "camera": "OV5647", "motors": "L298N"}

if __name__ == '__main__':
    print("=" * 50)
    print("Raspberry Pi Camera & Motor Control Server")
    print("=" * 50)
    
    # Initialize GPIO
    if not init_gpio():
        print("\n✗ GPIO initialization failed!")
        sys.exit(1)
    
    # Initialize camera
    if not init_camera():
        print("\n" + "=" * 50)
        print("CAMERA INITIALIZATION FAILED")
        print("=" * 50)
        sys.exit(1)
    
    # Get the local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\n✓ Server starting...")
    print(f"✓ Access restricted to: {ALLOWED_NETWORK}x")
    print(f"✓ Access the stream at:")
    print(f"  → http://{local_ip}:5000")
    print(f"  → http://localhost:5000 (from Pi only)")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n\n✓ Shutting down server...")
    finally:
        stop_motors()
        GPIO.cleanup()
        if picam2:
            picam2.stop()
            print("✓ Camera stopped")
        print("✓ Motors stopped")
        print("✓ GPIO cleaned up")
        print("✓ Server stopped")