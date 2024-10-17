import RPi.GPIO as GPIO
import time

# Setup GPIO pins 
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # Scissor lift continuous servo motor on pin 18
GPIO.setup(15, GPIO.OUT)  # Gripper system servo motor on pin 19

# Initialize PWM for both motors at 50Hz
pwm_lift = GPIO.PWM(18, 50)  # 50Hz frequency for the lift
pwm_gripper = GPIO.PWM(15, 50)  # 50Hz frequency for the gripper

# Start PWM with 0% duty cycle
pwm_lift.start(0)
pwm_gripper.start(0)

# Shelf level times (in seconds) for moving to each level 
shelf_times = {
    0: 0,  # Bottom shelf (starting position)
    1: 18.0,  # Middle shelf (shelf 1)
    2: 40.0   # Top shelf (shelf 2) 
}

# Global variable to track the current shelf level
current_shelf = 0  # Starting position is level 0 (ground)

# Function to move the scissor lift to the desired height
def lift_to_shelf(shelf_level):
    global current_shelf  # Update global shelf level
    if shelf_level in shelf_times:
        target_time = shelf_times[shelf_level]
        print(f"Lifting to level {shelf_level} (approx. time: {target_time}s)")
        
        # Move the lift up 
        pwm_lift.ChangeDutyCycle(5.0)  # Duty cycle to move the lift up
        time.sleep(target_time)  # Simulate time to reach the target level
        
        # Stop the lift motor after reaching the shelf
        pwm_lift.ChangeDutyCycle(0)  # Turn off the motor
        print(f"Lift stopped at level {shelf_level}")
        
        # Update current shelf level
        current_shelf = shelf_level
    else:
        print(f"Invalid shelf level: {shelf_level}")

# Function to close the gripper and grab the item
def close_gripper():
    print("Closing gripper to grab the item...")
    pwm_gripper.ChangeDutyCycle(1.6)  
    time.sleep(1)  # Allow time for the gripper to close
    pwm_gripper.ChangeDutyCycle(0)  # Turn off the motor after closing
    print("Gripper closed.")

# Function to lower the lift from shelf 2 to shelf 1
def lower_lift_to_shelf_1():
    global current_shelf  # Update global shelf level
    print(f"Lowering from shelf 2 to shelf 1...")
    pwm_lift.ChangeDutyCycle(5.0)  # Reverse direction to lower the lift
    time.sleep(25)  # Simulate time to lower to shelf 1 
    pwm_lift.ChangeDutyCycle(0)  # Stop the motor
    print("Lift lowered to shelf 1.")
    
    # Update current shelf level
    current_shelf = 1

# Function to lower the lift all the way to the starting position
def lower_lift_to_start(): 
    global current_shelf  # Access the global current shelf level
    
    if current_shelf == 2:
        # Lower from shelf 2 to the starting position
        print(f"Lowering from shelf 2 to the starting position...")
        total_time = shelf_times[2]  # Reduce time by 2 seconds
        pwm_lift.ChangeDutyCycle(12.0)  # Reverse direction to lower the lift
        time.sleep(total_time)  # Simulate time to lower to the starting point
        pwm_lift.ChangeDutyCycle(0)  # Stop the motor
        print("Lift lowered to the starting point.")
    
    elif current_shelf == 1:
        # Lower directly from shelf 1 to the starting position
        print(f"Lowering from shelf 1 to the starting position...")
        total_time = shelf_times[1]  # Reduce time by 2 seconds
        pwm_lift.ChangeDutyCycle(12.0)  # Reverse direction to lower the lift
        time.sleep(total_time)  # Simulate time to lower to the starting point
        pwm_lift.ChangeDutyCycle(0)  # Stop the motor
        print("Lift lowered to the starting point.")

    # Reset current shelf to 0 after reaching the starting position
    current_shelf = 0

# Function to open the gripper 
def drop_item():
    print("Opening gripper to release the item...")
    pwm_gripper.ChangeDutyCycle(6.6)  
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

#Function to bring the scissor lift back to the start (down)
def bringliftdown():
    print("Bringing scissor lift back down...")

    # Move the lift down (adjust the duty cycle to rotate the servo the opposite way)
    pwm_lift.ChangeDutyCycle(12.0)  # Example duty cycle to lower the lift (counterclockwise)

    # Adjust the sleep time based on how long it takes for the lift to fully retract
    time.sleep(18.0)  # Adjust based on the time it takes to return to the starting position

    # Stop the lift motor after reaching the bottom
    pwm_lift.ChangeDutyCycle(0)  # Turn off the motor
    print("Lift is back to the start position.")

# # Testing section 
if __name__ == "__main__":
    try:
        # Ask for user input for shelf number
        shelf_number = int(input("Enter the shelf level to lift to (0 for bottom, 1 for middle, 2 for top): "))
        
        # # Lift to the chosen shelf level
        # lift_to_shelf(shelf_number)
        # time.sleep(3)  # Wait for 3 seconds before grabbing the item
        
        # # # Grab the item
        # close_gripper()
        # # time.sleep(3)  # Wait for 3 seconds before releasing the item
        
        # # Drop the item
        # drop_item()
        
        # Lower the lift back to the starting position
        # lower_lift_to_start()
        bringliftdown()

    finally:
        cleanup()  # Ensure everything is cleaned up when done