# 🤖 Raspberry Pi Camera & Motor Control Server

A Flask-based web server for Raspberry Pi Zero W that provides live camera streaming, QR code scanning, and motor control capabilities. Perfect for building remote-controlled robots or surveillance systems.

## ✨ Features

- 📹 **Live Camera Streaming** - Real-time MJPEG video stream from OV5647 camera
- 🔍 **QR Code Scanner** - Automatic QR code detection and decoding
- 🎮 **Motor Control** - Web-based interface to control DC motors via L298N driver
- 🔒 **Network Security** - Restricts access to local network only
- 📱 **Mobile Friendly** - Touch-optimized controls for smartphones and tablets
- ⚡ **PWM Speed Control** - Adjustable motor speed (0-100%)

## 🛠️ Hardware Requirements

### Required Components
- Raspberry Pi Zero W (or any Raspberry Pi with GPIO)
- OV5647 Camera Module (Arducam compatible)
- L298N Motor Driver Module
- 2x DC Motors
- Power supply for motors (6-12V recommended)
- Jumper wires
- Micro SD card (8GB+ recommended)

### Optional Components
- Robot chassis
- Battery pack
- Motor wheels

## 🔌 Wiring Diagram

### Camera Connection
```
Raspberry Pi Zero W → OV5647 Camera
-----------------------------------
CSI Port → Camera Ribbon Cable
```

### Motor Driver Connection
```
Raspberry Pi Zero W    →    L298N Motor Driver
------------------------------------------------
GPIO 17 (Pin 11)       →    IN1 (Left Motor Direction)
GPIO 27 (Pin 13)       →    IN2 (Left Motor Direction)
GPIO 22 (Pin 15)       →    IN3 (Right Motor Direction)
GPIO 23 (Pin 16)       →    IN4 (Right Motor Direction)
GPIO 18 (Pin 12, PWM)  →    ENA (Left Motor Speed)
GPIO 24 (Pin 18, PWM)  →    ENB (Right Motor Speed)
GND (Pin 6, 9, etc.)   →    GND
5V (Pin 2 or 4)        →    5V (Logic Power)
```

### Motor Driver to Motors
```
L298N Motor Driver     →    DC Motors
---------------------------------------
OUT1                   →    Left Motor (+)
OUT2                   →    Left Motor (-)
OUT3                   →    Right Motor (+)
OUT4                   →    Right Motor (-)

External Power         →    Motor Driver
---------------------------------------
Battery (+) 6-12V      →    12V Input
Battery (-)            →    GND
```

**⚠️ Important:** 
- Remove the 5V jumper on L298N if using external power
- Ensure common ground between Raspberry Pi and motor power supply
- Use adequate power supply for motors (500mA+ per motor)

## 📋 Software Requirements

### System Requirements
- Raspberry Pi OS (Bullseye or later)
- Python 3.7+
- Enabled camera interface
- Internet connection (for initial setup)

### Python Dependencies
```bash
flask
picamera2
pyzbar
opencv-python
numpy
RPi.GPIO
libcamera
```

## 🚀 Installation

### 1. Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Enable Camera
```bash
sudo raspi-config
```
- Navigate to: **Interface Options** → **Camera** → **Enable**
- Ensure **Legacy Camera** is **DISABLED**
- Reboot: `sudo reboot`

### 3. Install System Dependencies
```bash
sudo apt install -y python3-pip python3-opencv libcamera-apps
sudo apt install -y libzbar0 python3-libcamera python3-picamera2
```

### 4. Install Python Packages
```bash
pip3 install flask picamera2 pyzbar opencv-python numpy RPi.GPIO
```

### 5. Test Camera
```bash
libcamera-hello --list-cameras
```
You should see your camera detected.

### 6. Clone or Download Code
```bash
mkdir ~/pi-robot
cd ~/pi-robot
# Copy main.py to this directory
```

### 7. Configure Network Access (Optional)
Edit the `ALLOWED_NETWORK` variable in `main.py` if your local network uses a different subnet:
```python
ALLOWED_NETWORK = "192.168.1."  # Change to match your network
```

## 🎯 Usage

### Starting the Server

**First time or after errors:**
```bash
cd ~/pi-robot

# Clean up GPIO (if needed)
sudo pkill -9 python3
python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()"

# Start the server
python3 main.py
```

