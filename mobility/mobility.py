from __future__ import print_function
import sys
import os
import time
import curses  # For capturing keyboard inputs in SSH-friendly mode
sys.path.append("../")

from DFRobot_RaspberryPi_DC_Motor import THIS_BOARD_TYPE, DFRobot_DC_Motor_IIC as Board

if THIS_BOARD_TYPE:
    board = Board(1, 0x10)  # RaspberryPi select bus 1, set address to 0x10
else:
    board = Board(7, 0x10)  # RockPi select bus 7, set address to 0x10

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
        print("board status: parameter error, last operate no effective")
    elif board.last_operate_status == board.STA_ERR_SOFT_VERSION:
        print("board status: unsupported board firmware version")

def SetTargetVelocities(x_dot, theta_dot):
    """
    Set the target velocities for the robot.
    
    :param x_dot: Linear velocity in m/s.
    :param theta_dot: Angular velocity in rad/s.
    """
    # Parameters based on motor and robot specs
    wheel_base = 0.15  # meters
    wheel_radius = 0.039 / 2  # meters
    max_motor_rpm = 240  # Loaded RPM
    max_motor_output = 100  # Motor output range is 0-100
    max_linear_speed = (max_motor_rpm / 60) * (2 * 3.14159 * wheel_radius)  # Max speed in m/s
    
    # Ensure the input velocities are within the robot's limits
    x_dot = max(min(x_dot, max_linear_speed), -max_linear_speed)
    
    # Convert linear and angular velocity into individual wheel velocities
    # Differential drive kinematics
    left_wheel_speed = (x_dot - (wheel_base / 2) * theta_dot) / wheel_radius
    right_wheel_speed = (x_dot + (wheel_base / 2) * theta_dot) / wheel_radius

    # Convert wheel speeds (rad/s) to motor RPM
    left_motor_rpm = left_wheel_speed * (60 / (2 * 3.14159))
    right_motor_rpm = right_wheel_speed * (60 / (2 * 3.14159))

    # Scale motor RPM to motor output range (0 to 100 for motor control)
    left_motor_output = min(max(int((left_motor_rpm / max_motor_rpm) * max_motor_output), 0), max_motor_output)
    right_motor_output = min(max(int((right_motor_rpm / max_motor_rpm) * max_motor_output), 0), max_motor_output)

    # Control the motors based on the calculated output values
    if x_dot >= 0:  # Forward
        board.motor_movement([board.M1], board.CCW, left_motor_output)
        board.motor_movement([board.M2], board.CW, right_motor_output)
    else:  # Backward
        board.motor_movement([board.M1], board.CW, left_motor_output)
        board.motor_movement([board.M2], board.CCW, right_motor_output)

def control_loop(stdscr):
    curses.cbreak()
    stdscr.nodelay(True)  # Don't wait for user input
    stdscr.clear()
    stdscr.addstr(0, 0, "Use WASD keys to control the tank drive. Press 'Q' to quit.")
    
    try:
        while True:
            key = stdscr.getch()  # Get the keypress

            # Initialize velocities
            x_dot = 0
            theta_dot = 0

            # WASD control for velocity
            # Move forward
            if key == ord('w'):
                x_dot = 0.4  # Set forward linear velocity (m/s)
                stdscr.addstr(1, 0, "Moving forward     ")

            # Move backward
            elif key == ord('s'):
                x_dot = -0.4  # Set backward linear velocity (m/s)
                stdscr.addstr(1, 0, "Moving backward    ")

            # Turn left
            elif key == ord('a'):
                theta_dot = 1.5  # Set left turn angular velocity (rad/s)
                stdscr.addstr(1, 0, "Turning left       ")

            # Turn right
            elif key == ord('d'):
                theta_dot = -1.5  # Set right turn angular velocity (rad/s)
                stdscr.addstr(1, 0, "Turning right      ")

            # Stop the motors when no movement key is pressed
            elif key == -1:
                stdscr.addstr(1, 0, "Motors stopped     ")

            # Exit the loop if 'q' is pressed
            elif key == ord('q'):
                stdscr.addstr(1, 0, "Exiting control    ")
                break

            # Set target velocities for the robot
            SetTargetVelocities(x_dot, theta_dot)

            time.sleep(0.1)  # Delay to reduce CPU usage
            stdscr.refresh()

    except KeyboardInterrupt:
        stdscr.addstr(1, 0, "Program interrupted by user")

    finally:
        board.motor_stop(board.ALL)
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

    curses.wrapper(control_loop)
