from __future__ import print_function
import sys
import os
import time
import argparse  # For handling command-line arguments
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
    max_motor_output = 60  # Motor output range is 0-100
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

def control_loop():
    """
    Interactive control loop using keyboard (WASD).
    """
    print("Use WASD keys to control the tank drive. Press 'Q' to quit.")
    
    try:
        while True:
            key = input("Enter control (W/A/S/D or Q to quit): ").lower()

            # Initialize velocities
            x_dot = 0
            theta_dot = 0

            # WASD control for velocity
            if key == 'w':
                SetTargetVelocities(0.4, 0)
                print("Moving forward")

            elif key == 's':
                SetTargetVelocities(-0.4, 0)
                print("Moving backward")

            elif key == 'a':
                SetTargetVelocities(0, -0.5)
                print("Turning left")

            elif key == 'd':
                SetTargetVelocities(0, 0.5)
                print("Turning right")

            elif key == 'q':
                print("Exiting control")
                break

            else:
                print("Invalid input, stopping motors")
                SetTargetVelocities(0, 0)

            time.sleep(0.1)  # Delay to reduce CPU usage

    except KeyboardInterrupt:
        print("Program interrupted by user")

    finally:
        board.motor_stop(board.ALL)
        print("Motors stopped")

if __name__ == "__main__":
    board_detect()

    while board.begin() != board.STA_OK:
        print_board_status()
        print("board begin failed")
        time.sleep(2)
    print("board begin success")

    board.set_encoder_enable(board.ALL)
    board.set_encoder_reduction_ratio(board.ALL, 100)
    board.set_moter_pwm_frequency(1000)

    # Argument parsing for command-line mode
    parser = argparse.ArgumentParser(description="Set robot target velocities")
    parser.add_argument("--x_dot", type=float, help="Linear velocity (m/s)", default=None)
    parser.add_argument("--theta_dot", type=float, help="Angular velocity (rad/s)", default=None)
    parser.add_argument("--interactive", action="store_true", help="Start in interactive mode")

    args = parser.parse_args()

    if args.x_dot is not None or args.theta_dot is not None:
        # Call SetTargetVelocities with command-line arguments
        SetTargetVelocities(args.x_dot, args.theta_dot)
        print(f"Set target velocities: x_dot={args.x_dot}, theta_dot={args.theta_dot}")
    elif args.interactive:
        # Start interactive mode
        control_loop()
    else:
        print("Please provide both --x_dot and --theta_dot for command-line mode or use --interactive for manual control.")