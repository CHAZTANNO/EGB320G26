import time
import picamera2
import cv2
import numpy as np
from threading import Thread
from pprint import *

class visionSystem:
    def __init__(self):

        self.prevTime = 0
        self.currentTime = 0

        self.cap = picamera2.Picamera2()
        self.frameSizeX = 300#820
        self.frameSizeY = 225#616
        self.minArea = int(self.frameSizeX*self.frameSizeY / 400)
        self.currentFrame = np.zeros((self.frameSizeX, self.frameSizeY, 3), np.uint8)
        # frameCount = 0
        config = self.cap.create_video_configuration(main={"format":'XRGB8888',"size":(self.frameSizeX,self.frameSizeY)},
                                                controls={'FrameRate': 50},
                                                raw={'size': (1640, 1232)})

        pprint(self.cap.sensor_modes)                                        
        self.cap.configure(config)
        self.cap.set_controls({"ColourGains": (1.4,1.5)})
        #self.cap.start()

        focalLengthMM = 3.04
        sensorWidthMM = 3.68
        sensorHeightMM = 2.76
        self.focalWidthPixels = focalLengthMM*self.frameSizeX / sensorWidthMM #focal length in pixels with specific resolution (not frame size)
        self.focalHeightPixels = focalLengthMM*self.frameSizeY / sensorHeightMM
        #https://www.raspberrypi.com/documentation/accessories/camera.html

        # fullHFOV = 62.2 #degrees
        # fullHResolution = 3280 #px
        # degreesPerPixel = fullHFOV / fullHResolution

        self.blueThreshold = [97, 120, 94, 255, 16, 179]
        orangeThreshold = [0, 21, 161, 255, 71, 255]
        self.yellowThreshold = [21, 35, 190, 255, 190, 255]
        self.greenThreshold = [38, 90, 60, 210, 15, 135]
        black01 = [9, 27, 85, 115, 45, 85] #good for row 1
        black02 = [9, 50, 25, 116, 36, 70] #good for row 3
        black04 = [11, 56, 0, 119, 0, 54]
        self.blackThreshold = [5, 60, 0, 160, 0, 120]
        square01 = [9, 50, 121, 175, 59, 84]
        homeBlackCircles = [0, 42, 74, 255, 19, 92]
        homeOrange = [6, 15, 248, 255, 186, 236]
        homeGreen = [58, 88, 65, 255, 20, 90]
        self.squareThreshold = [16, 38, 50, 140, 40, 140]


    def threshold(self, frame, thresholds, trueValue):
        hFrame = frame[:,:,0] # Extract hue channel
        sFrame = frame[:,:,1] # Extract saturation channel
        vFrame = frame[:,:,2] # Extract value channel

        # Threshold each extracted channel individually with values provided by function call:
        # hMask = np.where((hFrame >= thresholds[0]) & (hFrame <= thresholds[1]), trueValue, 0).astype(np.uint8)
        # sMask = np.where((sFrame >= thresholds[2]) & (sFrame <= thresholds[3]), trueValue, 0).astype(np.uint8)
        # vMask = np.where((vFrame >= thresholds[4]) & (vFrame <= thresholds[5]), trueValue, 0).astype(np.uint8)
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

    def contourImage(self, mask):
        kernel = np.ones((8,8),np.uint8)
        maskClose = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        maskCloseOpen = cv2.morphologyEx(maskClose, cv2.MORPH_OPEN, kernel)

        contours, heirarchy = cv2.findContours(maskCloseOpen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filteredContours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.minArea:
                filteredContours.append(contour)
        return filteredContours

    def findRangeWidth(self, objectWidthMM, widthPx):
        range = (self.focalWidthPixels*objectWidthMM) / widthPx
        return range

    def findRangeHeight(self, objectHeightMM, heightPx):
        range = (self.focalHeightPixels*objectHeightMM) / heightPx
        return range

    def findBearing(self, x, widthPx):
        objectCentreX = x + (widthPx/2)
        frameCentreX = self.frameSizeX/2
        bearing = np.degrees(np.arctan2(objectCentreX - frameCentreX, self.focalWidthPixels))
        return bearing

    def isCircle(self, contour):
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = (4 * np.pi * area) / (perimeter**2)
        if (0.8 < circularity < 1.2):# Check for circle
            #is a circle
            return True
        else:
            return False
        
    def isSquare(self, contour):
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Check if the approximated contour has 4 vertices and is close to square-shaped
        if len(approx) == 4:
            x,y,w,h = cv2.boundingRect(approx)
            aspectRatio = w / float(h)

            if 0.60 <= aspectRatio <= 1.40:  # Check if aspect ratio is close to 1 (square)
                #print("Contour is a square.")
                return True, x,y,w,h
            else:
                #print("Contour is not a square (aspect ratio is off).")
                return False, x,y,w,h
        else:
            #print("Contour is not a square (does not have 4 vertices).")
            return False, 0, 0, 0, 0


    def rowMarker(self, writeFrame, frameHSV, thresholdVals):
        outputRB = [None, None, None]
        mask = self.threshold(frameHSV, thresholdVals, 255) 
        if cv2.countNonZero(mask) > self.minArea:
            contours = self.contourImage(mask)

            circleCount = 0
            ranges = []
            bearings = []
            xs = []
            ys = []
            for contour in contours:
                if self.isCircle(contour) == True:
                    x,y,w,h = cv2.boundingRect(contour)
                    range = self.findRangeWidth(70, w)
                    bearing = self.findBearing(x, w)
                    circleCount += 1
                    cv2.drawContours(writeFrame, [contour], 0, (0, 0, 255), 2)
                    ranges.append(range)
                    bearings.append(bearing)
                    xs.append(x)
                    ys.append(y)
            if (0 < circleCount <= 3):
                meanRange = np.mean(ranges)
                meanBearing = np.mean(bearings)
                minX = np.min(xs)
                minY = np.min(ys)
                cv2.putText(writeFrame, f"R{circleCount}, {meanRange:.0f}mm, {meanBearing:.1f}*", (minX,minY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 1)
                RB = [meanRange, meanBearing]
                outputRB[circleCount-1] = RB
        
        return writeFrame, outputRB
            

            # if minX < 2:
            #     xText = 2
            # else:
            #     xText = minX
            # if minY < 35:
            #     yText = 25
            # else:
            #     yText = minY - 10
            # xText,yText
                
            # outputRB = [meanRange, meanBearing]
            # if circleCount == 1:
            #     return (outputRB, None, None)
            # elif circleCount == 2:
            #     return (None, outputRB, None)
            # elif circleCount == 3:
            #     return (None, None, outputRB)
          
    def obstacle(self, writeFrame, frame, thresholdVals):
        mask = self.threshold(frame, thresholdVals, 255)
        if cv2.countNonZero(mask) > self.minArea:
            kernel = np.ones((8,8),np.uint8)
            maskOpen = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, heirarchy = cv2.findContours(maskOpen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
            # contours = self.contourImage(frame, mask)

            outputRB = []
            for contour in contours:
                x,y,w,h = cv2.boundingRect(contour)
                
                if h >= (0.95*self.frameSizeY): #Obstacle is too close to use height, use width instead
                    range = self.findRangeWidth(60, w)
                else:
                    range = self.findRangeHeight(150, h)

                bearing = self.findBearing(x, w)

                outputRB.append((range, bearing))

                # if x < 2:
                #     xText = 2
                # else:
                #     xText = x
                # if y < 35:
                #     yText = 25
                # else:
                #     yText = y - 10
                cv2.putText(writeFrame, f"Obstacle, {range:.0f}mm, {bearing:.1f}*", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 1)
            
            cv2.drawContours(writeFrame, contours, -1, (255,0,255), 2)
        else:
            outputRB = None
        return writeFrame, outputRB

    def shelves(self, writeFrame, frame, thresholdVals):
        mask = self.threshold(frame, thresholdVals, 255)
        if cv2.countNonZero(mask) > self.minArea:
            contours = self.contourImage(mask)

            outputRB = []
            for contour in contours:
                x,y,w,h = cv2.boundingRect(contour)
                
                # if (h >= (0.95*frameSizeY)) | (y<20) | (y+h > 596): #Obstacle is too close to use height, use ultrasonic instead
                #     range = self.findRangeHeight(312, h) # future: ultrasonicDistance()
                # else:
                #     range = self.findRangeHeight(312, h)
                range = self.findRangeHeight(312, h)
                bearing = self.findBearing(x, w)
                outputRB.append((range, bearing))

                # if x < 2:
                #     xText = 2
                # else:
                #     xText = x
                # if y < 35:
                #     yText = 25
                # else:
                #     yText = y - 10
                cv2.putText(writeFrame, f"Shelf, {range:.0f}mm, {bearing:.1f}*", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 1)
            
            cv2.drawContours(writeFrame, contours, -1, (0,255,0), 3)
            outputRB = outputRB.sort(key = lambda x: x[1]) #self.sortBearingLtoR(outputRB) #sort by bearing, left to right
        else:
            outputRB = None
        return writeFrame, outputRB

    def packingBay(self, writeFrame, frame, threshValsSquare, threshValsYel):
        outputRB = [None, None]
        usefulContour = []
        usefulX, usefulY = 0, 0
        squareCount = 0
        # if can see square, use that, if not use yellow
        maskSquare = self.threshold(frame, threshValsSquare, 255)
        if cv2.countNonZero(maskSquare) > self.minArea:
            contoursSquare = self.contourImage(maskSquare)
            

            for contour in contoursSquare:
                squareStatus, x,y,w,h = self.isSquare(contour)
                if squareStatus == True:
                    range = self.findRangeHeight(70, h)
                    bearing = self.findBearing(x, w)
                    squareCount += 1
                    usefulContour = contour
                    usefulX = x
                    usefulY = y
                    #print("I found a square! R: " + str(range), "B: " + str(bearing))

        if squareCount != 1: #either no squares, or multiple squares - use yellow instead
            usefulContour = []
            #print("No squares, trying to find yellow")
            #Yellow:
            maskYel = self.threshold(frame, threshValsYel, 255)
            if cv2.countNonZero(maskYel) > self.minArea:
                contoursYel = self.contourImage(maskYel)

                if contoursYel:  # Make sure there are contours
                    usefulContour = max(contoursYel, key=cv2.contourArea) #only one packing station, so just take the largest
                    x,y,w,h = cv2.boundingRect(usefulContour)
                    range = self.findRangeHeight(63, h) #perpendicular height: 60
                    bearing = self.findBearing(x, w)
                    usefulX = x
                    usefulY = y
                    #print("Found Yellow! R: " + str(range) + " B: " + str(bearing))
        if len(usefulContour) > 0: #usefulContour has a value - something was identified
            cv2.drawContours(writeFrame, [usefulContour], 0, (173, 13, 106), 2)
            cv2.putText(writeFrame, f"PBay, {range:.0f}mm, {bearing:.1f}*", (usefulX,usefulY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (173, 13, 106), 1)
            outputRB = [range, bearing]

        return writeFrame, outputRB


    def GetDetectedObjects(self):
        # startTime = time.time() #start timer

        #camera - get frame and first step process
        globalFrame = self.currentFrame
        frameHSV = cv2.cvtColor(globalFrame, cv2.COLOR_BGR2HSV) 

        #items
        itemsRB = [None, None, None, None, None, None]

        #packing bay
        globalFrame, packingBayRB = self.packingBay(globalFrame, frameHSV, self.squareThreshold, self.yellowThreshold)

        #obstacles
        globalFrame, obstaclesRB = self.obstacle(globalFrame, frameHSV, self.greenThreshold)

        #row markers
        globalFrame, rowMarkersRB = self.rowMarker(globalFrame, frameHSV, self.blackThreshold)

        #shelves
        globalFrame, shelvesRB = self.shelves(globalFrame, frameHSV, self.blueThreshold)

        outputRB = (itemsRB, packingBayRB, obstaclesRB, rowMarkersRB, shelvesRB)
        print(outputRB)

        # Calculate frames per second (FPS)
        #endTime = time.time() #end timer
        self.currentTime = time.time()
        timeDiff = self.currentTime - self.prevTime
        fps = 1 / timeDiff if timeDiff > 0 else 0
        self.prevTime = self.currentTime
        cv2.putText(globalFrame, f"FPS:{fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        #Resize and Display Processed Image
        frameLarge = cv2.resize(globalFrame, (1200, 900), interpolation=cv2.INTER_LINEAR)
        cv2.imshow("Display", frameLarge)			# Display frame

        cv2.waitKey(1)
        return outputRB
            
  
    def captureImage(self):
        while(1):
            #print("Capturing Image")
            self.currentFrame = self.cap.capture_array()

    def startCapture(self):
        self.cap.start()
        Thread(target=self.captureImage, args=()).start()
        return self

vision_system = visionSystem().startCapture()
globalFrame = np.zeros((vision_system.frameSizeX, vision_system.frameSizeY, 3), np.uint8)


while(1):
    __ = vision_system.GetDetectedObjects()

vision_system.cap.close()
cv2.destroyAllWindows()

# startTime = time.time()
    # # vision_system.cap.start()
    # # vision_system.captureImage()
    # self.currentFrame = vision_system.currentFrame
    # #frame = cv2.resize(frame, (resolutionX, resolutionY))  # Lower resolution
    # #frameCount += 1
    # frameHSV = cv2.cvtColor(self.currentFrame, cv2.COLOR_BGR2HSV) 		# Convert from BGR to HSV colourspace

    # rowThread = Thread(target=vision_system.rowMarker, args=(frameHSV, vision_system.blackThreshold,))
    # obsThread = Thread(target=vision_system.obstacle, args=(frameHSV, vision_system.greenThreshold,))
    # shelThread = Thread(target=vision_system.shelves, args=(frameHSV, vision_system.blueThreshold,))
    # PBThread = Thread(target=vision_system.packingBay, args=(frameHSV, vision_system.squareThreshold, vision_system.yellowThreshold,))
    # rowThread.start()
    # obsThread.start()
    # shelThread.start()
    # PBThread.start()
    # rowThread.join()
    # obsThread.join()
    # shelThread.join()
    # PBThread.join()



    # #wallHeight = findWallHeight(frameHSV, wallThreshold)
    # #itemsRB = items(frameHSV, orangeThreshold)
    # # getImTime = time.time()
    # # #rowMarkerRB = vision_system.rowMarker(frameHSV, vision_system.blackThreshold)
    # # rowTime = time.time()
    # # #obstalcesRB = vision_system.obstacle(frameHSV, vision_system.greenThreshold)
    # # obsTime = time.time()
    # # #shelvesRB = vision_system.shelves(frameHSV, vision_system.blueThreshold)
    # # shelTime = time.time()
    # # #packingBayRB = vision_system.packingBay(frameHSV, vision_system.squareThreshold, vision_system.yellowThreshold)
    # # pbTime = time.time()

    # endTime = time.time()

    # timeDiff = endTime - startTime

    # # timeforImage = 1/(getImTime - startTime)
    # # timeforRow = 1/(rowTime - getImTime)
    # # timeforObs = 1/(obsTime - rowTime)
    # # timeforShel = 1/(shelTime - obsTime)
    # # timeforPb = 1/(pbTime - shelTime)

    # # Calculate frames per second (FPS)
    
    # fps = 1 / timeDiff if timeDiff > 0 else 0
    

    # cv2.putText(self.currentFrame, f"FPS:{fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    # # print("im:", str(timeforImage), "R:", str(timeforRow), "O:", str(timeforObs), "S:", str(timeforShel), "PB:", str(timeforPb))
    
    # frameLarge = cv2.resize(self.currentFrame, (1200, 900), interpolation=cv2.INTER_LINEAR)
    # cv2.imshow("Display", frameLarge)			# Display frame


    # cv2.waitKey(1)									# Exit on keypress







    # def items(frameHSV, thresholdVals):
        # mask = self.threshold(frameHSV, thresholdVals, 255) 
        # contours = self.contourImage(frame, mask)
        
        # contoursFiltered = []
        # outputRB = []
        # # bottles = []
        # # balls = []
        # # cubes = []
        # # cups = []
        # # rects = []
        # # bowls = []
        # for contour in contours:
        #     x,y,w,h = cv2.boundingRect(contour)
        #     if (y+h) > wallHeight:
        #         contoursFiltered.append(contour)
            

        #         itemType, itemHeightMM = "item", 45 #findItemType(contour, w, h)

        #         range = self.findRangeHeight(itemHeightMM, h)
        #         bearing = self.findBearing(x, w)

        #         if x < 2:
        #             xText = 2
        #         else:
        #             xText = x
        #         if y < 35:
        #             yText = 25
        #         else:
        #             yText = y - 10

        #         cv2.putText(frame, f"{itemType}, {range:.0f}mm, {bearing:.1f}*", (xText,yText), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1)
        #         outputRB.append((range, bearing))
        #         # if itemType == "bottle":
        #         #     bottles.append((range, bearing))
        #         # elif itemType == "ball":
        #         #     balls.append((range, bearing))
        #         # elif itemType == "cube":
        #         #     cubes.append((range, bearing))
        #         # elif itemType == "cup":
        #         #     cups.append((range, bearing))
        #         # elif itemType == "rect":
        #         #     rects.append((range, bearing))
        #         # elif itemType == "bowl":
        #         #     bowls.append((range, bearing))
        # # if bottles == []:
        # #     bottles = None
        # # if balls == []:
        # #     balls = None
        # # if cubes == []:
        # #     cubes = None
        # # if cups == []:
        # #     cups = None
        # # if rects == []:
        # #     rects = None
        # # if bowls == []:
        # #     bowls = None
        
        # # outputRB = [bottles, balls, cubes, cups, rects, bowls]
        # cv2.drawContours(frame, contoursFiltered, -1, (0,255,0), 1)
        # return outputRB


  # def findItemType(contour, w, h):
    #     # Aspect Ratios: bottle=0.25, ball=1, cube=1, cup=1.24, rect=1.44, bowl=2.15
    #     # Heights: bottle=72, ball=47, cube=38, cup=42, rect=45, bowl=26
    #     aspectRatio = w / h
    #     if aspectRatio < 0.5:
    #         return "bottle", 72
    #     elif (0.8 < aspectRatio) & (aspectRatio < 1.1):
    #         #ball or cube
    #         if self.isCircle(contour) == True:
    #             return "ball", 47
    #         else:
    #             return "cube", 38
    #     elif (1.1 < aspectRatio) & (aspectRatio < 1.34):
    #         return "cup", 42
    #     elif (1.34 < aspectRatio) & (aspectRatio < 1.8):
    #         return "rect", 45
    #     elif (aspectRatio > 1.8):
    #         return "bowl", 26
    #     else:
    #         return "unknown", 45 #45mm is average height