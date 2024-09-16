import time
import picamera2
import cv2
import numpy as np
import RPi.GPIO as GPIO

# GPIO mode setup
GPIO.setmode(GPIO.BCM)
# Define GPIO pins
TRIG = 23
ECHO = 24
# Set up GPIO pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

cap = picamera2.Picamera2()
frameSizeX = 820
frameSizeY = 616
config = cap.create_video_configuration(main={"format":'XRGB8888',"size":(frameSizeX,frameSizeY)})
cap.configure(config)
cap.set_controls({"ColourGains": (1.4,1.5)})
cap.start()

focalLengthMM = 3.04
sensorWidthMM = 3.68
sensorHeightMM = 2.76
focalWidthPixels = focalLengthMM*frameSizeX / sensorWidthMM #focal length in pixels with specific frame size (820x616)
focalHeightPixels = focalLengthMM*frameSizeY / sensorHeightMM
#https://www.raspberrypi.com/documentation/accessories/camera.html

fullHFOV = 62.2 #degrees
fullHResolution = 3280 #px
degreesPerPixel = fullHFOV / fullHResolution

blueThreshold = [79, 131, 6, 246, 20, 185]
orangeThreshold = [0, 21, 161, 255, 71, 255]
yellowThreshold = [21, 35, 205, 255, 195, 255]
greenThreshold = [50, 96, 73, 168, 67, 109]
black01 = [9, 27, 85, 115, 45, 85] #good for row 1
black02 = [9, 50, 25, 116, 36, 70] #good for row 3
black04 = [11, 56, 0, 119, 0, 54]
blackThreshold = [9, 56, 0, 119, 0, 85]
square01 = [9, 50, 121, 175, 59, 84]
homeBlackCircles = [0, 42, 74, 255, 19, 92]
homeOrange = [6, 15, 248, 255, 186, 236]
homeGreen = [58, 88, 65, 255, 20, 90]



def threshold(frame, thresholds, trueValue):
    hFrame = frame[:,:,0] # Extract hue channel
    sFrame = frame[:,:,1] # Extract saturation channel
    vFrame = frame[:,:,2] # Extract value channel

    # Threshold each extracted channel individually with values provided by function call:
    hMask = np.where((hFrame >= thresholds[0]) & (hFrame <= thresholds[1]), trueValue, 0).astype(np.uint8)
    sMask = np.where((sFrame >= thresholds[2]) & (sFrame <= thresholds[3]), trueValue, 0).astype(np.uint8)
    vMask = np.where((vFrame >= thresholds[4]) & (vFrame <= thresholds[5]), trueValue, 0).astype(np.uint8)

    combinedMask = hMask & sMask & vMask # Use binary operators to combine all three masks into one
    return combinedMask

def contourImage(frame, mask):
    kernel = np.ones((8,8),np.uint8)
    maskClose = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    maskCloseOpen = cv2.morphologyEx(maskClose, cv2.MORPH_OPEN, kernel)

    contours, heirarchy = cv2.findContours(maskCloseOpen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours


def items(frameHSV, thresholdVals):
    mask = threshold(frameHSV, thresholdVals, 255) 
    contours = contourImage(frameCopy, mask)
    cv2.drawContours(frameCopy, contours, -1, (0,255,0), 1)

    bottles = []
    balls = []
    cubes = []
    cups = []
    rects = []
    bowls = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)

        itemType, itemHeightMM = findItemType(contour, w, h)

        range = findRangeHeight(itemHeightMM, h)
        bearing = findBearing(x, w)

        if x < 2:
            xText = 2
        else:
            xText = x
        if y < 35:
            yText = 25
        else:
            yText = y - 10

        cv2.putText(frameCopy, f"{itemType}, {range:.0f}mm, {bearing:.1f}*", (xText,yText), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1)
        
        if itemType == "bottle":
            bottles.append((range, bearing))
        elif itemType == "ball":
            balls.append((range, bearing))
        elif itemType == "cube":
            cubes.append((range, bearing))
        elif itemType == "cup":
            cups.append((range, bearing))
        elif itemType == "rect":
            rects.append((range, bearing))
        elif itemType == "bowl":
            bowls.append((range, bearing))
    if bottles == []:
        bottles = None
    if balls == []:
        balls = None
    if cubes == []:
        cubes = None
    if cups == []:
        cups = None
    if rects == []:
        rects = None
    if bowls == []:
        bowls = None
    
    outputRB = [bottles, balls, cubes, cups, rects, bowls]
    return outputRB

