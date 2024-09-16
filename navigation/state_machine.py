import time
import random
from navigation import NavClass as nav
from datetime import datetime

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
            if navSys.dataDict['packingBayRB'] != None and (navSys.dataDict['packingBayRB'][0] < 1.9):
                event = 'finished_calibration'
        elif rowNo == 1:
            if navSys.dataDict['packingBayRB'] != None and (navSys.dataDict['packingBayRB'][0] < 0.9):
                event = 'finished_calibration'
        else:
            if navSys.dataDict['packingBayRB'] == None:
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

        if rowEstimate[0] != None and rowEstimate[0][0]<0.4:
            # row estimation identified
            event = 'row_pose_estimated'
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
        if navSys.dataDict['rowMarkerRB'][rowNo] == None and len(navSys.dataDict['wallPoints'])==2:
            event = 'reached_row_end'
        elif navSys.dataDict['rowMarkerRB'][rowNo] == None and len(navSys.dataDict['wallPoints'])!=2:
            event = 'lost_row_end'
        else:
            event = 'end_not_reached'
        
        #Check transition event
        if event == 'reached_row_end':
            if navSys.currentObjective['bay']==3:
                return aligningWithBayState()
            else:
                return movingToBayState()
        elif event == 'lost_row_end':
            return lostInRowState()
        else:
            return movingDownRowState()

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
        # if navSys.dataDict['itemsRB'] != None:
        #     for items in navSys.dataDict['itemsRB']:
        #         if items != None:
        #             for item in items:
        #                 if item != None:
        #                     print(item)
        #                     if item[0] < 0.25:
        #                         if (item[1] <= 0.25 and item[1] >= -0.25):
        #                             print(str(item[1]))
        #                             event = 'facing_bay'

        # check to see if enough time has passed at a given velocity to turn 90 degrees
        turn_time = 3
        time_delta = navSys.timerB - navSys.timerA
        if time_delta.seconds >= turn_time:
            event = 'facing_bay'

        if event=='facing_bay':
            navSys.LEDstate = 'YELLOW'
            return collectItemState()
        else:
            return aligningWithBayState()

class collectItemState(State):

    def run(self, navSys):
        if navSys.itemState == 'Collected':
            event = 'item_collected'

        if event=='item_collected':
            navSys.LEDstate = 'GREEN'
            return idleState()
        else:
            return aligningWithBayState()

class idleState(State):

    def run(self, navSys):
        print('Idling...')
        return idleState()

class stateMachine():
    def __init__(self):
        self.state = startState()

    def update_state(self, navSys):
        self.state = self.state.run(navSys)
    
    def get_current_state(self):
        return str(self.state)  # Return the string representation of the current state
