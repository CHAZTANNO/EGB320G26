import RPi.GPIO as GPIO			# Import the GPIO module

def setup():
    GPIO.setmode(GPIO.BOARD)		# Set the GPIO pin numbering scheme to BOARD
    GPIO.setup(21, GPIO.OUT)		# Set pin 11 as an output pin
    GPIO.setup(20, GPIO.OUT)		# Set pin 12 as an output pin
    GPIO.setup(16, GPIO.OUT)		# Set pin 13 as an output pin


def set_LED(LED):
    led_pins = {
        'RED': 21,
        'YELLOW': 20,
        'GREEN': 16
    }
    
    # if LED == currentLED:
    #     return

    if LED == 'RED':
        GPIO.output(led_pins['RED'], GPIO.HIGH)
        GPIO.output(led_pins['YELLOW'], GPIO.LOW)
        GPIO.output(led_pins['GREEN'], GPIO.LOW)
    elif LED == 'YELLOW':
        GPIO.output(led_pins['RED'], GPIO.LOW)
        GPIO.output(led_pins['YELLOW'], GPIO.HIGH)
        GPIO.output(led_pins['GREEN'], GPIO.LOW)
    elif LED == 'GREEN':
        GPIO.output(led_pins['RED'], GPIO.LOW)
        GPIO.output(led_pins['YELLOW'], GPIO.LOW)
        GPIO.output(led_pins['GREEN'], GPIO.HIGH)
    