def rowMarker(frameHSV, thresholdVals, diameter):
    mask = threshold(frameHSV, thresholdVals, 255) 
    contours = contourImage(frameCopy, mask)

    circleCount = 0
    ranges = []
    bearings = []
    xs = []
    ys = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)

        range = findRangeWidth(diameter, w)
        bearing = findBearing(x, w)
        if isCircle(contour) == True:
            circleCount += 1
            cv2.drawContours(frameCopy, [contour], 0, (0, 0, 255), 2)
            ranges.append(range)
            bearings.append(bearing)
            xs.append(x)
            ys.append(y)
    if (0 <circleCount) & (circleCount <=3):
        meanRange = np.mean(ranges)
        meanBearing = np.mean(bearings)
        minX = np.min(xs)
        minY = np.min(ys)
    else:
        return None #Not sure if good idea - revise later

    if minX < 2:
        xText = 2
    else:
        xText = minX
    if minY < 35:
        yText = 25
    else:
        yText = minY - 10
    cv2.putText(frameCopy, f"Row {circleCount}, {meanRange:.0f}mm, {meanBearing:.1f}*", (xText,yText), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
    
    outputRB = [meanRange, meanBearing]
    if circleCount == 1:
        return (outputRB, None, None)
    elif circleCount == 2:
        return (None, outputRB, None)
    elif circleCount == 3:
        return (None, None, outputRB)
    outputRB = [meanRange, meanBearing]
    return outputRB

def obstacle(frame, thresholdVals):
    mask = threshold(frame, thresholdVals, 255)
    contours = contourImage(frameCopy, mask)
    cv2.drawContours(frameCopy, contours, -1, (255,0,255), 1)

    outputRB = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        
        if h >= (0.95*frameSizeY): #Obstacle is too close to use height, use width instead
            range = findRangeWidth(60, w)
        else:
            range = findRangeHeight(150, h)

        bearing = findBearing(x, w)

        outputRB.append((range, bearing))

        if x < 2:
            xText = 2
        else:
            xText = x
        if y < 35:
            yText = 25
        else:
            yText = y - 10
        cv2.putText(frameCopy, f"Obstacle, {range:.0f}mm, {bearing:.1f}*", (xText,yText), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 1)
    
    return outputRB

def shelves(frame, thresholdVals):
    mask = threshold(frame, thresholdVals, 255)
    contours = contourImage(frameCopy, mask)
    cv2.drawContours(frameCopy, contours, -1, (0,200,90), 1)

    outputRB = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        
        if (h >= (0.95*frameSizeY)) | (y<20) | (y+h > 596): #Obstacle is too close to use height, use ultrasonic instead
            range = 1000 #ultrasonicDistance()
        else:
            range = findRangeHeight(312, h)

        bearing = findBearing(x, w)

        outputRB.append((range, bearing))

        if x < 2:
            xText = 2
        else:
            xText = x
        if y < 35:
            yText = 25
        else:
            yText = y - 10
        cv2.putText(frameCopy, f"Shelf, {range:.0f}mm, {bearing:.1f}*", (xText,yText), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 1)
    
    outputRB = sortBearingLtoR(outputRB)
    return outputRB

def sortBearingLtoR(RB):
    RB.sort(key = lambda x: x[1])
    return RB

def ultrasonicDistance():
    # Send a 10µs pulse to trigger the sensor
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.08)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
    
    # Wait for the echo pin to go HIGH
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()
    
    # Wait for the echo pin to go LOW again
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()
    
    # Calculate pulse duration and distance
    if 'pulse_end' in locals() and 'pulse_start' in locals():
        pulse_duration = pulse_end - pulse_start
        distance_cm = pulse_duration * 17150
        distance_cm = round(distance_cm, 2)
    else:
        distance_cm = None
    
    return distance_cm

def findRangeWidth(objectWidthMM, widthPx):
    range = (focalWidthPixels*objectWidthMM) / widthPx
    return range

def findRangeHeight(objectHeightMM, heightPx):
    range = (focalHeightPixels*objectHeightMM) / heightPx
    return range

def findBearing(x, widthPx):
    objectCentreX = x + (widthPx/2)
    frameCentreX = frameSizeX/2
    bearing = np.degrees(np.arctan2(objectCentreX - frameCentreX, focalWidthPixels))
    return bearing

def isCircle(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if (perimeter > 0) & (area > 100):
        circularity = (4 * np.pi * area) / (perimeter**2)
        if 0.8 < circularity < 1.2:  # Check for circle
            #is a circle
            return True
        else:
            return False
        
def findItemType(contour, w, h):
    # Aspect Ratios: bottle=0.25, ball=1, cube=1, cup=1.24, rect=1.44, bowl=2.15
    # Heights: bottle=72, ball=47, cube=38, cup=42, rect=45, bowl=26
    aspectRatio = w / h
    if aspectRatio < 0.5:
        return "bottle", 72
    elif (0.8 < aspectRatio) & (aspectRatio < 1.1):
        #ball or cube
        if isCircle(contour) == True:
            return "ball", 47
        else:
            return "cube", 38
    elif (1.1 < aspectRatio) & (aspectRatio < 1.34):
        return "cup", 42
    elif (1.34 < aspectRatio) & (aspectRatio < 1.8):
        return "rect", 45
    elif (aspectRatio > 1.8):
        return "bowl", 26
    else:
        return "unknown", 45 #45mm is average height
    


while(1):
    frame = cap.capture_array()
    frameCopy = frame.copy()
    frameHSV = cv2.cvtColor(frameCopy, cv2.COLOR_BGR2HSV) 		# Convert from BGR to HSV colourspace

    itemsRB = items(frameHSV, orangeThreshold)
    rowMarkerRB = rowMarker(frameHSV, blackThreshold, 70) #replace with right size or modify function
    obstalcesRB = obstacle(frameHSV, greenThreshold)
    shelvesRB = shelves(frameHSV, blueThreshold)

    cv2.imshow("Threshold", frameCopy)			# Display thresholded frame


    cv2.waitKey(1)									# Exit on keypress

cap.close()
cv2.destroyAllWindows()