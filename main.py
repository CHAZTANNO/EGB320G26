# Replace with imports for other subsystems
from warehousebot_lib import *

# Nav imports
from navigation import NavClass as nav
from navigation import state_machine as sm
from mobility import mobility as mob
from mobility import led
from item_collection import item_collection_code as itemcollection

import random
import time
import numpy as np

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
        packerBotSim = COPPELIA_WarehouseRobot("131.181.33.230", robotParameters, sceneParameters)
        packerBotSim.StartSimulator()

        navSystem = nav.NavClass()
        led.setup()

        # parse order data
        navSystem.plan_objectives()
        Frequency = 100.0 #Hz
        Interval = 1.0/Frequency

        while True:
            now = time.time()  # get the time

            # VISION SYSTEM
            # pull vision data in correct format

            # NAVIGATION
            navSystem.update(packerBotSim.GetDetectedObjects(), packerBotSim.GetDetectedWallPoints())

            # MOBILITY
            # update the velo and rot velo as well as LED state
            packerBotSim.SetTargetVelocities(navSystem.forward_vel, navSystem.rot_vel) # 
            mob.SetTargetVelocities(navSystem.forward_vel, navSystem.rot_vel) #
            led.set_LED(navSystem.LEDstate) #
            

            # ITEM COLLECTION
            # tell it to collect at the objective height if needed
            if navSystem.itemState == 'Collecting':
                itemcollection.collect_item(navSystem.currentObjective.get['height'])
                navSystem.itemState = 'Collected'
            
            if navSystem.itemstate == 'Dropping':
                itemcollection.drop_item()
                navSystem.itemState = 'Not_Collected'
                # update objective

            packerBotSim.UpdateObjectPositions()

            print(navSystem.LEDstate)
            elapsed = time.time() - now  # how long was it running?
            if(Interval-elapsed > 0):
                time.sleep(Interval-elapsed) # wait for amount of time left from interval

    except KeyboardInterrupt:
        # Attempt to stop simulator so it restarts and don't have to manually press the Stop button in VREP
        packerBotSim.StopSimulator()
