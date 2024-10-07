import time
import picamera2
import cv2
import numpy as np
from threading import Thread
from pprint import *
import math

class visionSystem:
    def __init__(self):

        self.prevTime = 0
        self.currentTime = 0

        self.cap = picamera2.Picamera2()
        self.frameSizeX = 300#820
        self.frameSizeY = 225#616
        self.minArea = int(self.frameSizeX*self.frameSizeY / 600)
        self.currentFrame = np.zeros((self.frameSizeX, self.frameSizeY, 3), np.uint8)
        # frameCount = 0
        config = self.cap.create_video_configuration(main={"format":'XRGB8888',"size":(self.frameSizeX,self.frameSizeY)},
                                                controls={'FrameRate': 50},
                                                raw={'size': (1640, 1232)})

        pprint(self.cap.sensor_modes)                                        
        self.cap.configure(config)
        self.cap.set_controls({"ExposureTime": 200000, "AnalogueGain": 1.2, "ColourGains": (1.4,1.5)})
        #STANDARD EXPOSURE: 200000, 1.2
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

        self.blueThreshold = [78, 122, 77, 255, 30, 178]
        self.orangeThreshold = [0, 18, 179, 255, 73, 255]
        self.yellowThreshold = [11, 33, 166, 255, 192, 255]
        self.greenThreshold = [50, 83, 67, 202, 0, 127]
        self.blackThreshold = [18, 79, 0, 83, 20, 88]
        self.squareThreshold = [15, 44, 55, 131, 59, 118]
        self.wallThreshold = [25, 55, 13, 115, 170, 255]

        self.colShelf = (108, 147, 45)
        self.colObstacle = (255, 126, 127)
        self.colRowMarker = (255, 231, 27)
        self.colPB = (196, 161, 247)
        self.colItem = (96, 233, 245)
        self.colWall = (75, 110, 222)
        self.colFPS = (56, 13, 146)


    def threshold(self, frame, thresholds):
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
        if (0.7 < circularity < 1.3):# Check for circle
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

    def findRangeWall(self, y, maskFullHeight):
        range = 0
        if y < 135: #too far away, use wall height
            contours, __ = cv2.findContours(maskFullHeight, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            largestContour = max(contours, key=cv2.contourArea)
            __,__,__,h = cv2.boundingRect(largestContour)
            range = self.findRangeHeight(450, h)
        else: #can't see top of wall, use amount of carpet seen
            range = 14.58891 + (173504700 - 14.58891)/(1 + ((y/21.52743)**7.974995)) #((10^(-5)) * (y^4)) - (0.008*(y^3)) + (2.1877*(y^2)) - (256.61 * y) + 12131
        print(range)
        return range

    def get_orientation(self, line):
        orientation = math.atan2(abs((line[3] - line[1])), abs((line[2] - line[0])))
        return math.degrees(orientation)

    def check_is_line_different(self, line_1, groups, min_distance, min_angle):
        for group in groups:
            for line_2 in group:
                if self.get_distance(line_2, line_1) < min_distance:
                    orientation_1 = self.get_orientation(line_1)
                    orientation_2 = self.get_orientation(line_2)
                    if abs(orientation_1 - orientation_2) < min_angle:
                        group.append(line_1)
                        return False
        return True

    def distance_point_to_line(self, point, line):
        px, py = point
        x1, y1, x2, y2 = line

        def line_magnitude(x1, y1, x2, y2):
            return math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1), 2))

        lmag = line_magnitude(x1, y1, x2, y2)
        if lmag < 0.00000001:
            return 9999

        u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
        u = u1 / (lmag * lmag)

        if (u < 0.00001) or (u > 1):
            ix = line_magnitude(px, py, x1, y1)
            iy = line_magnitude(px, py, x2, y2)
            return min(ix, iy)
        else:
            ix = x1 + u * (x2 - x1)
            iy = y1 + u * (y2 - y1)
            return line_magnitude(px, py, ix, iy)

    def get_distance(self, a_line, b_line):
        dist1 = self.distance_point_to_line(a_line[:2], b_line)
        dist2 = self.distance_point_to_line(a_line[2:], b_line)
        dist3 = self.distance_point_to_line(b_line[:2], a_line)
        dist4 = self.distance_point_to_line(b_line[2:], a_line)
        return min(dist1, dist2, dist3, dist4)

    def merge_lines_into_groups(self, lines, min_distance, min_angle):
        groups = [[lines[0]]]
        for line_new in lines[1:]:
            if self.check_is_line_different(line_new, groups, min_distance, min_angle):
                groups.append([line_new])
        return groups

    def merge_line_segments(self, lines):
        orientation = self.get_orientation(lines[0])
        
        if len(lines) == 1:
            return np.block([[lines[0][:2], lines[0][2:]]])

        points = []
        for line in lines:
            points.append(line[:2])
            points.append(line[2:])
        if 45 < orientation <= 90:
            points = sorted(points, key=lambda point: point[1])
        else:
            points = sorted(points, key=lambda point: point[0])

        return np.block([[points[0], points[-1]]])

    def process_lines(self, lines, min_distance, min_angle):
        lines_horizontal = []
        lines_vertical = []
        
        for line_i in [l[0] for l in lines]:
            orientation = self.get_orientation(line_i)
            if 45 < orientation <= 90:
                lines_vertical.append(line_i)
            else:
                lines_horizontal.append(line_i)

        lines_vertical = sorted(lines_vertical, key=lambda line: line[1])
        lines_horizontal = sorted(lines_horizontal, key=lambda line: line[0])
        merged_lines_all = []

        for i in [lines_horizontal, lines_vertical]:
            if len(i) > 0:
                groups = self.merge_lines_into_groups(i, min_distance, min_angle)
                merged_lines = [self.merge_line_segments(group) for group in groups]
                merged_lines_all.extend(merged_lines)
                    
        return np.asarray(merged_lines_all)

    def findItemType(self, contour, w, h):
        # Aspect Ratios: bottle=0.25, ball=1, cube=1, cup=1.24, rect=1.44, bowl=2.15
        # Heights: bottle=72, ball=47, cube=38, cup=42, rect=45, bowl=26
        aspectRatio = w / h
        if aspectRatio < 0.5:
            return "bottle", 72
        elif (0.8 < aspectRatio) & (aspectRatio < 1.1):
            #ball or cube
            if self.isCircle(contour) == True:
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


    def rowMarker(self, writeFrame, frameHSV, thresholdVals):
        outputRB = [None, None, None]
        mask = self.threshold(frameHSV, thresholdVals) 
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
                    cv2.drawContours(writeFrame, [contour], 0, self.colRowMarker, 1)
                    ranges.append(range)
                    bearings.append(bearing)
                    xs.append(x)
                    ys.append(y)
            if (0 < circleCount <= 3):
                meanRange = np.mean(ranges)
                meanBearing = np.mean(bearings)
                minX = np.min(xs)
                minY = np.min(ys)
                cv2.putText(writeFrame, f"R{circleCount} {meanRange:.0f} {meanBearing:.1f}", (minX,minY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colRowMarker, 1)
                RB = [(meanRange/1000), math.radians(meanBearing)]
                outputRB[circleCount-1] = RB
        
        return writeFrame, outputRB
          
    def obstacle(self, writeFrame, frame, thresholdVals):
        mask = self.threshold(frame, thresholdVals)
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

                cv2.putText(writeFrame, f"O {range:.0f} {bearing:.1f}", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colObstacle, 1)
                outputRB.append(((range/1000), math.radians(bearing)))
            
            cv2.drawContours(writeFrame, contours, -1, self.colObstacle, 1)
        else:
            outputRB = None
        return writeFrame, outputRB

    def shelves(self, writeFrame, frame, thresholdVals):
        mask = self.threshold(frame, thresholdVals)
        splitMask = mask


        if cv2.countNonZero(mask) > self.minArea:
            edges = cv2.Canny(mask, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=20, maxLineGap=50)

            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Calculate the angle in radians
                    angleDeg = math.degrees(math.atan2(y2 - y1, x2 - x1))
                    # cv2.line(writeFrame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    if angleDeg < 0:
                        angleDeg += 180
                    if 70 < angleDeg < 110: #verticalish
                        avgx = int((x1+x2)/2) #split the image here
                        splitMask[:, avgx-7:avgx+7] = 0
                    
            contours = self.contourImage(splitMask)

            outputRB = []
            for contour in contours:
                x,y,w,h = cv2.boundingRect(contour)
                
                range = self.findRangeHeight(312, h)
                bearing = self.findBearing(x, w)
                cv2.putText(writeFrame, f"S {range:.0f} {bearing:.1f}", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colShelf, 1)
                outputRB.append(((range/1000), math.radians(bearing)))
            
            cv2.drawContours(writeFrame, contours, -1, self.colShelf, 1)
            # outputRB = outputRB.sort(key = lambda x: x[1]) #self.sortBearingLtoR(outputRB) #sort by bearing, left to right
            outputRB = sorted(outputRB, key=lambda x: x[1])
        else:
            outputRB = None

        return writeFrame, outputRB

    def packingBay(self, writeFrame, frame, threshValsSquare, threshValsYel):
        outputRB = None
        usefulContour = []
        usefulX, usefulY = 0, 0
        squareCount = 0
        # if can see square, use that, if not use yellow
        maskSquare = self.threshold(frame, threshValsSquare)
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
            maskYel = self.threshold(frame, threshValsYel)
            if cv2.countNonZero(maskYel) > self.minArea:
                contoursYel = self.contourImage(maskYel)

                if contoursYel:  # Make sure there are contours
                    usefulContour = max(contoursYel, key=cv2.contourArea) #only one packing station, so just take the largest
                    x,y,w,h = cv2.boundingRect(usefulContour)
                    range = self.findRangeHeight(63, h) #perpendicular height: 60
                    bearing = self.findBearing(x, w)
                    usefulX = x
                    usefulY = y
        if len(usefulContour) > 0: #usefulContour has a value - something was identified
            cv2.drawContours(writeFrame, [usefulContour], 0, self.colPB, 1)
            cv2.putText(writeFrame, f"PB {range:.0f} {bearing:.1f}", (usefulX,usefulY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colPB, 1)
            outputRB = [(range/1000), math.radians(bearing)]

        return writeFrame, outputRB

    def items(self, writeFrame, frame, thresholdVals):
        mask = self.threshold(frame, thresholdVals) 
        outputRB = []
        if cv2.countNonZero(mask) > self.minArea:
            contours = self.contourImage(mask)
            cv2.drawContours(writeFrame, contours, -1, self.colItem, 1)
            for contour in contours:
                x,y,w,h = cv2.boundingRect(contour)

                itemType, itemHeightMM = self.findItemType(contour, w, h) #"item", 45 

                rangeI = self.findRangeHeight(itemHeightMM, h)
                bearing = self.findBearing(x, w)

                cv2.putText(writeFrame, f"I {rangeI:.0f} {bearing:.1f}", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colItem, 1)
                outputRB.append(((rangeI/1000), math.radians(bearing)))
        
        if len(outputRB) <= 0:
            outputRB = None
        return writeFrame, outputRB

    def walls(self, writeFrame, frame, thresholdVals):
        height, width = frame.shape[:2]

        # Create a mask with the same size as the image (bottom half set to 255, top half set to 0) - walls always below half way
        maskBottomOnly = np.zeros((height, width), dtype=np.uint8)
        maskBottomOnly[height//2:, :] = 255  # Keep only the bottom half
        
        openKernel = np.ones((15,15), np.uint8)
        erodeKernel = np.ones((9,9), np.uint8)
        
        whiteMask = self.threshold(frame, thresholdVals)
        mask = whiteMask & maskBottomOnly

        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, openKernel)
        openingFullHeight = cv2.morphologyEx(whiteMask, cv2.MORPH_OPEN, openKernel)

        cv2.imshow('full', openingFullHeight)
        # cv2.imshow("open", opening)

        edges = cv2.Canny(opening, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=50, maxLineGap=80)
        # cv2.imshow("edges", edges)

        min_height = height
        wallLine = None
        pointCount = 0
        midx = 0
        midy = 0
        if lines is not None:
            # cv2.line(frameGlobal, (x1, y1), (x2, y2), (0, 255, 255), 2)
            mergedLines = self.process_lines(lines, min_distance=10, min_angle=5)
            
            for line in mergedLines:
                x1, y1, x2, y2 = line[0]
                xAvg = int((x1+x2)/2)
                yAvg = int((y1+y2)/2)
                # cv2.line(frameGlobal, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        
                angleDeg = math.degrees(math.atan2(y2 - y1, x2 - x1))
                if angleDeg < 0: #convert to absolute angle
                    angleDeg += 180

                if ((angleDeg < 80) or (angleDeg > 100)) and (y1 > height/2+5) and (yAvg < min_height): 
                    min_height = yAvg
                    if (angleDeg > 10) and (angleDeg < 170): #not head on, one point only
                        pointCount = 1
                        midx = xAvg
                        midy = yAvg
                    else:
                        pointCount = 2
                        wallLine = (x1, y1, x2, y2)

        # Draw the highest line
        if pointCount == 1:
            rangeMid = self.findRangeWall(midy, openingFullHeight)
            bearingMid = self.findBearing(midx, 1)
            cv2.circle(writeFrame, (midx,midy), 3, self.colWall, -1)
            cv2.putText(writeFrame, f"{rangeMid:.0f} {bearingMid:.1f}", (midx,midy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colWall, 1)
            outputRB = [[(rangeMid/1000), math.radians(bearingMid)], None, None]
        elif pointCount == 2:
            x1, y1, x2, y2 = wallLine
            # print(f'{y1}   {y2}')
            range1 = self.findRangeWall(y1, openingFullHeight)
            range2 = self.findRangeWall(y1, openingFullHeight)
            bearing1 = self.findBearing(x1, 1)
            bearing2 = self.findBearing(x2,1)

            cv2.putText(writeFrame, f"{range1:.0f} {bearing1:.1f}", (x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colWall, 1)
            cv2.putText(writeFrame, f"{range2:.0f} {bearing2:.1f}", (x2,y2-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colWall, 1)
            cv2.circle(writeFrame, (x1,y1), 3, self.colWall, -1)
            cv2.circle(writeFrame, (x2,y2), 3, self.colWall, -1)
            outputRB = [[(range1/1000), math.radians(bearing1)], None, [(range2/1000), math.radians(bearing2)]]
        else:
            outputRB = [None, None, None]
            
        # cv2.imshow('frame', writeFrame)
        return writeFrame, outputRB

   
    def GetDetectedObjects(self):
        # startTime = time.time() #start timer

        #camera - get frame and first step process
        globalFrame = self.currentFrame
        frameHSV = cv2.cvtColor(globalFrame, cv2.COLOR_BGR2HSV) 

        #items
        globalFrame, itemsRB = self.items(globalFrame, frameHSV, self.orangeThreshold)

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
        cv2.putText(globalFrame, f"FPS:{fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colItem, 1)
        
        #Resize and Display Processed Image
        frameLarge = cv2.resize(globalFrame, (900, 675), interpolation=cv2.INTER_LINEAR)
        cv2.imshow("GetDetectedObjects", frameLarge)			# Display frame

        cv2.waitKey(1)
        return outputRB

    def GetDetectedWallPoints(self):
        wallFrame = self.currentFrame
        frameHSV = cv2.cvtColor(wallFrame, cv2.COLOR_BGR2HSV) 

        wallFrame, outputRB = self.walls(wallFrame, frameHSV, self.wallThreshold)

        frameLarge = cv2.resize(wallFrame, (600, 450), interpolation=cv2.INTER_LINEAR)
        cv2.imshow("GetDetectedWallPoints", frameLarge)			# Display frame

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
    GetDetectedObjectsOutput = vision_system.GetDetectedObjects()
    GetDetectedWallPointsOutput = vision_system.GetDetectedWallPoints()


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







    