**Normal startup:**
```bash
cd ~/pi-robot
python3 main.py
```

**If you get GPIO errors, try with sudo:**
```bash
sudo python3 main.py
```

### Accessing the Interface
Once started, you'll see output like:
```
✓ GPIO initialized successfully
✓ Camera initialized successfully (rotated 180°)
✓ Server starting...
✓ Access the stream at:
  → http://192.168.1.X:5000
```

Open the URL in your web browser (computer, phone, or tablet on the same network).

### Motor Controls
- **⬆️ Forward** - Move forward
- **⬇️ Backward** - Move backward
- **⬅️ Left** - Turn left (pivot)
- **➡️ Right** - Turn right (pivot)
- **⏹️ Stop** - Stop all motors
- **Speed Slider** - Adjust motor speed (0-100%)

**Controls:**
- **Click/Tap briefly**: Motor runs for a moment then stops
- **Hold button**: Motor runs continuously until you release
- **Release or drag off**: Motor stops immediately
- **Stop button**: Emergency stop for all motors

### QR Code Scanner
Point the camera at any QR code, and it will automatically detect and display the contents in real-time.

## 🔧 Configuration

### Creating a GPIO Cleanup Script (Recommended)

Create a helper script to clean up GPIO before starting:

```bash
nano ~/pi-robot/cleanup_gpio.sh
```

Add this content:
```bash
#!/bin/bash
echo "🧹 Cleaning up GPIO..."
sudo pkill -9 python3 2>/dev/null
python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()" 2>/dev/null
echo "✓ GPIO cleaned up successfully"
```

Make it executable:
```bash
chmod +x ~/pi-robot/cleanup_gpio.sh
```

Use it before starting your server:
```bash
cd ~/pi-robot
./cleanup_gpio.sh
python3 main.py
```

### Changing GPIO Pins
Edit the pin assignments in `main.py`:
```python
MOTOR_LEFT_IN1 = 17   # Change to your preferred GPIO
MOTOR_LEFT_IN2 = 27
MOTOR_RIGHT_IN3 = 22
MOTOR_RIGHT_IN4 = 23
MOTOR_LEFT_EN = 18    # PWM pin
MOTOR_RIGHT_EN = 24   # PWM pin
```

### Adjusting Camera Settings
Modify camera configuration in `init_camera()` function:
```python
config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # Change resolution
    # ...
)
```

### Changing Default Speed
```python
DEFAULT_SPEED = 80  # 80% speed (0-100)
```

## 🔄 Auto-Start on Boot (Optional)

### Using systemd

1. Create service file:
```bash
sudo nano /etc/systemd/system/pi-robot.service
```

2. Add content:
```ini
[Unit]
Description=Pi Camera and Motor Control Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/pi-robot
ExecStartPre=/usr/bin/python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()"
ExecStart=/usr/bin/python3 /home/pi/pi-robot/main.py
Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable pi-robot.service
sudo systemctl start pi-robot.service
```

4. Check status:
```bash
sudo systemctl status pi-robot.service
```

5. View logs:
```bash
journalctl -u pi-robot.service -f
```

6. Stop/disable service:
```bash
sudo systemctl stop pi-robot.service
sudo systemctl disable pi-robot.service
```

## 🐛 Troubleshooting

### GPIO Errors ("GPIO not allocated" or "Permission denied")

**Solution 1: Clean up GPIO**
```bash
sudo pkill -9 python3
python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()"
python3 main.py
```

**Solution 2: Run with sudo**
```bash
sudo python3 main.py
```

**Solution 3: Add user to GPIO group**
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

**Solution 4: Create cleanup script (recommended)**
```bash
# Create the script
echo '#!/bin/bash
sudo pkill -9 python3 2>/dev/null
python3 -c "import RPi.GPIO as GPIO; GPIO.cleanup()" 2>/dev/null
echo "✓ GPIO cleaned up"' > ~/pi-robot/cleanup_gpio.sh

# Make executable
chmod +x ~/pi-robot/cleanup_gpio.sh

# Use before starting
./cleanup_gpio.sh && python3 main.py
```

