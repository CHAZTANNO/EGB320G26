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

    blueThreshold = [92, 130, 95, 255, 30, 179]
    greenThreshold = [35, 90, 70, 190, 15, 120]
    originalBlueThreshold = [97, 120, 94, 255, 16, 179]

    yellowThreshold = [21, 35, 190, 255, 190, 255]
    greyThreshold = [19, 63, 6, 66, 118, 205]


    whiteMask = threshold(frameHSV, wallThreshold) 
    contours = contourImage(frameHSV, whiteMask)
    if contours:  # Make sure there are contours
        usefulContour = max(contours, key=cv2.contourArea) #only one packing station, so just take the largest
        x,y,w,h = cv2.boundingRect(usefulContour)
        width=820
        height=616
        leftx,lefty = width,0
        rightx,righty = 0,0
        contour_points = [(point[0][0], point[0][1]) for point in usefulContour]
        miny = max(y for (x,y) in contour_points)
        variation = 25
        bottom_coords = [(x, y) for x, y in contour_points if miny-variation <= y <= miny + variation]
        if bottom_coords:  # Ensure there are bottom coordinates found
            bottom_left = min(bottom_coords, key=lambda coord: coord[0])  # minimum x
            bottom_right = max(bottom_coords, key=lambda coord: coord[0])  # maximum x



        # for point in usefulContour:
        #     x,y = point[0]

        #     if y > lefty or y > righty:
        #         if x < leftx:
        #             lefty = y
        #             leftx = x
        #         if x > rightx:
        #             righty = y
        #             rightx = x

            # if lefty is None or (y > lefty) or (y == lefty and x < leftx):
            #     leftx, lefty = x, y

            # # Check for bottom right point
            # if righty is None or (y > righty) or (y == righty and x > rightx):
            #     rightx, righty = x, y
        
        cv2.circle(frame, bottom_left, 10, (255,0,255), -1)
        cv2.circle(frame, bottom_right, 10, (255,255,0), -1)



    # greyMask = threshold(frameHSV, greyThreshold)
    # kernel = np.ones((5,5),np.uint8)

    # whitedil = cv2.dilate(whiteMask,kernel,iterations = 1)
    # greydil = cv2.dilate(greyMask,kernel,iterations = 1)
    #combinedThreshold = cv2.morphologyEx(combinedThreshold, cv2.MORPH_OPEN, kernel)
    # combinedThreshold = whitedil & greydil
    cv2.imshow("Threshold", frame)			# Display thresholded frame
    cv2.imshow("Original", whiteMask)


    cv2.waitKey(1)									# Exit on keypress

cap.close()
cv2.destroyAllWindows()
