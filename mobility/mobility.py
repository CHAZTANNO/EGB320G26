import sys
import time
import curses  # For capturing keyboard inputs in SSH-friendly mode
sys.path.append("../")

from DFRobot_RaspberryPi_DC_Motor import THIS_BOARD_TYPE, DFRobot_DC_Motor_IIC as Board

if THIS_BOARD_TYPE:
    board = Board(1, 0x10)    # RaspberryPi select bus 1, set address to 0x10
else:
    board = Board(7, 0x10)    # RockPi select bus 7, set address to 0x10

def board_detect():
    l = board.detecte()
    print("Board list conform:")
    print(l)

def print_board_status():
    if board.last_operate_status == board.STA_OK:
        print("board status: everything ok")
    elif board.last_operate_status == board.STA_ERR:
        print("board status: unexpected error")
    elif board.last_operate_status == board.STA_ERR_DEVICE_NOT_DETECTED:
        print("board status: device not detected")
    elif board.last_operate_status == board.STA_ERR_PARAMETER:
        print("board status: parameter error, last operate not effective")
    elif board.last_operate_status == board.STA_ERR_SOFT_VERSION:
        print("board status: unsupported board firmware version")

# Function to set target velocities for forward and rotational movement
def setTargetVelocities(forward_velocity, rotational_velocity):
    # Set the speeds of individual motors based on the input velocities
    max_speed = 100  # Max speed for the motor
    left_motor_speed = forward_velocity - rotational_velocity
    right_motor_speed = forward_velocity + rotational_velocity

    # Convert velocities to motor commands
    left_motor_speed = max(min(left_motor_speed, 1.0), -1.0) * max_speed
    right_motor_speed = max(min(right_motor_speed, 1.0), -1.0) * max_speed

    # Apply motor speeds to the board
    if left_motor_speed > 0:
        board.motor_movement([board.M1], board.CCW, int(abs(left_motor_speed)))
    else:
        board.motor_movement([board.M1], board.CW, int(abs(left_motor_speed)))

    if right_motor_speed > 0:
        board.motor_movement([board.M2], board.CW, int(abs(right_motor_speed)))
    else:
        board.motor_movement([board.M2], board.CCW, int(abs(right_motor_speed)))

# The control loop for keyboard input
def control_loop(stdscr):
    curses.cbreak()
    stdscr.nodelay(True)  # Don't wait for user input
    stdscr.clear()
    stdscr.addstr(0, 0, "Use WASD keys to control the robot. Press 'Q' to quit.")
    
    try:
        while True:
            key = stdscr.getch()  # Get the keypress

            # WASD control mode
            if key == ord('w'):
                setTargetVelocities(0.1, 0.0)  # Move forward with velocity 0.1 m/s
                stdscr.addstr(1, 0, "Moving forward     ")

            elif key == ord('s'):
                setTargetVelocities(-0.1, 0.0)  # Move backward with velocity -0.1 m/s
                stdscr.addstr(1, 0, "Moving backward    ")

            elif key == ord('a'):
                setTargetVelocities(0.0, 0.5)  # Turn left with rotational velocity 0.5 rad/s
                stdscr.addstr(1, 0, "Turning left       ")

            elif key == ord('d'):
                setTargetVelocities(0.0, -0.5)  # Turn right with rotational velocity -0.5 rad/s
                stdscr.addstr(1, 0, "Turning right      ")

            elif key == -1:  # No key pressed, stop
                setTargetVelocities(0.0, 0.0)
                stdscr.addstr(1, 0, "Motors stopped     ")

            elif key == ord('q'):  # Exit the loop
                stdscr.addstr(1, 0, "Exiting control    ")
                break

            stdscr.refresh()
            time.sleep(0.1)  # Delay to reduce CPU usage

    except KeyboardInterrupt:
        stdscr.addstr(1, 0, "Program interrupted by user")

    finally:
        setTargetVelocities(0.0, 0.0)  # Stop motors before exiting
        stdscr.addstr(1, 0, "Motors stopped")

if __name__ == "__main__":
    board_detect()

    while board.begin() != board.STA_OK:
        print_board_status()
        print("board begin failed")
        time.sleep(2)
    print("board begin success")

    board.set_encoder_enable(board.ALL)
    board.set_encoder_reduction_ratio(board.ALL, 43)
    board.set_moter_pwm_frequency(1000)

    # Start control loop with keyboard input
    curses.wrapper(control_loop)
