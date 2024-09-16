# Replace with imports for other subsystems
from warehousebot_lib import *

# Nav imports
from navigation import NavClass as nav
from navigation import state_machine as sm

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
        packerBotSim = COPPELIA_WarehouseRobot("127.0.0.1", robotParameters, sceneParameters)
        packerBotSim.StartSimulator()

        navSystem = nav.NavClass()

        # parse order data
        navSystem.plan_objectives()

        while True:
            # now = time.time()  # get the time

            # VISION SYSTEM
            # pull vision data in correct format

            # NAVIGATION
            navSystem.update(packerBotSim.GetDetectedObjects(), packerBotSim.GetDetectedWallPoints())

            # MOBILITY
            # update the velo and rot velo as well as LED state
            packerBotSim.SetTargetVelocities(navSystem.forward_vel, navSystem.rot_vel) # 

            # ITEM COLLECTION
            # tell it to collect at the objective height if needed
            if navSystem.itemState == 'Collecting':
                navSystem.itemState = 'Collected' # call nav function @ navSystem.currentObjective.get['height']

            packerBotSim.UpdateObjectPositions()

            print(navSystem.LEDstate)

    except KeyboardInterrupt:
        # Attempt to stop simulator so it restarts and don't have to manually press the Stop button in VREP
        packerBotSim.StopSimulator()