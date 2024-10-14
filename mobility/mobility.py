from __future__ import print_function
from math import pi
import time
import argparse  # For handling command-line arguments
from .DFRobot_RaspberryPi_DC_Motor import THIS_BOARD_TYPE, DFRobot_DC_Motor_IIC as Board

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
    if x_dot is None or theta_dot is None:
        print("Error: Invalid velocity inputs")
        return

    # Parameters based on motor and robot specs
    wheel_base = 0.15  # meters
    wheel_diameter = 0.039  # meters
    max_motor_rpm = 280  # Loaded RPM
    max_motor_output = 40  # Motor output range is 0-100
    
    # left_wheel_speed = x_dot - (theta_dot * wheel_base) / 2
    # right_wheel_speed = x_dot + (theta_dot * wheel_base) / 2
    
    # if (x_dot == 0 and theta_dot == 0):
    #     left_direction = board.CCW
    #     right_direction = board.CW
    #     left_motor_output = 0
    #     right_motor_output = 0
    #     board.motor_movement([board.M1], left_direction, left_motor_output)
    #     board.motor_movement([board.M2], right_direction, right_motor_output)
    #     print("M1 - Direction: ", str(left_direction), "Speed: ", str(left_motor_output))
    #     print("M2 - Direction: ", str(right_direction), "Speed: ", str(right_motor_output))
    #     return

    # if (x_dot == 0):
    #     left_wheel_speed = -theta_dot
    #     right_wheel_speed = theta_dot
    # else:
    left_wheel_speed = x_dot - (theta_dot * wheel_base) / 2
    right_wheel_speed = x_dot + (theta_dot * wheel_base) / 2
    
    print(left_wheel_speed)
    print(right_wheel_speed)
 
    # Convert wheel speeds (rad/s) to motor RPM
    # RPM = (V / (π × D)) × 60
    left_motor_rpm = (left_wheel_speed / (pi * wheel_diameter)) * 60
    right_motor_rpm = (right_wheel_speed / (pi * wheel_diameter)) * 60
    print(left_motor_rpm)
    print(right_motor_rpm)

    # Determine the direction for each motor based on wheel speed
    # left_direction = "CCW" if left_motor_rpm >= 0 else "CW"
    # right_direction = "CW" if right_motor_rpm >= 0 else "CCW"
    left_direction = board.CCW if left_motor_rpm >= 0 else board.CW
    right_direction = board.CW if right_motor_rpm >= 0 else board.CCW

    # Scale motor RPM to motor output range (0 to 100 for motor control)
    left_motor_output = min(max(abs(left_motor_rpm / max_motor_rpm * max_motor_output), 0), max_motor_output)
    right_motor_output = min(max(abs(right_motor_rpm / max_motor_rpm * max_motor_output), 0), max_motor_output)

    # Control the motors based on the calculated output values and directions
    board.motor_movement([board.M1], left_direction, left_motor_output)
    board.motor_movement([board.M2], right_direction, right_motor_output)
    print("M1 - Direction: ", str(left_direction), "Speed: ", str(left_motor_output))
    print("M2 - Direction: ", str(right_direction), "Speed: ", str(right_motor_output))

def setupMob():
    board_detect()

    while board.begin() != board.STA_OK:
        print_board_status()
        print("board begin failed")
        time.sleep(2)
    print("board begin success")

    board.set_encoder_enable(board.ALL)
    board.set_encoder_reduction_ratio(board.ALL, 100)
    board.set_moter_pwm_frequency(1000)

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

    x_dot = 0
    theta_dot = 0

    while True:
        x_dot = float(input("x_dot"))
        theta_dot = float(input("theta_dot"))

        SetTargetVelocities(x_dot, theta_dot)