### Camera Not Detected
```bash
# Check camera detection
libcamera-hello --list-cameras

# Check camera config
vcgencmd get_camera

# Verify ribbon cable connection
# Ensure legacy camera is disabled in raspi-config
```

### Motors Not Responding

**Check 1: Power Supply**
- Verify 6-12V power connected to L298N's 12V terminal
- Check battery/power supply has sufficient current (1A+ per motor)
- The 5V from Raspberry Pi is NOT enough for motors

**Check 2: L298N Jumper Configuration**
- **ENA jumper**: Should be REMOVED (we use PWM from GPIO 18)
- **ENB jumper**: Should be REMOVED (we use PWM from GPIO 24)
- **5V jumper**: Remove if using external motor power (6-12V)

**Check 3: Run Diagnostic Test**
```bash
cd ~/pi-robot
python3 motor_test.py
```

**Check 4: Verify Connections**
- Test GPIO pins output ~3.3V when active (use multimeter)
- Verify motor power supply outputs correct voltage
- Check all wires are securely connected
- Test motors directly with battery to confirm they work

**Check 5: Button Behavior**
- Motors should stop immediately when button is released
- If motors keep running, try refreshing the webpage
- Check browser console for JavaScript errors (F12)

### Motors Keep Running After Button Release
- **Refresh the webpage** - Browser cache might have old JavaScript
- **Clear browser cache** - Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
- **Try a different browser** - Test with Chrome, Firefox, or Safari
- **Check JavaScript console** - Press F12 and look for errors

### Permission Errors
```bash
# Add user to GPIO group
sudo usermod -a -G gpio $USER

# Reboot
sudo reboot
```

**Alternative: Run with sudo**
```bash
sudo python3 main.py
```

### Web Interface Not Loading
- Check firewall settings: `sudo ufw status`
- Verify Pi's IP address: `hostname -I`
- Ensure you're on the same network as the Pi
- Try accessing via: `http://raspberrypi.local:5000`

### QR Code Not Scanning
- Ensure adequate lighting
- Hold QR code steady and in focus
- Try different distances from camera
- Check if zbar is installed: `dpkg -l | grep zbar`

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/video_feed` | GET | MJPEG video stream |
| `/motor_control` | POST | Send motor commands |
| `/motor_speed` | POST | Update motor speed |
| `/scan_qr` | GET | Scan for QR codes |
| `/status` | GET | Health check |

### Example API Usage
```bash
# Move forward at 80% speed
curl -X POST http://192.168.1.X:5000/motor_control \
  -H "Content-Type: application/json" \
  -d '{"command":"forward","speed":80}'

# Stop motors
curl -X POST http://192.168.1.X:5000/motor_control \
  -H "Content-Type: application/json" \
  -d '{"command":"stop"}'
```

## 🔒 Security Notes

- Server only accepts connections from `192.168.1.x` network by default
- Change `ALLOWED_NETWORK` constant to match your network
- No authentication implemented - add if exposing to internet
- Never expose directly to the internet without proper security measures

## 🎨 Customization Ideas

- Add obstacle detection with ultrasonic sensors
- Implement autonomous navigation
- Add joystick control via WebSocket
- Record video to file
- Integrate with voice commands
- Add LED indicators for status
- Implement battery level monitoring
- Create waypoint navigation

## 📝 License

This project is provided as-is for educational and hobby purposes.

## 🤝 Contributing

Feel free to fork, modify, and improve this project!

## 📧 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run the diagnostic test: `python3 motor_test.py`
3. Clean up GPIO: `./cleanup_gpio.sh`
4. Verify all connections match the wiring diagram
5. Test components individually (camera, then motors)
6. Review system logs: `journalctl -u pi-robot.service` (if using systemd)
7. Check for GPIO conflicts: `ps aux | grep python`

## 🔧 Quick Commands Reference

```bash
# Clean up GPIO
./cleanup_gpio.sh

# Start server
python3 main.py

# Start with sudo (if permission errors)
sudo python3 main.py

# Test motors
python3 motor_test.py

# Check running processes
ps aux | grep python

# Kill all Python processes
sudo pkill -9 python3

# View service logs
journalctl -u pi-robot.service -f
```

## 🙏 Acknowledgments

- Built with Flask, Picamera2, and RPi.GPIO
- Inspired by the maker community

---

**Happy Building! 🚀**