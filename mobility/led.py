import RPi.GPIO as GPIO  # Import the GPIO module
import time

def setup():
    GPIO.setmode(GPIO.BOARD)         # Set the GPIO pin numbering scheme to BOARD
    GPIO.setwarnings(False)          # Disable warnings
    GPIO.setup(40, GPIO.OUT)         # Physical pin 40 corresponds to GPIO 21
    GPIO.setup(38, GPIO.OUT)         # Physical pin 38 corresponds to GPIO 20
    GPIO.setup(36, GPIO.OUT)         # Physical pin 36 corresponds to GPIO 16

def set_LED(LED):
    led_pins = {
        'RED': 40,                   # Physical pin 40
        'YELLOW': 38,                # Physical pin 38
        'GREEN': 36                  # Physical pin 36
    }
    
    if LED == 'RED':
        GPIO.output(led_pins['RED'], GPIO.HIGH)
        GPIO.output(led_pins['YELLOW'], GPIO.LOW)
        GPIO.output(led_pins['GREEN'], GPIO.LOW)
    elif LED == 'YELLOW':
        GPIO.output(led_pins['RED'], GPIO.HIGH)
        GPIO.output(led_pins['GREEN'], GPIO.HIGH)
        GPIO.output(led_pins['YELLOW'], GPIO.LOW)
    elif LED == 'GREEN':
        GPIO.output(led_pins['RED'], GPIO.LOW)
        GPIO.output(led_pins['YELLOW'], GPIO.LOW)
        GPIO.output(led_pins['GREEN'], GPIO.HIGH)

def test():
    set_LED('RED')  # Set the LED to red
    time.sleep(0.5)
    set_LED('YELLOW')  # Set the LED to yellow
    time.sleep(0.5)
    set_LED('GREEN')  # Set the LED to green
    time.sleep(0.5)

setup()
test()


