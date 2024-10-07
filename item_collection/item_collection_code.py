import RPi.GPIO as GPIO
import time

# Setup GPIO pins for both the scissor lift and the gripper motor
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # Scissor lift continuous servo motor on pin 18
GPIO.setup(19, GPIO.OUT)  # Gripper system servo motor on pin 19

# Initialize PWM for both motors at 50Hz
pwm_lift = GPIO.PWM(18, 50)  # 50Hz frequency for the lift
pwm_gripper = GPIO.PWM(19, 50)  # 50Hz frequency for the gripper

# Start PWM with 0% duty cycle to avoid immediate movement
pwm_lift.start(0)
pwm_gripper.start(0)

# Shelf level times (in seconds) for moving to each level (adjust based on testing)
shelf_times = {
    0: 1.5,  # Bottom shelf
    1: 20.0,  # Middle shelf (you mentioned this is longer)
    2: 4.5   # Top shelf
}

# Function to move the scissor lift to the desired height and grab the item
def collect_item(shelf_level):
    if shelf_level in shelf_times:
        target_time = shelf_times[shelf_level]
        print(f"Lifting to level {shelf_level} (approx. time: {target_time}s)")
        
        # Move the lift up (adjust the duty cycle as needed for your servo)
        pwm_lift.ChangeDutyCycle(12.0)  # Example duty cycle for moving the lift
        time.sleep(target_time)  # Simulate time to reach the target level
        
        # Stop the lift motor after reaching the shelf
        pwm_lift.ChangeDutyCycle(0)  # Turn off the motor
        print(f"Lift stopped at level {shelf_level}")
        
        # Close the gripper to grab the item
        print("Closing gripper to grab the item...")
        pwm_gripper.ChangeDutyCycle(9.0)  # Adjust this value to close the gripper
        time.sleep(1)  # Allow time for the gripper to close
        pwm_gripper.ChangeDutyCycle(0)  # Turn off the motor after closing
        print("Item grabbed.")
    else:
        print(f"Invalid shelf level: {shelf_level}")

# Function to open the gripper and release the item
def drop_item():
    print("Opening gripper to release the item...")
    
    # **Adjust Duty Cycle**: Try a different value than 5.0 for opening
    pwm_gripper.ChangeDutyCycle(12.5)  # Example duty cycle to open the gripper (adjust this value)
    
    time.sleep(1)  # Allow time for the gripper to open fully
    pwm_gripper.ChangeDutyCycle(0)  # Turn off the motor after opening
    print("Item released.")

# Cleanup function to stop servos
def cleanup():
    """
    Stops all servos and releases GPIO pins.
    Call this when the script is done running.
    """
    pwm_lift.stop()
    pwm_gripper.stop()
    GPIO.cleanup()

def bringliftdown():
    print("Bringing scissor lift back down...")

    # Move the lift down (adjust the duty cycle to rotate the servo the opposite way)
    pwm_lift.ChangeDutyCycle(5.0)  # Example duty cycle to lower the lift (counterclockwise)

    # Adjust the sleep time based on how long it takes for the lift to fully retract
    time.sleep(15)  # Adjust based on the time it takes to return to the starting position

    # Stop the lift motor after reaching the bottom
    pwm_lift.ChangeDutyCycle(0)  # Turn off the motor
    print("Lift is back to the start position.")

# Testing
if __name__ == "__main__":
    try:
        #collect_item(1)
        bringliftdown()
        
    finally:
        cleanup()  # Ensure everything is cleaned up when done