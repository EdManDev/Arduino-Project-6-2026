# Raspberry Pi Camera Live Streaming Server

A lightweight Flask-based web server for streaming live video from a Raspberry Pi camera module (OV5647) over your local network. Optimized for Raspberry Pi Zero W with network access restrictions for security.

## Features

- 📹 Live MJPEG video streaming at 640x480 @ 30fps
- 🔒 Network-restricted access (192.168.1.x only)
- 🎨 Clean, responsive web interface
- ⚡ Optimized for Raspberry Pi Zero W performance
- 🔍 Built-in camera diagnostics and troubleshooting
- 📊 Health check endpoint for monitoring

## Requirements

### Hardware
- Raspberry Pi Zero W (or any Pi model)
- OV5647 Arducam camera module
- Properly connected camera cable

### Software
- Raspberry Pi OS (Bullseye or later)
- Python 3.7+
- `picamera2` library
- Flask

## Installation

1. **Update your system:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install required packages:**
```bash
sudo apt install -y python3-pip python3-picamera2 python3-flask
```

3. **Install Python dependencies:**
```bash
pip3 install flask picamera2
```

4. **Enable the camera interface:**
```bash
sudo raspi-config
```
- Navigate to: `Interface Options` → `Legacy Camera` → **Disable**
- Reboot: `sudo reboot`

5. **Download the script:**
```bash
# Save main.py to your desired directory
chmod +x main.py
```

## Configuration

### Network Access

By default, the server only accepts connections from:
- `192.168.1.x` subnet
- `127.0.0.1` (localhost)

To change the allowed network, edit this line in `main.py`:
```python
ALLOWED_NETWORK = "192.168.1."  # Change to your network prefix
```

### Camera Settings

You can modify the resolution and frame rate in the `init_camera()` function:
```python
config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # Change resolution here
    lores={"size": (320, 240)},
    display="lores",
    encode="main"
)
```

## Usage

### Starting the Server

```bash
python3 main.py
```

You should see output like:
```
==================================================
Raspberry Pi Camera Streaming Server
==================================================
✓ Camera initialized successfully

✓ Server starting...
✓ Access restricted to: 192.168.1.
✓ Access the stream at:
  → http://192.168.1.x:5000
  → http://localhost:5000 (from Pi only)

Press Ctrl+C to stop
```

### Accessing the Stream

Open a web browser on any device in your local network and navigate to:
```
http://<your-pi-ip-address>:5000
```

To find your Pi's IP address:
```bash
hostname -I
```

### Endpoints

- `/` - Main streaming page with video feed
- `/video_feed` - Raw MJPEG stream endpoint
- `/status` - JSON health check endpoint

## Troubleshooting

### Camera Not Detected

If you see "No cameras detected", try these steps:

1. **Check camera connection:**
   - Ensure the camera cable is properly seated
   - Check that the cable is inserted in the correct orientation

2. **Verify camera detection:**
```bash
libcamera-hello --list-cameras
vcgencmd get_camera
```

3. **Disable legacy camera:**
```bash
sudo raspi-config
# Interface Options → Legacy Camera → Disable
sudo reboot
```

4. **Check for errors:**
```bash
dmesg | grep -i camera
```

### Connection Issues

- **403 Forbidden Error:** Your device is not on the allowed network. Check the `ALLOWED_NETWORK` setting.
- **Can't connect:** Ensure your Pi and client device are on the same network.
- **Firewall issues:** The Pi doesn't typically have a firewall enabled, but check with `sudo ufw status`.

### Performance Issues

For better performance on Pi Zero W:
- Lower the resolution to 320x240
- Reduce frame rate if needed
- Ensure good power supply (2.5A recommended)
- Close unnecessary applications

## Running on Startup

To start the server automatically on boot:

1. **Create a systemd service:**
```bash
sudo nano /etc/systemd/system/picamera-stream.service
```

2. **Add this content:**
```ini
[Unit]
Description=Pi Camera Streaming Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. **Enable and start:**
```bash
sudo systemctl enable picamera-stream.service
sudo systemctl start picamera-stream.service
```

4. **Check status:**
```bash
sudo systemctl status picamera-stream.service
```

## Security Notes

- This server is restricted to local network access only
- Do **not** expose this server directly to the internet without proper authentication
- Consider adding HTTPS/SSL if deploying in production
- The IP restriction is basic; for higher security needs, implement proper authentication

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Made for Raspberry Pi enthusiasts 🥧**