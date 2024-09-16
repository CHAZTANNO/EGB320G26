import RPi.GPIO as GPIO
import time

# GPIO mode setup
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
TRIG = 14
ECHO = 18

# Set up GPIO pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def distance():
    # Send a 10µs pulse to trigger the sensor
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.05)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
    
    # Wait for the echo pin to go HIGH
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()
    
    # Wait for the echo pin to go LOW again
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()
    
    # Calculate pulse duration and distance
    if 'pulse_end' in locals() and 'pulse_start' in locals():
        pulse_duration = pulse_end - pulse_start
        distance_cm = pulse_duration * 17150
        distance_cm = round(distance_cm, 2)
    else:
        distance_cm = None
    
    return distance_cm

try:
    while True:
        dist = distance()
        if dist is not None:
            print(f"Distance: {dist} cm")
        else:
            print("Failed to get reading.")
except KeyboardInterrupt:
    print("Measurement stopped by User")
finally:
    GPIO.cleanup()
