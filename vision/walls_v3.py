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
    # hMask = np.where((hFrame >= thresholds[0]) & (hFrame <= thresholds[1]), 255, 0).astype(np.uint8)
    # sMask = np.where((sFrame >= thresholds[2]) & (sFrame <= thresholds[3]), 255, 0).astype(np.uint8)
    # vMask = np.where((vFrame >= thresholds[4]) & (vFrame <= thresholds[5]), 255, 0).astype(np.uint8)

    __, hMaskLow = cv2.threshold(hFrame, thresholds[0], 255, cv2.THRESH_BINARY)
    __, hMaskUp = cv2.threshold(hFrame, thresholds[1], 255, cv2.THRESH_BINARY_INV)
    hMask = cv2.bitwise_and(hMaskLow, hMaskUp)
    __, sMaskLow = cv2.threshold(sFrame, thresholds[2], 255, cv2.THRESH_BINARY)
    __, sMaskUp = cv2.threshold(sFrame, thresholds[3], 255, cv2.THRESH_BINARY_INV)
    sMask = cv2.bitwise_and(sMaskLow, sMaskUp)
    __, vMaskLow = cv2.threshold(vFrame, thresholds[4], 255, cv2.THRESH_BINARY)
    __, vMaskUp = cv2.threshold(vFrame, thresholds[5], 255, cv2.THRESH_BINARY_INV)
    vMask = cv2.bitwise_and(vMaskLow, vMaskUp)

    combinedMask = hMask & sMask & vMask # Use binary operators to combine all three masks into one
    return combinedMask

def contourImage(frame, mask):
    kernel = np.ones((8,8),np.uint8)
    maskClose = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    maskCloseOpen = cv2.morphologyEx(maskClose, cv2.MORPH_OPEN, kernel)

    contours, heirarchy = cv2.findContours(maskCloseOpen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filteredContours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 800:
            filteredContours.append(contour)
    return filteredContours

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
    square02 = [16, 38, 50, 133, 40, 129]
    wallThreshold = [2, 42, 0, 70, 150, 232]
    wallThreshold2 = [2, 63, 6, 70, 118, 221]
    wallThreshold3 = [2, 75, 0, 85, 70, 240]

    blueThreshold = [92, 130, 95, 255, 30, 179]
    greenThreshold = [35, 90, 70, 190, 15, 120]
    originalBlueThreshold = [97, 120, 94, 255, 16, 179]

    yellowThreshold = [21, 35, 190, 255, 190, 255]
    greyThreshold = [19, 63, 6, 66, 118, 205]



    height, width = frame.shape[:2]

    # Create a mask with the same size as the image (bottom half set to 255, top half set to 0)
    maskBottomOnly = np.zeros((height, width), dtype=np.uint8)
    maskBottomOnly[height//2:, :] = 255  # Keep only the bottom half
    whiteMask = threshold(frameHSV, wallThreshold3) 
    kernel = np.ones((5,5),np.uint8)
    largeKernel = np.ones((10,10), np.uint8)
    # whiteMask = cv2.morphologyEx(whiteMask, cv2.MORPH_CLOSE, kernel)
    whiteMask = cv2.erode(whiteMask, largeKernel, iterations=1)
    mask = maskBottomOnly & whiteMask
    
    expandedMask = cv2.erode(mask, largeKernel, iterations=1)
    maskedImage = cv2.bitwise_and(frame, frame, mask= mask)

    #gray = cv2.cvtColor(maskedImage, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(maskedImage, (15, 15), 0)
    
    # Apply morphological operations to reduce texture noise
    # kernel = np.ones((5,5), np.uint8)
    # morph = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

    maskedImage = blurred


    edges = cv2.Canny(maskedImage, 10, 40)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=20, maxLineGap=110)
    # ^outputs (x1, y1, x2, y2) which are start and end coords of (straight) lines

    max_length = 0
    min_height = height
    longest_line = None
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            xAvg = int((x1+x2)/2)
            yAvg = int((y1+y2)/2)
            # print(expandedMask[yAvg, xAvg])
            # cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 1)
            if (expandedMask[yAvg, xAvg] != 0) and ((expandedMask[y1,x1] == 0) or (x1 < 40) or (x1 > width-40)) and ((expandedMask[y2,x2] == 0) or (x2 < 40) or (x2 > width-40)):
                # cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 1)  # Red color for longest line

                # length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)  # Calculate Euclidean distance

                # Check if this line is the highest 
                if (y1 > height/2+5) & (yAvg < min_height): 
                    min_height = yAvg
                    longest_line = (x1, y1, x2, y2)

        # Draw the longest line
        if longest_line is not None:
            x1, y1, x2, y2 = longest_line
            # cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red color for longest line
            cv2.circle(frame, (x1,y1), 10, (255,0,255), -1)
            cv2.circle(frame, (x2,y2), 10, (255,255,0), -1)


    cv2.imshow("Threshold", frame)			# Display thresholded frame
    # cv2.imshow("filtered", maskedImage)
    #cv2.imshow("Original", mask)
    # cv2.imshow("hi", maskedImage)


    cv2.waitKey(1)									# Exit on keypress

cap.close()
cv2.destroyAllWindows()
