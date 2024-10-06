import time
import picamera2
import cv2
import numpy as np
import math

cap = picamera2.Picamera2()
config = cap.create_video_configuration(main={"format":'XRGB8888',"size":(820,616)})
cap.configure(config)
cap.set_controls({"ExposureTime": 200000, "AnalogueGain": 1.2, "ColourGains": (1.4,1.5)})


cap.start()

def threshold(frame, thresholds):
    hFrame = frame[:,:,0] # Extract hue channel
    sFrame = frame[:,:,1] # Extract saturation channel
    vFrame = frame[:,:,2] # Extract value channel

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

def contourImage(mask):
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

def walls(frame, thresholdVals):
    height, width = frame.shape[:2]

    # Create a mask with the same size as the image (bottom half set to 255, top half set to 0)
    maskBottomOnly = np.zeros((height, width), dtype=np.uint8)
    maskBottomOnly[height//2:, :] = 255  # Keep only the bottom half
     
    openKernel = np.ones((15,15), np.uint8)
    erodeKernel = np.ones((9,9), np.uint8)
    
    kernel = np.ones((5,5), np.uint8)
    grey = frame[:,:,2]
    # __, whiteMask = cv2.threshold(grey, 163, 255, cv2.THRESH_BINARY)
    whiteMask = threshold(frame, thresholdVals)
    mask = whiteMask & maskBottomOnly
    # cv2.imshow("whiteMask", whiteMask)
    opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, openKernel)
    cv2.imshow("open", opening)
    
    expandedMask = cv2.erode(opening, erodeKernel, iterations=1)

    edges = cv2.Canny(opening, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=20, maxLineGap=80)
    cv2.imshow("edges", edges)

    min_height = height
    wallLine = None
    if lines is not None:
        x1, y1, x2, y2 = line[0]
        cv2.line(frameGlobal, (x1, y1), (x2, y2), (0, 255, 255), 2)
        mergedLines = process_lines(lines, min_distance=10, min_angle=5)
        
        for line in mergedLines:
            x1, y1, x2, y2 = line[0]
            xAvg = int((x1+x2)/2)
            yAvg = int((y1+y2)/2)
            cv2.line(frameGlobal, (x1, y1), (x2, y2), (0, 0, 255), 2)
            if (expandedMask[yAvg, xAvg] != 0) and  (y1 > height/2+5) and (yAvg < min_height): #((expandedMask[y1,x1] == 0) or (x1 < 40) or (x1 > width-40)) and ((expandedMask[y2,x2] == 0) or (x2 < 40) or (x2 > width-40))
                min_height = yAvg
                wallLine = (x1, y1, x2, y2)

        # Draw the highest line
        if wallLine is not None:
            x1, y1, x2, y2 = wallLine
            cv2.circle(frameGlobal, (x1,y1), 10, (255,0,255), -1)
            cv2.circle(frameGlobal, (x2,y2), 10, (255,255,0), -1)

    cv2.imshow('frame', frameGlobal)

    # contours, heirarchy = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # for contour in contours:
    #     area = cv2.contourArea(contour)
    #     if area > 400:
    #         cv2.drawContours(frameGlobal, [contour], 0, (0, 0, 255), 2)
    # cv2.imshow("frame", frameGlobal)
            
    # whiteMask = cv2.erode(whiteMask, largeKernel, iterations=1)
    # mask = maskBottomOnly & whiteMask
    
    # expandedMask = cv2.erode(mask, largeKernel, iterations=1)
    # maskedImage = cv2.bitwise_and(frame, frame, mask= mask)

    # blurred = cv2.GaussianBlur(maskedImage, (19, 19), 0)
    # blurred = cv2.GaussianBlur(blurred, (15, 15), 0)
    # blurred = cv2.GaussianBlur(blurred, (19, 19), 0)
    # cv2.imshow("gau", blurred)


    # filtered_image = cv2.bilateralFilter(maskedImage, d=9, sigmaColor=150, sigmaSpace=150)
    # cv2.imshow("bila", filtered_image)

    # maskedImage = blurred

    # edges = cv2.Canny(maskedImage, 10, 15)
    # # cv2.imshow("edges", edges)
    # lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=20, maxLineGap=80)
    # # ^outputs (x1, y1, x2, y2) which are start and end coords of (straight) lines
    

    # 
    # 
def get_orientation(line):
    orientation = math.atan2(abs((line[3] - line[1])), abs((line[2] - line[0])))
    return math.degrees(orientation)

def check_is_line_different(line_1, groups, min_distance, min_angle):
    for group in groups:
        for line_2 in group:
            if get_distance(line_2, line_1) < min_distance:
                orientation_1 = get_orientation(line_1)
                orientation_2 = get_orientation(line_2)
                if abs(orientation_1 - orientation_2) < min_angle:
                    group.append(line_1)
                    return False
    return True

def distance_point_to_line(point, line):
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

def get_distance(a_line, b_line):
    dist1 = distance_point_to_line(a_line[:2], b_line)
    dist2 = distance_point_to_line(a_line[2:], b_line)
    dist3 = distance_point_to_line(b_line[:2], a_line)
    dist4 = distance_point_to_line(b_line[2:], a_line)
    return min(dist1, dist2, dist3, dist4)

def merge_lines_into_groups(lines, min_distance, min_angle):
    groups = [[lines[0]]]
    for line_new in lines[1:]:
        if check_is_line_different(line_new, groups, min_distance, min_angle):
            groups.append([line_new])
    return groups

def merge_line_segments(lines):
    orientation = get_orientation(lines[0])
    
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

def process_lines(lines, min_distance, min_angle):
    lines_horizontal = []
    lines_vertical = []
    
    for line_i in [l[0] for l in lines]:
        orientation = get_orientation(line_i)
        if 45 < orientation <= 90:
            lines_vertical.append(line_i)
        else:
            lines_horizontal.append(line_i)

    lines_vertical = sorted(lines_vertical, key=lambda line: line[1])
    lines_horizontal = sorted(lines_horizontal, key=lambda line: line[0])
    merged_lines_all = []

    for i in [lines_horizontal, lines_vertical]:
        if len(i) > 0:
            groups = merge_lines_into_groups(i, min_distance, min_angle)
            merged_lines = [merge_line_segments(group) for group in groups]
            merged_lines_all.extend(merged_lines)
                
    return np.asarray(merged_lines_all)


while(1):
    frameGlobal = cap.capture_array()
    frameHSV = cv2.cvtColor(frameGlobal, cv2.COLOR_BGR2HSV) 		# Convert from BGR to HSV colourspace

    
    wallThreshold = [2, 42, 0, 70, 150, 232]
    wallThreshold2 = [2, 63, 6, 70, 118, 221]
    wallThreshold3 = [2, 75, 0, 85, 163, 255]

    greyThreshold = [19, 63, 6, 66, 118, 205]

    walls(frameHSV, wallThreshold3)


    # cv2.imshow("Threshold", frameGlobal)			# Display thresholded frame
    # cv2.imshow("filtered", maskedImage)
    #cv2.imshow("Original", mask)
    # cv2.imshow("hi", maskedImage)


    cv2.waitKey(1)									# Exit on keypress

cap.close()
cv2.destroyAllWindows()
