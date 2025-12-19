#!/usr/bin/env python3
"""
Motor Driver Diagnostic Tool
Tests L298N motor driver connections
"""

import RPi.GPIO as GPIO
import time

# Pin configuration (match your main.py)
MOTOR_LEFT_IN1 = 17
MOTOR_LEFT_IN2 = 27
MOTOR_RIGHT_IN3 = 22
MOTOR_RIGHT_IN4 = 23
MOTOR_LEFT_EN = 18
MOTOR_RIGHT_EN = 24

def setup():
    """Initialize GPIO"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    GPIO.setup(MOTOR_LEFT_IN1, GPIO.OUT)
    GPIO.setup(MOTOR_LEFT_IN2, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_IN3, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_IN4, GPIO.OUT)
    GPIO.setup(MOTOR_LEFT_EN, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_EN, GPIO.OUT)
    
    # Setup PWM
    pwm_left = GPIO.PWM(MOTOR_LEFT_EN, 1000)
    pwm_right = GPIO.PWM(MOTOR_RIGHT_EN, 1000)
    pwm_left.start(0)
    pwm_right.start(0)
    
    return pwm_left, pwm_right

def stop_all():
    """Stop all motors"""
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    print("✓ All motors stopped")

def test_left_motor_forward(pwm_left, speed=100):
    """Test left motor forward"""
    print(f"\n→ Testing LEFT motor FORWARD at {speed}% speed...")
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    print(f"  IN1 (GPIO {MOTOR_LEFT_IN1}): HIGH")
    print(f"  IN2 (GPIO {MOTOR_LEFT_IN2}): LOW")
    print(f"  EN (GPIO {MOTOR_LEFT_EN}): {speed}% PWM")
    time.sleep(2)
    stop_all()

def test_left_motor_backward(pwm_left, speed=100):
    """Test left motor backward"""
    print(f"\n→ Testing LEFT motor BACKWARD at {speed}% speed...")
    GPIO.output(MOTOR_LEFT_IN1, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    print(f"  IN1 (GPIO {MOTOR_LEFT_IN1}): LOW")
    print(f"  IN2 (GPIO {MOTOR_LEFT_IN2}): HIGH")
    print(f"  EN (GPIO {MOTOR_LEFT_EN}): {speed}% PWM")
    time.sleep(2)
    stop_all()

def test_right_motor_forward(pwm_right, speed=100):
    """Test right motor forward"""
    print(f"\n→ Testing RIGHT motor FORWARD at {speed}% speed...")
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    pwm_right.ChangeDutyCycle(speed)
    print(f"  IN3 (GPIO {MOTOR_RIGHT_IN3}): HIGH")
    print(f"  IN4 (GPIO {MOTOR_RIGHT_IN4}): LOW")
    print(f"  EN (GPIO {MOTOR_RIGHT_EN}): {speed}% PWM")
    time.sleep(2)
    stop_all()

def test_right_motor_backward(pwm_right, speed=100):
    """Test right motor backward"""
    print(f"\n→ Testing RIGHT motor BACKWARD at {speed}% speed...")
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.HIGH)
    pwm_right.ChangeDutyCycle(speed)
    print(f"  IN3 (GPIO {MOTOR_RIGHT_IN3}): LOW")
    print(f"  IN4 (GPIO {MOTOR_RIGHT_IN4}): HIGH")
    print(f"  EN (GPIO {MOTOR_RIGHT_EN}): {speed}% PWM")
    time.sleep(2)
    stop_all()

def test_both_forward(pwm_left, pwm_right, speed=100):
    """Test both motors forward"""
    print(f"\n→ Testing BOTH motors FORWARD at {speed}% speed...")
    GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)
    time.sleep(2)
    stop_all()

def voltage_check():
    """Guide for voltage checking"""
    print("\n" + "="*60)
    print("VOLTAGE CHECK GUIDE")
    print("="*60)
    print("\nWith a multimeter, measure these voltages:")
    print(f"\n1. GPIO {MOTOR_LEFT_EN} to GND:")
    print("   Should be ~3.3V when motor is running")
    print(f"\n2. L298N 12V terminal to GND:")
    print("   Should be 6-12V (your motor power supply)")
    print(f"\n3. L298N 5V terminal to GND:")
    print("   Should be ~5V (from Pi or L298N regulator)")
    print(f"\n4. Between OUT1 and OUT2 (left motor):")
    print("   Should be ~motor voltage when running")
    print(f"\n5. Between OUT3 and OUT4 (right motor):")
    print("   Should be ~motor voltage when running")
    print("\n" + "="*60)

def main():
    print("="*60)
    print("L298N MOTOR DRIVER DIAGNOSTIC TEST")
    print("="*60)
    print("\n⚠️  SAFETY CHECKS:")
    print("  1. Motors should be on wheels/stand (not on surface)")
    print("  2. Motor power supply connected (6-12V to L298N)")
    print("  3. All wires securely connected")
    print("  4. Keep hands clear of moving parts")
    print("\nPress ENTER to continue or Ctrl+C to cancel...")
    input()
    
    try:
        pwm_left, pwm_right = setup()
        print("\n✓ GPIO initialized successfully")
        
        # Test individual motors
        print("\n" + "="*60)
        print("TESTING INDIVIDUAL MOTORS")
        print("="*60)
        
        test_left_motor_forward(pwm_left, 100)
        time.sleep(1)
        
        test_left_motor_backward(pwm_left, 100)
        time.sleep(1)
        
        test_right_motor_forward(pwm_right, 100)
        time.sleep(1)
        
        test_right_motor_backward(pwm_right, 100)
        time.sleep(1)
        
        # Test both motors
        print("\n" + "="*60)
        print("TESTING BOTH MOTORS TOGETHER")
        print("="*60)
        
        test_both_forward(pwm_left, pwm_right, 100)
        
        # Speed test
        print("\n" + "="*60)
        print("TESTING DIFFERENT SPEEDS")
        print("="*60)
        
        for speed in [50, 75, 100]:
            print(f"\n→ Testing at {speed}% speed...")
            GPIO.output(MOTOR_LEFT_IN1, GPIO.HIGH)
            GPIO.output(MOTOR_LEFT_IN2, GPIO.LOW)
            GPIO.output(MOTOR_RIGHT_IN3, GPIO.HIGH)
            GPIO.output(MOTOR_RIGHT_IN4, GPIO.LOW)
            pwm_left.ChangeDutyCycle(speed)
            pwm_right.ChangeDutyCycle(speed)
            time.sleep(2)
            stop_all()
            time.sleep(1)
        
        print("\n" + "="*60)
        print("DIAGNOSTIC TEST COMPLETE")
        print("="*60)
        
        voltage_check()
        
        print("\n📊 RESULTS:")
        print("  → Did any motors move? (yes/no)")
        print("  → If NO motors moved:")
        print("     - Check power supply to L298N 12V terminal")
        print("     - Verify motor connections to OUT1-OUT4")
        print("     - Check GPIO connections match the code")
        print("     - Ensure ENA/ENB jumpers are REMOVED")
        print("  → If only some motors moved:")
        print("     - Check wiring for non-working motors")
        print("     - Test motor directly with battery")
        print("     - Verify all GPIO pins are connected")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_all()
        GPIO.cleanup()
        print("\n✓ GPIO cleanup complete")

if __name__ == '__main__':
    main()
