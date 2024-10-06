import numpy as np
import cv2
from picamera2 import Picamera2
import stdscr

# Initialize the camera
cap = Picamera2()
frameSizeX = 300  # Adjust as needed
frameSizeY = 225  # Adjust as needed
currentFrame = np.zeros((frameSizeX, frameSizeY, 3), np.uint8)
stdscr.getch()

# Create the camera configuration
config = cap.create_video_configuration(
    main={"format": 'XRGB8888', "size": (frameSizeX, frameSizeY)},
    controls={'FrameRate': 50},
    raw={'size': (1640, 1232)}
)

cap.configure(config)
cap.set_controls({"ColourGains": (1.4, 1.5)})

# Save the video in the current working directory
video_file = "output_video.mp4"

# OpenCV video writer to save the video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(video_file, fourcc, 50, (frameSizeX, frameSizeY))

# Start the camera
cap.start()

print("Recording started. Press 'q' to stop.")

while True:
    # Capture the frame
    frame = cap.capture_array()
    out.write(frame)

    # Show the frame on the screen (optional)
    cv2.imshow("Recording", frame)

    # Exit if 'q' is pressed
    if key == ord('q'):
        break

# Stop the camera and release resources
cap.stop()
out.release()
cv2.destroyAllWindows()
print("Recording stopped and saved as 'output_video.avi'.")
