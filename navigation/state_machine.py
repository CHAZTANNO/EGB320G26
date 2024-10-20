import time
import random
from navigation import NavClass as nav
from datetime import datetime
from item_collection import item_collection_code as itemCollection
from mobility import mobility as mob

class State:

    def __init__(self):
        print('Current state:', str(self))

    def run():
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__

class startState(State):

    def run(self, navSys):
        print('Calibrating sensors...')
        event = ''
        rowNo = navSys.objectiveRow
        
        if rowNo == 2:
            event = 'finished_calibration'
        elif rowNo == 1:
            if navSys.dataDict['packingBayRB'] != None and (navSys.dataDict['packingBayRB'][0] <= 0.40):
                event = 'finished_calibration'
        else:
            if navSys.dataDict['packingBayRB'] != None and (navSys.dataDict['packingBayRB'][0] <= 0.15):    
                event = 'finished_calibration'
            elif navSys.dataDict['packingBayRB'] == None:
                event = 'finished_calibration'

        #Check transition event
        if event == 'finished_calibration':
            return explorationState()
        else:
            return startState()

class explorationState(State):

    def run(self, navSys):
        print('Searching for shelves...')

        rowEstimate = navSys.rowEstimation
        rowNo = navSys.objectiveRow

        if rowEstimate[0] != None:
            if navSys.objectiveRow==0:
                # row estimation identified
                event = 'row_pose_estimated'
            elif navSys.objectiveRow==1 and rowEstimate[0][0]<1:
                # row estimation identified
                event = 'row_pose_estimated'
            elif navSys.objectiveRow==2 and rowEstimate[0][0]<0.70:
                # row estimation identified
                event = 'row_pose_estimated'
            else:
                event = 'row_pose_not_found'
        else:
            event = 'row_pose_not_found'

        #Check transition event
        if event == 'row_pose_estimated':
            return searchState()
        else:
            return explorationState()

class searchState(State):

    def run(self, navSys):
        print('Searching for row...')

        rowNo = navSys.objectiveRow

        if navSys.dataDict['rowMarkerRB'][rowNo] != None:
            # row marker identified
            event = 'row_marker_found' 
        elif navSys.rowEstimation[0] == None:
            # lost row estimation
            event = 'lost_row_estimation'
            return explorationState()
        else:
            event = 'row_marker_not_found'

        #Check transition event
        if event == 'row_marker_found':
            return movingDownRowState()
        else:
            return searchState()

class movingDownRowState(State):

    def run(self, navSys):
        print('Moving down row...')
        event = ''
        rowNo = navSys.objectiveRow
        chassisOffset = 0.1

        # print(navSys.dataDict['rowMarkerRB'][rowNo])
        # print(navSys.dataDict['wallPoints'])

        if navSys.dataDict['rowMarkerRB'][rowNo] != None:
            if navSys.dataDict['rowMarkerRB'][rowNo][0] <= navSys.BAY_DISTANCES[navSys.currentObjective['bay']]:
                event = 'arrived_at_bay'
            elif navSys.currentObjective['bay'] == 3:
                if navSys.dataDict['rowMarkerRB'][rowNo][0] <= navSys.BAY_DISTANCES[2]:
                    event = 'arrived_at_bay_2'
            else:
                event = 'travelling_to_bay'
        else:
            if rowNo == 2:
                event = 'travelling_to_bay'
            else:
                event = 'lost_in_row'
        
        #Check transition event
        if event == 'arrived_at_bay':
            navSys.timerA = datetime.now()
            return aligningWithBayState()
        elif event == 'lost_in_row':
            return lostInRowState()
        elif event == 'arrived_at_bay_2':
            navSys.timerA = datetime.now()
            return bruteForcingBay3State()
        else:
            return movingDownRowState()

class bruteForcingBay3State(State):

    def run(self, navSys):
        print('At bay 2, moving to 3...')
        event = ''
        rowNo = navSys.objectiveRow
        navSys.timerB = datetime.now()

        delta = navSys.timerB - navSys.timerA
        seconds = delta.total_seconds()

        if seconds >= 3.5:
            event = 'arrived_at_bay'
        
        #Check transition event
        if event == 'arrived_at_bay':
            navSys.timerA = datetime.now()
            return aligningWithBayState()
        else:
            return bruteForcingBay3State()

