import RPi.GPIO as GPIO  # Import the GPIO module
import time

def setup():
    GPIO.setmode(GPIO.BCM)         # Set the GPIO pin numbering scheme to BOARD
    GPIO.setup(21, GPIO.OUT)         # GPIO 21 = Physical pin 40 = RED
    GPIO.setup(20, GPIO.OUT)         # GPIO 20 = Physical pin 38 = GREEN
    GPIO.setup(16, GPIO.OUT)         # GPIO 16 = Physical pin 36 = BLUE

def set_LED(LED):
    if LED == 'RED':
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)
    elif LED == 'YELLOW':
        GPIO.output(21, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(20, GPIO.LOW)
    elif LED == 'GREEN':
        GPIO.output(21, GPIO.LOW)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.HIGH)
    elif LED == 'OFF':
        GPIO.output(21, GPIO.LOW)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.LOW)