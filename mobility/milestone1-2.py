from __future__ import print_function
import sys
import os
import time
import curses  # For capturing keyboard inputs in SSH-friendly mode
sys.path.append("../")

from DFRobot_RaspberryPi_DC_Motor import THIS_BOARD_TYPE, DFRobot_DC_Motor_IIC as Board

speed = 20  # Initial speed

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
        print("board status: parameter error, last operate no effective")
    elif board.last_operate_status == board.STA_ERR_SOFT_VERSION:
        print("board status: unsupported board firmware version")

def control_loop(stdscr):
    global speed
    curses.cbreak()
    stdscr.nodelay(True)  # Don't wait for user input
    stdscr.clear()
    stdscr.addstr(0, 0, "Use WASD keys to control the tank drive. Press 'Q' to quit. Press 'I' to enter speed input mode.")
    
    input_mode = False
    speed_str = ""  # To store speed input as a string

    try:
        while True:
            key = stdscr.getch()  # Get the keypress

            if input_mode:
                # If Enter is pressed, convert the string to an integer and update the speed
                if key == ord('\n') or key == ord('\r'):
                    if speed_str.isdigit():
                        speed = int(speed_str)
                        stdscr.addstr(2, 0, f"Speed set to {speed}      ")
                    else:
                        stdscr.addstr(2, 0, "Invalid input. Please enter a valid number.    ")
                    speed_str = ""
                    input_mode = False  # Exit input mode
                    stdscr.addstr(2, 0, "Press 'I' to enter input mode")
                    stdscr.refresh()
                # Handle backspace to remove the last character
                elif key == 127 or key == curses.KEY_BACKSPACE:
                    speed_str = speed_str[:-1]
                    stdscr.addstr(3, 0, f"Speed input: {speed_str}    ")
                # Append the digit to the speed string if it's a number
                elif chr(key).isdigit():
                    speed_str += chr(key)
                    stdscr.addstr(3, 0, f"Speed input: {speed_str}    ")
                stdscr.refresh()
                continue

            # Check if input mode is active, and do not process drive commands
            if input_mode:
                continue

            # Move forward
            if key == ord('w'):
                board.motor_movement([board.M1], board.CCW, speed)    # Motor 1 Forward
                board.motor_movement([board.M2], board.CW, speed)   # Motor 2 Forward
                stdscr.addstr(1, 0, "Moving forward     ")

            # Move backward
            elif key == ord('s'):
                board.motor_movement([board.M1], board.CW, speed)   # Motor 1 Backward
                board.motor_movement([board.M2], board.CCW, speed)    # Motor 2 Backward
                stdscr.addstr(1, 0, "Moving backward    ")

            # Turn left
            elif key == ord('a'):
                board.motor_movement([board.M1], board.CCW, speed)    # Motor 1 Forward
                board.motor_movement([board.M2], board.CCW, speed)    # Motor 2 Backward
                stdscr.addstr(1, 0, "Turning left       ")

            # Turn right
            elif key == ord('d'):
                board.motor_movement([board.M1], board.CW, speed)   # Motor 1 Backward
                board.motor_movement([board.M2], board.CW, speed)   # Motor 2 Forward
                stdscr.addstr(1, 0, "Turning right      ")

            # Stop the motors when no movement key is pressed
            elif key == -1:
                board.motor_stop(board.ALL)
                stdscr.addstr(1, 0, "Motors stopped     ")

            # Exit the loop if 'q' is pressed
            elif key == ord('q'):
                stdscr.addstr(1, 0, "Exiting control    ")
                break

            # Enter input mode when 'I' is pressed
            elif key == ord('i') or key == ord('I'):
                input_mode = True
                speed_str = ""
                stdscr.addstr(2, 0, "Enter new speed: ")
                stdscr.addstr(3, 0, "Speed input:        ")
                stdscr.refresh()

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