class lostInRowState(State):

    def run(self, navSys):
        print('Lost row marker...')
        rowNo = navSys.objectiveRow
        if navSys.dataDict['rowMarkerRB'][rowNo] != None:
            event = 'found_row_marker'
        else:
            event = 'lost_row_marker'
        
        #Check transition event
        if event == 'found_row_marker':
            return movingDownRowState()
        else:
            return lostInRowState()
        
class movingToBayState(State):

    def run(self, navSys):
        print('Backing out to bay...')
        rowNo = navSys.objectiveRow
        chassisOffset = 0.1255
        if navSys.dataDict['rowMarkerRB'][rowNo] != None:
            if navSys.dataDict['rowMarkerRB'][rowNo][0] >= navSys.BAY_DISTANCES[navSys.currentObjective['bay']]-chassisOffset:
                event = 'arrived_at_bay'
            else:
                event = 'travelling_to_bay'
        else:
            event = 'travelling_to_bay'
        
        #Check transition event
        if event == 'arrived_at_bay':
            navSys.timerA = datetime.now()
            return aligningWithBayState()
        else:
            return movingToBayState()

class aligningWithBayState(State):

    def run(self, navSys):
        navSys.timerB = datetime.now()
        print('Aligning with bay...')
        event = ''

        # check to see if an orange item is directly in front of you and close
        if navSys.dataDict['itemsRB'] != None:
            for items in navSys.dataDict['itemsRB']:
                if items != None:
                    for item in items:
                        if item != None:
                            if isinstance(item, float):
                                if (items[1] <= 0.2 and items[1] >= -0.2) and items[0] < 0.20:
                                    event = 'facing_bay'
                            elif item[0] < 0.20:
                                if (item[1] <= 0.2 and item[1] >= -0.2):
                                    event = 'facing_bay'

        if event=='facing_bay':
            navSys.LEDstate = 'YELLOW'
            navSys.timerA = datetime.now()
            return givingLiftSpace()
        else:
            return aligningWithBayState()


class givingLiftSpace(State):

    def run(self, navSys):
        print('Backing up to give lift space...')
        navSys.timerB = datetime.now()
        event = ''

        delta = navSys.timerB - navSys.timerA
        seconds = delta.total_seconds()

        if seconds >= 1:
            event = 'space_made'

        if event=='space_made':
            navSys.timerA = datetime.now()
            return adjustingLiftHeightState()
        else:
            return givingLiftSpace()
        

class adjustingLiftHeightState(State):

    def run(self, navSys):
        print('Adjusting lift to item height...')
        event = ''

        if navSys.liftState == 0:
            event = 'lift_aligned'

        if event=='lift_aligned':
            navSys.timerA = datetime.now()
            return approachItemState()
        else:
            return adjustingLiftHeightState()

class approachItemState(State):

    def run(self, navSys):
        navSys.timerB = datetime.now()
        rowNo = navSys.objectiveRow
        shelfNo = navSys.currentObjective['shelf']
        event = ''
        # check to see if an orange item is directly in front of you and close
        # if navSys.dataDict['itemsRB'] != None:
        #     for items in navSys.dataDict['itemsRB']:
        #         if items != None:
        #             for item in items:
        #                 if item != None:
        #                     print("Item Distance:" + str(item))
        #                     if isinstance(item, float):
        #                         if (item <= 0.005):
        #                             event = 'item_close'
        #                     elif item[0] <= 0.005:
        #                         event = 'item_close'

        # drive forward for 3 seconds

        delta = navSys.timerB - navSys.timerA
        seconds = delta.total_seconds()

        if rowNo == 1:
            if shelfNo == 2:
                if seconds >= 2:
                    event = 'item_close'
            elif shelfNo == 3:
                if seconds >= 1.4:
                    event = 'item_close'
        elif rowNo == 2:
            if shelfNo == 4:
                if seconds >= 2:
                    event = 'item_close'
            elif shelfNo == 5:
                if seconds >= 1.4:
                    event = 'item_close'
            

        if event=='item_close':
            navSys.itemState = 'Close'
            return collectItemState()
        else:
            return approachItemState()

