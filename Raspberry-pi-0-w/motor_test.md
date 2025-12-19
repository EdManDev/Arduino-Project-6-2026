# L298N Motor Driver Diagnostic Tool

A comprehensive diagnostic utility for testing L298N motor driver connections on Raspberry Pi. This tool systematically tests each motor individually and together, helping you verify wiring and troubleshoot motor control issues.

## Features

- 🔍 Individual motor testing (forward and backward)
- ⚡ PWM speed testing at multiple levels
- 🔄 Both motors simultaneous testing
- 📊 Detailed voltage checking guide
- 🛡️ Safety checks and warnings
- 📝 Clear diagnostic output with pin states

## Hardware Requirements

### Components
- Raspberry Pi (any model with GPIO)
- L298N H-Bridge motor driver module
- 2x DC motors
- Motor power supply (6-12V)
- Connecting wires

### Wiring Configuration

The script uses these GPIO pins (BCM numbering):

| Component | GPIO Pin | L298N Pin | Description |
|-----------|----------|-----------|-------------|
| Left Motor IN1 | GPIO 17 | IN1 | Left motor direction control |
| Left Motor IN2 | GPIO 27 | IN2 | Left motor direction control |
| Left Motor EN | GPIO 18 | ENA | Left motor speed (PWM) |
| Right Motor IN3 | GPIO 22 | IN3 | Right motor direction control |
| Right Motor IN4 | GPIO 23 | IN4 | Right motor direction control |
| Right Motor EN | GPIO 24 | ENB | Right motor speed (PWM) |

### L298N Connections

```
Raspberry Pi          L298N          Motors/Power
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO 17        →      IN1
GPIO 27        →      IN2
GPIO 18        →      ENA
GPIO 22        →      IN3
GPIO 23        →      IN4
GPIO 24        →      ENB
GND            →      GND
                      12V      ←    + Power Supply (6-12V)
                      GND      ←    - Power Supply
                      OUT1/OUT2 →   Left Motor
                      OUT3/OUT4 →   Right Motor
```

**IMPORTANT:** Remove the ENA and ENB jumpers from the L298N to enable PWM speed control!

## Installation

1. **Install RPi.GPIO library:**
```bash
sudo apt update
sudo apt install python3-rpi.gpio
```

Or using pip:
```bash
pip3 install RPi.GPIO
```

2. **Download the script:**
```bash
# Save motor_test.py to your project directory
chmod +x motor_test.py
```

## Usage

### Running the Diagnostic

```bash
python3 motor_test.py
```

Or if made executable:
```bash
./motor_test.py
```

### Test Sequence

The script runs through these tests automatically:

1. **Individual Motor Tests:**
   - Left motor forward (2 seconds)
   - Left motor backward (2 seconds)
   - Right motor forward (2 seconds)
   - Right motor backward (2 seconds)

2. **Both Motors Together:**
   - Both motors forward simultaneously (2 seconds)

3. **Speed Variations:**
   - Both motors at 50% speed (2 seconds)
   - Both motors at 75% speed (2 seconds)
   - Both motors at 100% speed (2 seconds)

4. **Voltage Check Guide:**
   - Instructions for measuring key voltages with a multimeter

### Safety Precautions

⚠️ **Before running the test:**
- Ensure motors are mounted on wheels/stand (not touching any surface)
- Verify motor power supply is connected (6-12V to L298N 12V terminal)
- Check all wires are securely connected
- Keep hands and objects clear of moving parts
- Have an emergency stop method ready (Ctrl+C)

## Interpreting Results

### Successful Test
If everything is working correctly, you should observe:
- Each motor spinning in the specified direction
- Smooth speed changes during speed tests
- Clear console output showing pin states

### Troubleshooting

#### No Motors Moving

**Check these in order:**

1. **Power Supply:**
   - Measure voltage at L298N 12V terminal (should be 6-12V)
   - Ensure power supply can provide sufficient current (typically 1-2A per motor)

