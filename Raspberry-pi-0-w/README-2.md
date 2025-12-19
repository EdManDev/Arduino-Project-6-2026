# Raspberry Pi Camera Live Streaming Server

A Flask-based camera streaming server for Raspberry Pi with built-in QR code scanning capabilities. Optimized for Raspberry Pi Zero W with OV5647 camera module.

## Features

- 📹 Live MJPEG video streaming at 640x480 @ 30fps
- 🔍 Real-time QR code detection and decoding
- 🔒 Network access restriction (local network only)
- 🎨 Modern, responsive web interface
- 📱 Mobile-friendly design
- 🔄 Automatic image rotation (180°)

## Hardware Requirements

- Raspberry Pi Zero W (or any Raspberry Pi model)
- OV5647 Arducam camera module
- MicroSD card with Raspberry Pi OS
- Power supply

## Software Requirements

- Python 3.7+
- Raspberry Pi OS (Bullseye or newer with libcamera support)

## Installation

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install System Dependencies

```bash
sudo apt install -y python3-pip python3-opencv libzbar0
```

### 3. Enable Camera

```bash
sudo raspi-config
```

Navigate to:
- `Interface Options` → `Legacy Camera` → **Disable**
- Reboot after making changes

### 4. Install Python Dependencies

```bash
pip3 install flask picamera2 pyzbar opencv-python-headless numpy
```

### 5. Test Camera

```bash
libcamera-hello --list-cameras
```

You should see your camera listed (e.g., "imx219" or "ov5647").

## Configuration

### Network Access

By default, the server restricts access to the `192.168.1.x` network range. To change this, edit the `ALLOWED_NETWORK` variable in `main.py`:

```python
ALLOWED_NETWORK = "192.168.1."  # Change to your network prefix
```

### Camera Rotation

The camera is configured to rotate 180° by default. To adjust rotation, modify the `Transform` parameter in the `init_camera()` function:

```python
# Current: 180° rotation
transform=Transform(hflip=True, vflip=True)

# 90° clockwise
transform=Transform(hflip=True, vflip=False, transpose=True)

# 90° counter-clockwise
transform=Transform(hflip=False, vflip=True, transpose=True)

# No rotation
transform=Transform()
```

## Usage

### Start the Server

```bash
python3 main.py
```

### Access the Stream

Open a web browser and navigate to:
```
http://<raspberry-pi-ip>:5000
```

To find your Pi's IP address:
```bash
hostname -I
```

### Endpoints

- `/` - Main streaming page with QR scanner
- `/video_feed` - Raw MJPEG video stream
- `/scan_qr` - QR code scanning API endpoint (JSON)
- `/status` - Health check endpoint

## QR Code Scanner

The QR code scanner runs automatically when you access the main page. Simply point the camera at a QR code, and detected codes will appear in the scanner panel with:
- Decoded data
- QR code type
- Detection timestamp

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is recognized
libcamera-hello --list-cameras

# Check camera detection
vcgencmd get_camera

# Verify camera interface
sudo raspi-config
# Ensure Legacy Camera is DISABLED
```

### Permission Issues

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Reboot
sudo reboot
```

### Port Already in Use

Change the port in `main.py`:
```python
app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
```

### Low Frame Rate on Pi Zero W

The Pi Zero W has limited processing power. If streaming is slow:
- Reduce resolution in `init_camera()`
- Lower frame rate
- Disable QR scanning if not needed

## Running as a Service

To run the server automatically on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/picamera.service
```

Add the following content:

```ini
[Unit]
Description=Pi Camera Streaming Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/camera-server
ExecStart=/usr/bin/python3 /home/pi/camera-server/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable picamera.service
sudo systemctl start picamera.service
sudo systemctl status picamera.service
```

## Security Notes

- The server restricts access to local network IPs only
- Change `ALLOWED_NETWORK` to match your network
- Do not expose port 5000 to the internet without additional security measures
- Consider adding authentication for production use

## Performance Tips

- **Pi Zero W**: Use 640x480 or lower resolution
- **Pi 3/4**: Can handle 1080p streaming
- Reduce `lores` size if QR scanning is slow
- Adjust JPEG quality in `MJPEGEncoder()` if needed

## License

MIT License - Feel free to modify and distribute

## Credits

- Built with Flask, Picamera2, and OpenCV
- QR code detection powered by pyzbar
- Designed for Raspberry Pi Zero W

## Support

For issues and feature requests, check:
- Raspberry Pi Camera documentation: https://www.raspberrypi.com/documentation/cameras/
- Picamera2 library: https://github.com/raspberrypi/picamera2
- libcamera troubleshooting: https://www.raspberrypi.com/documentation/computers/camera_software.html