class collectItemState(State):

    def run(self, navSys):
        mob.stopAll()
        event = ''
        # itemCollection.close_gripper()
        # navSys.itemState = 'Collected'

        if navSys.itemState == 'Collected':
            event = 'item_collected'

        if event=='item_collected':
            navSys.LEDstate = 'GREEN'
            navSys.timerA = datetime.now()
            return bayReversalState()
        else:
            return collectItemState()

class bayReversalState(State):

    def run(self, navSys):
        event = ''
        navSys.timerB = datetime.now()
        diff = navSys.timerB-navSys.timerA
        if  diff.total_seconds() >= 3:
            event = 'row_centered'

        if event=='row_centered':
            return idleState() # for a 4
        else:
            return bayReversalState()
        
class liftStabilisationState(State):

    def run(self, navSys):
        event = ''

        if  navSys.liftHeight == 1:
            event = 'lift_stable'

        if event=='lift_stable':
            return leavingRowState()
        else:
            return liftStabilisationState()

class leavingRowState(State):

    def run(self, navSys):
        print('Searching for shelves...')
        event = ''
        rowEstimate = navSys.rowEstimation

        # if navSys.objectiveRow == 0:
        #     if navSys.dataDict['packingBayRB']!=None:
        #         event = 'found_pb'
        # else:
        if rowEstimate[0] != None and navSys.dataDict['wallPoints'] != None:
            event = 'row_pose_estimated'
        else:
            event = 'row_pose_not_found'

        #Check transition event
        if event == 'row_pose_estimated':
            return exitingRowState()
        # elif event == 'found_pb':
        #     return movingForPBState()
        else:
            return leavingRowState()

class exitingRowState(State):

    def run(self, navSys):
        print('Driving out of row...')
        event = ''
        rowEstimate = navSys.rowEstimation

        if rowEstimate[0] == None:
            event = 'out_of_row'
        else:
            event = 'in_row'

        #Check transition event
        if event == 'out_of_row':
            return exploringForPBState()
        else:
            return exitingRowState()

class exploringForPBState(State):

    def run(self, navSys):
        print('Adjusting to find PB...')
        event = ''

        if navSys.dataDict['wallPoints']!=None:
            if len(navSys.dataDict['wallPoints'])==2:
                if navSys.dataDict['wallPoints'][0][0]<=0.5:
                    event = 'ready_for_pb'

        #Check transition event
        if event == 'ready_for_pb':
            return scanningForPBState()
        else:
            return exploringForPBState()

class scanningForPBState(State):

    def run(self, navSys):
        print('Scanning for PB...')
        event = ''

        if navSys.dataDict['packingBayRB']!=None:
            event = 'found_pb'

        #Check transition event
        if event == 'found_pb':
            return movingForPBState()
        else:
            return scanningForPBState()

class movingForPBState(State):

    def run(self, navSys):
        print('Moving to PB...')
        event = ''

        if navSys.dataDict['packingBayRB']==None:
            event = 'at_pb'
        elif navSys.dataDict['packingBayRB']!=None:
            if navSys.dataDict['packingBayRB'][0] <= 0.1:
                event = 'at_pb'
        else:
            event = 'lost_pb'

        #Check transition event
        if event == 'at_pb':
            navSys.itemState='Dropping'
            return returnItemState()
        elif event == 'lost_pb':
            return scanningForPBState()
        else:
            return movingForPBState()

class returnItemState(State):

    def run(self, navSys):
        print('Returning item...')
        #print(navSys.itemState)
        event = ''

        if navSys.itemState=='Not_Collected':
            event = 'item_returned'

        #Check transition event
        if event == 'item_returned':
            navSys.LEDstate = 'RED'
            return idleState()
        else:
            return returnItemState()

class idleState(State):

    def run(self, navSys):
        print('Idling...')
        return idleState()
    
class stopState(State):
    
    def run (self, navSys):
        return stopState()

class stateMachine():
    def __init__(self):
        self.state = startState()

    def update_state(self, navSys):
        self.state = self.state.run(navSys)
    
    def get_current_state(self):
        return str(self.state)  # Return the string representation of the current state
