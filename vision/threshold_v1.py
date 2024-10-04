import time
import picamera2
import cv2
import numpy as np

cap = picamera2.Picamera2()
config = cap.create_video_configuration(main={"format":'XRGB8888',"size":(820,616)})
cap.configure(config)
cap.set_controls({"ColourGains": (1.4,1.5)})

cap.start()

def threshold(frame, thresholds):
    hFrame = frame[:,:,0] # Extract hue channel
    sFrame = frame[:,:,1] # Extract saturation channel
    vFrame = frame[:,:,2] # Extract value channel
    # Threshold each extracted channel individually with values provided by function call:
    hMask = np.where((hFrame >= thresholds[0]) & (hFrame <= thresholds[1]), 255, 0).astype(np.uint8)
    sMask = np.where((sFrame >= thresholds[2]) & (sFrame <= thresholds[3]), 255, 0).astype(np.uint8)
    vMask = np.where((vFrame >= thresholds[4]) & (vFrame <= thresholds[5]), 255, 0).astype(np.uint8)
    combinedMask = hMask & sMask & vMask # Use binary operators to combine all three masks into one
    return combinedMask

while(1):
    frame = cap.capture_array()
    frameHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 		# Convert from BGR to HSV colourspace

    blue01_2 = [79, 131, 21, 227, 20, 135] #good for 1, 2
    blue03_4 = [79, 131, 6, 246, 20, 135] #good for 3, 4
    blue05 = [79, 131, 6, 246, 20, 165] #good for 5
    blueAll = [79, 131, 6, 246, 10, 200] #works fairly well - some stuff in far distance gets lost but not bad

    orange01 = [0, 20, 161, 255, 142, 255] #good for 1
    orange02 = [0, 30, 161, 255, 142, 255] #good for 2, 3, 4, 5, 6
    orange07 = [0, 30, 161, 255, 94, 255] #long range darker
    orangeMix = [0, 20, 161, 255, 71, 255] #
    orangeAll = [0, 21, 161, 255, 71, 255]

    yellow01 = [21, 35, 215, 255, 210, 255] #good for 1
    yellow02 = [21, 35, 215, 255, 195, 255] #good for 2
    yellow03 = [21, 35, 205, 255, 195, 255] #good for 2
    yellowAll = [21, 35, 205, 255, 195, 255] 

    green01 = [39, 70, 85, 185, 25, 115] #good for 1
    green02 = [39, 70, 85, 185, 25, 145] #good for 2
    green03 = [50, 70, 65, 185, 25, 145] #good for 3
    greenAll = [40, 70, 65, 185, 25, 145]

    black01 = [9, 27, 85, 115, 45, 85] #good for row 1 - no good
    black02 = [9, 50, 25, 116, 36, 70] #good for row 3 - no good

    blackCircle01 = [11, 73, 7, 64, 21, 68]
    blackCircle03 = [0, 93, 0, 45, 30, 62]
    blackCircleAll = [0, 93, 0, 64, 21, 68]

    square01 = [9, 50, 121, 175, 59, 84]

    
    blackThreshold = [5, 60, 0, 150, 0, 110]


    combinedThreshold = threshold(frameHSV, blackThreshold) 
    cv2.imshow("Threshold", combinedThreshold)			# Display thresholded frame
    #cv2.imshow("Original", frame)


    cv2.waitKey(1)									# Exit on keypress

cap.close()
cv2.destroyAllWindows()
