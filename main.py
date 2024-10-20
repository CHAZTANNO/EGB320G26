# Replace with imports for other subsystems
from warehousebot_lib import *

# Nav imports
from navigation import NavClass as nav
from navigation import state_machine as sm
from mobility import mobility as mob
from mobility import led
from item_collection import item_collection_code as itemCollection
from vision import EGB320_v21 as vis

import random
import time
import numpy as np
import cv2
import datetime

# # SET SCENE PARAMETERS
# sceneParameters = SceneParameters()
# sceneParameters.bayContents = np.random.randint(0, 6, (6, 4, 3))  # Correct function name: np.random.randint
# sceneParameters.bayContents[0, 3, 1] = (warehouseObjects.bowl)  # Specify a bowl in the bay

# sceneParameters.obstacle0_StartingPosition = None
# sceneParameters.obstacle1_StartingPosition = None
# sceneParameters.obstacle2_StartingPosition = None

# # SET ROBOT PARAMETERS
# robotParameters = RobotParameters()
# robotParameters.driveType = ("differential")

if __name__ == "__main__":
    try:
        # packerBotSim = COPPELIA_WarehouseRobot("10.88.40.27", robotParameters, sceneParameters)
        # # '127.0.0.1'
        # packerBotSim.StartSimulator()

        navSystem = nav.NavClass()
        led.setup()
        mob.setupMob()
        visSys = vis.visionSystem()
        print('MADE IT HERE!')
        vision_system = visSys.startCapture()

        # parse order data
        navSystem.plan_objectives()
        Frequency = 10000.0 #Hz
        Interval = 1.0/Frequency

        # raise lift to shelf 2
        #itemCollection.lift_to_shelf(1)
        #navSystem.liftHeight = 1

        print('STARTING MAIN LOOP!')
        while True:
            now = time.time()  # get the time
            state = str(navSystem.my_sm.get_current_state())

            # VISION SYSTEM
            # pull vision data in correct format
            GetDetectedObjectsOutput = vision_system.GetDetectedObjects()
            print(GetDetectedObjectsOutput)
            GetDetectedWallPointsOutput = vision_system.GetDetectedWallPoints()

            # NAVIGATION
            navSystem.update(GetDetectedObjectsOutput, GetDetectedWallPointsOutput)
            # navSystem.update(packerBotSim.GetDetectedObjects(), packerBotSim.GetDetectedWallPoints())

            # MOBILITY
            # update the velo and rot velo as well as LED state
            #packerBotSim.SetTargetVelocities(navSystem.forward_vel, navSystem.rot_vel) #
            mobfvel, mobrvel = navSystem.normalise_velocity(navSystem.forward_vel, navSystem.rot_vel)
            mob.SetTargetVelocities(mobfvel, -mobrvel) #

            if state == 'idleState':
                break

            print(mobfvel)
            print(-mobrvel)
            led.set_LED(navSystem.LEDstate)
            

            # ITEM COLLECTION
            if state == 'adjustingLiftHeightState':
                navSystem.liftState = 1
                if navSystem.liftHeight != navSystem.currentObjective['height']:
                    if navSystem.currentObjective['height'] == 0:
                        mob.stopAll()
                        itemCollection.lower_lift_to_shelf_1()
                    elif navSystem.currentObjective['height'] == 1:
                        mob.stopAll()
                        itemCollection.lift_to_shelf(1)
                while True:
                    if itemCollection.getICShelfState() == navSystem.currentObjective['height']:
                        navSystem.liftHeight = navSystem.currentObjective['height']
                        break
                navSystem.timerA = datetime.now()
                navSystem.liftState = 0

            if state == 'liftStabilisationState':
                if navSystem.liftHeight != 1:
                    itemCollection.lift_to_shelf(1)
                    while True:
                        if itemCollection.getICShelfState() == 1:
                            navSystem.liftHeight = navSystem.currentObjective['height']
                            break
                    navSystem.liftHeight = 1

            # tell it to collect at the objective height if needed
            if state == 'collectItemState':
                itemCollection.close_gripper()
                time.sleep(2)
                #packerBotSim.CollectItem(navSystem.currentObjective['height'])
                navSystem.itemState = 'Collected'
            
            if navSystem.itemState == 'Dropping':
                #packerBotSim.Dropitem()
                if navSystem.liftHeight > 0:
                    #itemCollection.lower_to_shelf(0)
                    navSystem.liftHeight = 0
                #itemcollection.drop_item()
                navSystem.itemState = 'Not_Collected'

                # change to new objective
                index = navSystem.objectives.index(navSystem.currentObjective)+1
                length = len(navSystem.objectives)
                if index <= length:
                    navSystem.currentObjective = navSystem.objectives[index]

            #packerBotSim.UpdateObjectPositions()

            #print(navSystem.LEDstate)s
            # elapsed = time.time() - now  # how long was it running?
            # if(Interval-elapsed > 0):
            #     time.sleep(Interval-elapsed) # wait for amount of time left from interval

        mob.stopAll()
        led.set_LED("OFF")
        if navSystem.liftHeight > 0:
            itemCollection.lower_lift_to_start()

        time.sleep(3)
        itemCollection.drop_item()
        
    except KeyboardInterrupt:
        # Attempt to stop simulator so it restarts and don't have to manually press the Stop button in VREP
        mob.stopAll()
        led.set_LED("OFF")
        vision_system.cap.close()
        cv2.destroyAllWindows()
        #packerBotSim.StopSimulator()
