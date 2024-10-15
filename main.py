# Replace with imports for other subsystems
from warehousebot_lib import *

# Nav imports
from navigation import NavClass as nav
from navigation import state_machine as sm
from mobility import mobility as mob
from mobility import led
from item_collection import item_collection_code as itemcollection
from vision import EGB320_v21 as vis

import random
import time
import numpy as np
import cv2

# SET SCENE PARAMETERS
sceneParameters = SceneParameters()
sceneParameters.bayContents = np.random.randint(0, 6, (6, 4, 3))  # Correct function name: np.random.randint
sceneParameters.bayContents[0, 3, 1] = (warehouseObjects.bowl)  # Specify a bowl in the bay

sceneParameters.obstacle0_StartingPosition = None
sceneParameters.obstacle1_StartingPosition = None
sceneParameters.obstacle2_StartingPosition = None

# SET ROBOT PARAMETERS
robotParameters = RobotParameters()
robotParameters.driveType = ("differential")

if __name__ == "__main__":
    try:
        packerBotSim = COPPELIA_WarehouseRobot("131.181.33.22", robotParameters, sceneParameters)
        #'127.0.0.1'
        #packerBotSim.StartSimulator()

        navSystem = nav.NavClass()
        led.setup()
        mob.setupMob()
        visSys = vis.visionSystem()
        print('MADE IT HERE!')
        vision_system = visSys.startCapture()

        # parse order data
        navSystem.plan_objectives()
        Frequency = 100.0 #Hz
        Interval = 1.0/Frequency

        print('STARTING MAIN LOOP!')
        while True:
            now = time.time()  # get the time

            # VISION SYSTEM
            # pull vision data in correct format
            GetDetectedObjectsOutput = vision_system.GetDetectedObjects()
            GetDetectedWallPointsOutput = vision_system.GetDetectedWallPoints()

            # NAVIGATION
            navSystem.update(GetDetectedObjectsOutput, GetDetectedWallPointsOutput)
            # navSystem.update(packerBotSim.GetDetectedObjects(), packerBotSim.GetDetectedWallPoints())

            # MOBILITY
            # update the velo and rot velo as well as LED state
            #packerBotSim.SetTargetVelocities(navSystem.forward_vel, navSystem.rot_vel) #
            mobfvel, mobrvel = navSystem.normalise_velocity(navSystem.forward_vel, navSystem.rot_vel)
            mob.SetTargetVelocities(mobfvel, -mobrvel) #
            print(mobfvel)
            print(-mobrvel)
            led.set_LED(navSystem.LEDstate)
            

            # ITEM COLLECTION
            # tell it to collect at the objective height if needed
            if navSystem.itemState == 'Collecting':
                #itemcollection.lift_to_shelf(navSystem.currentObjective.get['height'])
                #itemcollection.close_gripper()
                #packerBotSim.CollectItem(navSystem.currentObjective['height'])
                navSystem.itemState = 'Collected'
            
            if navSystem.itemState == 'Dropping':
                #itemcollection.drop_item()
                #packerBotSim.Dropitem()
                navSystem.itemState = 'Not_Collected'

            #packerBotSim.UpdateObjectPositions()

            #print(navSystem.LEDstate)s
            elapsed = time.time() - now  # how long was it running?
            if(Interval-elapsed > 0):
                time.sleep(Interval-elapsed) # wait for amount of time left from interval
    except KeyboardInterrupt:
        # Attempt to stop simulator so it restarts and don't have to manually press the Stop button in VREP
        mob.SetTargetVelocities(0, 0)
        mob.SetTargetVelocities(0, 0)
        vision_system.cap.close()
        cv2.destroyAllWindows()
        #packerBotSim.StopSimulator()
