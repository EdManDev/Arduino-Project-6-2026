#!/usr/bin/env python3
"""
Raspberry Pi Camera Live Streaming Server
Compatible with OV5647 camera on Raspberry Pi Zero W
Usage: python3 main.py
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

app = Flask(__name__)

# Allowed IP range (allow entire local network)
ALLOWED_NETWORK = "192.168.1."

@app.before_request
def limit_remote_addr():
    """Restrict access to only the allowed network"""
    client_ip = request.remote_addr
    # Allow localhost and IPs in the 192.168.1.x range
    if not (client_ip.startswith(ALLOWED_NETWORK) or client_ip == "127.0.0.1"):
        print(f"✗ Access denied from: {client_ip}")
        abort(403)  # Forbidden

# HTML template for the streaming page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera Stream</title>
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
    </style>
</head>
<body>
    <h1>📹 Raspberry Pi Camera Stream</h1>
    <img src="{{ url_for('video_feed') }}" alt="Camera Stream">
    <div class="info">
        <p>Camera: OV5647 Arducam</p>
        <p>Resolution: 640x480 @ 30fps</p>
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
        
        function scanQR() {
            fetch('/scan_qr')
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('qr-results');
                    
                    if (data.qr_codes && data.qr_codes.length > 0) {
                        // Check if QR code data has changed
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
                        // Only update if we had a QR code before
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
        
        // Start continuous scanning (every 500ms)
        setInterval(scanQR, 500);
        
        // Initial scan
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
        # Check camera availability first
        if not check_camera_availability():
            return False
        
        picam2 = Picamera2()
        
        # Print camera properties
        print(f"Camera model: {picam2.camera_properties.get('Model', 'Unknown')}")
        
        # Configure camera for streaming with 180-degree rotation
        config = picam2.create_video_configuration(
            main={"size": (640, 480)},
            lores={"size": (320, 240)},
            display="lores",
            encode="main",
            transform=Transform(hflip=True, vflip=True)  # Rotate 180 degrees
        )
        picam2.configure(config)
        
        # Create output stream
        output = StreamingOutput()
        
        # Start camera
        print("Starting camera...")
        picam2.start()
        time.sleep(2)  # Wait for camera to warm up
        
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
    """Main page with video stream"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=FRAME')

@app.route('/scan_qr')
def scan_qr():
    """Capture image and scan for QR codes"""
    global picam2
    
    try:
        # Capture a frame
        frame = picam2.capture_array()
        
        # Convert to grayscale for better QR detection
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Decode QR codes
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
        
        if not results:
            print("✗ No QR codes detected")
        
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
    return {"status": "running", "camera": "OV5647"}

if __name__ == '__main__':
    print("=" * 50)
    print("Raspberry Pi Camera Streaming Server")
    print("=" * 50)
    
    # Initialize camera
    if not init_camera():
        print("\n" + "=" * 50)
        print("CAMERA INITIALIZATION FAILED")
        print("=" * 50)
        print("\nPlease run these diagnostic commands:")
        print("  → libcamera-hello --list-cameras")
        print("  → vcgencmd get_camera")
        print("\nIf camera is not detected:")
        print("  → Check physical connection")
        print("  → Disable legacy camera in raspi-config")
        print("  → Reboot the Pi")
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
        # Run Flask server
        # Use host='0.0.0.0' to allow external connections
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n\n✓ Shutting down server...")
    finally:
        if picam2:
            picam2.stop()
            print("✓ Camera stopped")
        print("✓ Server stopped")