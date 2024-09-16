import cv2
import picamera2

cap = picamera2.Picamera2()
config = cap.create_video_configuration(main={"format":'XRGB8888',"size":(820,616)})
cap.configure(config)
cap.set_controls({"ColourGains":(1.4,1.5)})

cap.start()

frame = cap.capture_array()
cv2.imwrite("green01.png", frame)		# Save the frame as frame01.png

cap.close() # Release the camera object (if using picamera2)
cv2.destroyAllWindows() # Close all opencv pop-up windows





#frame = cv2.resize(frame, (320, 240))
#frame = cv2.rotate(frame, cv2.ROTATE_180)