2. **L298N Jumpers:**
   - **Remove ENA and ENB jumpers** to enable PWM control
   - If jumpers are in place, motors will only run at full speed when enabled

3. **Motor Connections:**
   - Verify OUT1 & OUT2 connected to left motor
   - Verify OUT3 & OUT4 connected to right motor
   - Test motors directly with battery to confirm they work

4. **GPIO Connections:**
   - Verify all GPIO wires match the pin configuration in the code
   - Check for loose connections
   - Ensure Pi GND is connected to L298N GND

#### Only Some Motors Moving

1. **For non-working motor:**
   - Check specific GPIO connections (IN pins and EN pin)
   - Test motor directly with battery
   - Try swapping motor connections to isolate driver vs motor issue

2. **Verify L298N pins:**
   - Measure voltage on OUT pins when motor should be running
   - Check continuity from GPIO to L298N pins

#### Motors Running Opposite Direction

If motors spin in the wrong direction:
- Swap the two wires for that motor (OUT1↔OUT2 or OUT3↔OUT4)
- Or modify the code to reverse the IN pin signals

## Voltage Testing Guide

Use a multimeter to measure these voltages while a test is running:

| Measurement Point | Expected Voltage | What It Indicates |
|------------------|------------------|-------------------|
| GPIO EN pin to GND | ~3.3V | Pi is sending PWM signal |
| L298N 12V to GND | 6-12V | Motor power supply connected |
| L298N 5V to GND | ~5V | L298N regulator working |
| OUT1 to OUT2 | ~Motor voltage | Left motor receiving power |
| OUT3 to OUT4 | ~Motor voltage | Right motor receiving power |

## Pin Configuration Customization

If you need to use different GPIO pins, modify these variables at the top of the script:

```python
MOTOR_LEFT_IN1 = 17   # Change to your pin
MOTOR_LEFT_IN2 = 27   # Change to your pin
MOTOR_RIGHT_IN3 = 22  # Change to your pin
MOTOR_RIGHT_IN4 = 23  # Change to your pin
MOTOR_LEFT_EN = 18    # Change to your pin (must support PWM)
MOTOR_RIGHT_EN = 24   # Change to your pin (must support PWM)
```

**Note:** EN pins must be PWM-capable GPIO pins.

## Common Issues and Solutions

### Issue: "Permission denied" error
**Solution:**
```bash
sudo python3 motor_test.py
```
GPIO access may require root privileges on some systems.

### Issue: Motors jitter or move erratically
**Possible causes:**
- Insufficient power supply current
- Loose connections
- Defective L298N module
- EMI from motors affecting Pi

### Issue: Motors run but very slowly
**Check:**
- Power supply voltage (should be 6-12V, not 5V)
- Battery charge level
- Motor specifications match power supply
- PWM duty cycle in code

### Issue: L298N gets very hot
**This is normal** if:
- Running motors at high loads
- Motors are stalled or blocked
- Using high voltage (12V)

**Add a heatsink** to the L298N chip if it gets too hot to touch.

## Integration with Main Project

This diagnostic tool uses the same pin configuration as your main project. Once you've verified everything works with this test, your main motor control code should work correctly.

To use these settings in your main project:
```python
from motor_test import (
    MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_LEFT_EN,
    MOTOR_RIGHT_IN3, MOTOR_RIGHT_IN4, MOTOR_RIGHT_EN
)
```

## Advanced Testing

### Manual Motor Control

You can modify the script to test specific scenarios:

```python
# Test specific speed
test_left_motor_forward(pwm_left, speed=60)

# Test for longer duration
time.sleep(5)  # Run for 5 seconds

# Test turning
GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)   # Left forward
GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)   # Right backward
GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)
pwm_left.ChangeDutyCycle(100)
pwm_right.ChangeDutyCycle(100)
```

## License

This diagnostic tool is provided as-is for testing and troubleshooting purposes.

## Contributing

Feel free to modify and improve this diagnostic tool for your specific needs. If you add useful features, consider sharing them!

---

**Happy Testing! 🤖**