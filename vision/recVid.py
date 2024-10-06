from picamera2 import Picamera2

cap = Picamera2()
frameSizeX = 300  # Adjust as needed
frameSizeY = 225  # Adjust as needed

config = cap.create_video_configuration(
    main={"format": 'XRGB8888', "size": (frameSizeX, frameSizeY)},
    controls={'FrameRate': 50},
    raw={'size': (1640, 1232)}
)
cap.configure(config)
cap.set_controls({"ColourGains": (1.4, 1.5)})

cap.start_and_record_video("test_video.mp4", duration=600)
