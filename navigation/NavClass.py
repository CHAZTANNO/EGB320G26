from navigation import state_machine as sm
from navigation import velocity_calculator as vc
from tests import milestone_2 as m2
import random
import time
import numpy as np

class NavClass:
    def __init__(self):
        self.forward_vel = 0        # desired forward velocity
        self.rot_vel = 0            # desired rotational velocity
        self.objectives = []
        self.currentObjective = {}
        self.my_sm = sm.stateMachine()
        self.order_data = m2.Milestone2()
        self.v_calc = vc.VelocityCalculator()
        self.objectiveRow = 0
        self.timerA = 0
        self.timerB = 0
        self.LEDstate = 'RED'
        self.itemState = 'Not_Collected'
        self.liftHeight = 0
        self.prev_theta_dot = 0
        self.rotational_gain = 2.0  # Adjust for smoother rotation
        self.alpha = 0.8  # Low-pass filter smoothing factor (0 < alpha < 1)

        # set max values
        self.max_forward_vel = 0.15
        self.max_rot_vel = 3

        self.dataDict = {
            'itemsRB': [],
            'packingBayRB': [],
            'obstaclesRB': [],
            'rowMarkerRB': [],
            'shelvesRB': [],
            'wallPoints': []
        }

        self.gainDict = {
            'itemsRB': [1, 0],
            'packingBayRB': [1, 1],
            'obstaclesRB': [1, 1],
            'rowMarkerRB': [1, 0],
            'shelvesRB': [1, 1],
            'wallPoints': [1, 0]
        }

        self.rowEstimation = [None]

        # bay centers, need to add offeset of camera pos
        self.BAY_DISTANCES = {
            3: 0.1, #0.1315
            2: 0.37, #0.3945
            1: 0.61, #0.6515
            0: 0.85 #0.9085 
        }
    
    def plan_objectives(self):
        # parse order data into a list of dictionaries
        self.objectives.append(self.order_data.get_order())
        self.currentObjective = self.objectives[0]

    def simulator_to_IRL(self, input_list):
        # change simulator output to better match IRL imeplementation
        return [element for element in input_list if element is not None]
    
    def update(self, detected_objects, detected_walls):
        self.dataDict['itemsRB'], self.dataDict['packingBayRB'], self.dataDict['obstaclesRB'], self.dataDict['rowMarkerRB'], self.dataDict['shelvesRB'] = detected_objects
        #self.dataDict['shelvesRB'] = self.simulator_to_IRL(self.dataDict['shelvesRB']) # not needed once intragrated
        self.rowEstimation = self.estimate_row_position(self.dataDict['shelvesRB'])
        self.dataDict['wallPoints'] = detected_walls
        shelfNo = self.currentObjective.get('shelf')
        if shelfNo > 3:
            self.objectiveRow = 2
        elif shelfNo > 1:
            self.objectiveRow = 1
        else:
            self.objectiveRow = 0

        #run state machine update
        self.my_sm.update_state(self)

        # What state are we in?
        state = str(self.my_sm.get_current_state())

        if state == 'startState':
            # # drive towards packing bay
            # attractors = []
            # attractive_f, repulsive_f = self.field_force_calculator(attractors)
        
            # # special force considerations
            # attractive_f.append(self.attraction_calculation(self.dataDict['packingBayRB'], 1))
        
            # # drive towards packingbay
            # vels = self.calculate_resultant_velocity(attractive_f, repulsive_f)
            # self.forward_vel, self.rot_vel = self.normalise_velocity(vels[0], vels[1])

            if self.dataDict['packingBayRB'] != None:
                self.forward_vel, self.rot_vel = self.pf_packing_bay()
            else:
                self.forward_vel = 0
                self.rot_vel = self.max_rot_vel
        
        elif state == 'explorationState':
            self.forward_vel = 0
            self.rot_vel = -self.max_rot_vel*0.8
        
        elif state == 'searchState' or state == 'exitingRowState':
            # what is attractive in this state
            attractors = []
            # calculate forces
            attractive_f, repulsive_f = self.field_force_calculator(attractors)
            attractive_f.append(self.attraction_calculation(self.rowEstimation[0], 1))
            # drive towards desired row estimation using potential fields
            vels = self.calculate_resultant_velocity(attractive_f, repulsive_f)
            self.forward_vel, self.rot_vel = self.normalise_velocity(vels[0], vels[1])
        
        elif state == 'movingDownRowState':
            # self.forward_vel, self.rot_vel = self.potential_fields()
            #attractors = ['rowMarkerRB']
            # calculate forces
            #attractive_f, repulsive_f = self.field_force_calculator(attractors)
            # drive towards desired row marker using potential fields
            # vels = self.calculate_resultant_velocity(attractive_f, repulsive_f)
            #self.forward_vel, self.rot_vel = self.normalise_velocity(vels[0], vels[1])
            self.forward_vel, self.rot_vel = self.potential_fields()

        elif state == 'lostInRowState':
            # spin in a circle
            self.forward_vel = 0
            self.rot_vel = -self.max_rot_vel
        
        elif state == 'movingToBayState':
            # back out of the row
            vels = self.back_out_with_virtual_wall()
            self.forward_vel, self.rot_vel = self.normalise_velocity(vels[0], vels[1])
        
        elif state == 'aligningWithBayState':
            self.forward_vel = 0
            if (self.currentObjective['shelf'] % 2) == 0:
                self.rot_vel = self.max_rot_vel*0.8
            else:
                self.rot_vel = -self.max_rot_vel*0.8
        
        elif state == 'approachItemState':
            self.forward_vel = 0.05
            self.rot_vel = 0
        
        elif state == 'collectItemState':
            self.itemState = 'Collecting'
        
        elif state == 'bayReversalState':
            self.forward_vel = -0.05
            self.rot_vel = 0

        elif state == 'leavingRowState':
            self.forward_vel = 0
            if (self.currentObjective['shelf'] % 2) == 0:
                self.rot_vel = self.max_rot_vel
            else:
                self.rot_vel = -self.max_rot_vel
        
        elif state == 'exploringForPBState':
            self.forward_vel, self.rot_vel = self.potential_field_to_point((0.1, 0))
        
        elif state == 'scanningForPBState':
            # spin in a circle
            self.forward_vel = 0
            self.rot_vel = -self.max_rot_vel
        
        elif state == 'movingForPBState':
            self.forward_vel, self.rot_vel = self.pf_packing_bay()
            # if self.dataDict['packingBayRB']==None:
            #     if self.dataDict['wallPoints']!=None:
            #         if len(self.dataDict['wallPoints'])>1:
            #             print(self.dataDict['wallPoints'])
            #             self.forward_vel, self.rot_vel = self.potential_field_to_point(tuple(self.dataDict['wallPoints'][1]))
        
        elif state == 'returnItemState':
            self.forward_vel=0
            self.rot_vel=0

        elif state == 'adjustingLiftHeightState' or state == 'liftStabilisationState':
            self.forward_vel=0
            self.rot_vel=0
        
        elif state == 'idleState':
            # stop
            pass
        
        else:
            pass

    def normalise_velocity(self, forward_vel, rot_vel):
        """
        Normalizes forward and rotational velocities while considering their signs and keeping them proportional.
        
        :param forward_vel: The forward velocity to normalize.
        :param rot_vel: The rotational velocity to normalize.
        :param max_forward_vel: The maximum forward velocity (can be positive or negative).
        :param max_rot_vel: The maximum rotational velocity (can be positive or negative).
        :return: Proportionally normalized forward and rotational velocities with their signs preserved.
        """
        # Ensure max values are positive (since they define the upper limit)
        max_forward_vel = abs(self.max_forward_vel)
        max_rot_vel = abs(self.max_rot_vel)
        
        # Calculate scaling factors based on the absolute values of velocities
        forward_factor = min(1, max_forward_vel / abs(forward_vel)) if forward_vel != 0 else 1
        rot_factor = min(1, max_rot_vel / abs(rot_vel)) if rot_vel != 0 else 1

        # Use the smaller factor to scale both velocities proportionally
        scaling_factor = min(forward_factor, rot_factor)

        # Apply scaling factor and retain the original sign of the velocities
        forward_vel *= scaling_factor
        rot_vel *= scaling_factor

        return forward_vel, rot_vel

    def calculate_midpoint(self, shelves_rb):
        """
        Calculate the estimated midpoint between two shelves given their range and bearing data.

        :param shelves_rb: A list of two [range, bearing] pairs, each representing a shelf's position.
        :return: A new [range, bearing] pair representing the midpoint between the two shelves.
        """
        if shelves_rb[0]==None or shelves_rb[1]==None:
            return None # can't find midpoint
        else:
            # Extract range and bearing for each shelf
            shelf0_range, shelf0_bearing = shelves_rb[0]
            shelf1_range, shelf1_bearing = shelves_rb[1]

            # Convert polar coordinates (range, bearing) to Cartesian coordinates (x, y)
            shelf0_x = shelf0_range * np.cos(shelf0_bearing)
            shelf0_y = shelf0_range * np.sin(shelf0_bearing)
            
            shelf1_x = shelf1_range * np.cos(shelf1_bearing)
            shelf1_y = shelf1_range * np.sin(shelf1_bearing)

            # Calculate the midpoint in Cartesian coordinates
            midpoint_x = (shelf0_x + shelf1_x) / 2
            midpoint_y = (shelf0_y + shelf1_y) / 2

            # Convert the midpoint back to polar coordinates (range, bearing)
            midpoint_range = np.sqrt(midpoint_x**2 + midpoint_y**2)
            midpoint_bearing = np.arctan2(midpoint_y, midpoint_x)

            return [midpoint_range, midpoint_bearing]


    def estimate_row_position(self, shelfRBData):
        # data will be variable legnth in the form [left_most_visable_shelf... right_most_visable_shelf]
        # Return the row estimation RB
        if shelfRBData==None:
            return [None]
        elif len(shelfRBData)<2:
            return [None]
        else:
            # we have enough data, use the right most pair
            return [shelfRBData[-2], shelfRBData[-1]]
    
    def estimate_flank_shelves(self, shelfRBData):
        pass
    
    def field_force_calculator(self, attractors):
        attractive_force_pairs = []
        for attractor in attractors:
            # check if the data is a List
            if isinstance(self.dataDict[attractor], list):
                # for each item in the list create a force calculation and append it to the attractive forces list
                for RB in self.dataDict[attractor]:
                    if RB != None:
                        attractive_force_pairs.append(self.attraction_calculation(RB, self.gainDict[attractor][0]))
        
        repulsive_force_pairs = []
        for rbData in self.dataDict:
            if rbData not in attractors and rbData != 'itemsRB' and rbData != 'packingBayRB':
                if self.dataDict[rbData]:
                    for RB in self.dataDict[rbData]:
                        if RB != None:
                            force_x, force_y = self.repulsion_calculation(RB, self.gainDict[rbData][1], 10)
                            repulsive_force_pairs.append((force_x, force_y))
        
        return attractive_force_pairs, repulsive_force_pairs


    def attraction_calculation(self, range_bearing, gain):
        """
        Attractive potential field calculation.
        
        :param range_bearing: A tuple (distance, bearing) to the goal.
        :param gain: Gain that controls the strength of attraction.
        :return: Tuple (force_x, force_y) representing the attractive force in x and y components.
        """
        distance, bearing = range_bearing
        # Attractive potential field using quadratic function
        force_magnitude = gain * (distance ** 2)  # Quadratic attractive potential
        force_x = force_magnitude * np.cos(bearing)
        force_y = force_magnitude * np.sin(bearing)
        
        return (force_x, force_y)


    def repulsion_calculation(self, range_bearing, gain, Q_star=1.0):
        """
        Repulsive potential field calculation.
        
        :param range_bearing: A tuple (distance, bearing) to the obstacle.
        :param gain: Gain that controls the strength of repulsion.
        :param Q_star: The distance at which repulsion starts to take effect (influence range).
        :return: Tuple (force_x, force_y) representing the repulsive force in x and y components.
        """
        distance, bearing = range_bearing
        
        if distance > Q_star:
            return 0, 0  # No repulsive force outside the influence range
        
        force_magnitude = gain * (1/distance - 1/Q_star) ** 2
        force_x = -force_magnitude * np.cos(bearing)  # Repulsive force is in the opposite direction
        force_y = -force_magnitude * np.sin(bearing)
        
        return (force_x, force_y)


    def calculate_resultant_velocity(self, attractive_forces, repulsive_forces):
        return self.v_calc.calculate_smooth_velocity(attractive_forces, repulsive_forces)
    
    def potential_field_to_point(self, target_rb):
        # Define parameters for the potential fields
        attractive_gain = 10  # Gain for the attractive force (towards target point)
        repulsive_gain = 1    # Gain for the repulsive force (away from obstacles, shelves, and walls)
        safe_distance = 0.15  # Distance at which repulsive force starts to take effect
        obstacle_gain = 2     # Specific gain for obstacles
        shelf_gain = 1        # Specific gain for shelves
        wall_gain = 5         # Specific gain for walls

        # Initialize the resultant force (x, y) components
        force_x = 0.0
        force_y = 0.0

        obstaclesRB = self.dataDict['obstaclesRB']
        shelvesRB = self.dataDict['shelvesRB']
        wallsRB = self.dataDict['wallPoints']

        # Calculate attractive force towards the target point (if detected)
        if target_rb is not None:
            target_range, target_bearing = target_rb
            force_x += attractive_gain * (1.0 / target_range) * np.cos(target_bearing)
            force_y += attractive_gain * (1.0 / target_range) * np.sin(target_bearing)

        # Calculate repulsive forces from obstacles
        if obstaclesRB is not None:
            for obstacle in obstaclesRB:
                if obstacle is not None:
                    obstacle_range = obstacle[0]
                    obstacle_bearing = obstacle[1]
                    if obstacle_range < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / obstacle_range - 1.0 / safe_distance) / (obstacle_range ** 2)
                        force_x -= repulsive_force * np.cos(obstacle_bearing) * obstacle_gain
                        force_y -= repulsive_force * np.sin(obstacle_bearing) * obstacle_gain

        # Calculate repulsive forces from shelves
        if shelvesRB is not None:
            for shelf in shelvesRB:
                if shelf is not None:
                    shelf_range = shelf[0]
                    shelf_bearing = shelf[1]
                    if shelf_range < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / shelf_range - 1.0 / safe_distance) / (shelf_range ** 2)
                        force_x -= repulsive_force * np.cos(shelf_bearing) * shelf_gain
                        force_y -= repulsive_force * np.sin(shelf_bearing) * shelf_gain

        # Calculate repulsive forces from walls
        if wallsRB is not None:
            for wall in wallsRB:
                if wall is not None:
                    wall_range = wall[0]
                    wall_bearing = wall[1]
                    if wall_range < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / wall_range - 1.0 / safe_distance) / (wall_range ** 2)
                        force_x -= repulsive_force * np.cos(wall_bearing) * wall_gain
                        force_y -= repulsive_force * np.sin(wall_bearing) * wall_gain

        # Calculate the resultant velocity commands
        x_dot = force_x  # Linear speed in x direction
        theta_dot = np.arctan2(force_y, force_x)  # Rotational speed (direction of the resultant force)

        # Normalize and scale the velocities to ensure they are within the robot's limits
        max_linear_speed = 0.1  # Example max speed (adjust based on your robot)
        max_rotation_speed = 0.5  # Example max rotational speed (adjust based on your robot)

        # Normalize the linear velocity
        speed = np.hypot(force_x, force_y)
        if speed > max_linear_speed:
            x_dot = max_linear_speed * (force_x / speed)

        # Ensure theta_dot is within the allowed range
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed

        # Set the target velocities to the robot
        return x_dot, theta_dot

    def potential_fields(self):
        # Define parameters for the potential fields
        attractive_gain = 3  # Gain for the attractive force (towards row markers)
        repulsive_gain = 0   # Gain for the repulsive force (away from obstacles, shelves, and walls)
        safe_distance = 0.3    # Distance at which repulsive force starts to take effect
        random_explore_gain = 0  # Gain for the random exploration force
        left_bias = 0

        # specific object params
        obstacle_gain = 0
        shelf_gain = 1
        wall_gain = 0
        packingStation_gain = 0

        # Initialize the resultant force (x, y) components
        force_x = 0.0
        force_y = 0.0

        rowMarkerRB = self.dataDict['rowMarkerRB']
        obstaclesRB = self.dataDict['obstaclesRB']
        shelvesRB = self.dataDict['shelvesRB']
        wallsRB = self.dataDict['wallPoints']
        packingBayRB = self.dataDict['packingBayRB']

        # Calculate attractive force towards the row markers (if detected)
        if rowMarkerRB is not None:
            for rowMarker in rowMarkerRB:
                if rowMarker is not None:
                    rowMarkerRange = rowMarker[0]
                    rowMarkerBearing = -rowMarker[1]
                    force_x += attractive_gain * (1.0 / rowMarkerRange) * np.cos(rowMarkerBearing)
                    force_y += attractive_gain * (1.0 / rowMarkerRange) * np.sin(rowMarkerBearing)
                else:
                    # Add a random exploration force if no row markers are detected
                    random_force_x = random.uniform(0, 0.5)
                    random_force_y = random.uniform(-2, 2)
                    force_x += random_explore_gain * random_force_x
                    force_y += random_explore_gain * random_force_y

        # Calculate repulsive forces from obstacles
        if obstaclesRB is not None:
            for obstacle in obstaclesRB:
                if obstacle is not None:
                    obstacleRange = obstacle[0]
                    obstacleBearing = obstacle[1]
                    if obstacleRange < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / obstacleRange - 1.0 / safe_distance) / (obstacleRange ** 2)
                        force_x -= repulsive_force * np.cos(obstacleBearing) * obstacle_gain
                        force_y -= repulsive_force * np.sin(obstacleBearing) * obstacle_gain

        # Calculate repulsive forces from shelves
        if shelvesRB is not None:
            for shelf in shelvesRB:
                if shelf is not None:
                    shelfRange = shelf[0]
                    shelfBearing = shelf[1]
                    if shelfRange < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / shelfRange - 1.0 / safe_distance) / (shelfRange ** 2)
                        force_x -= repulsive_force * np.cos(shelfBearing) * shelf_gain
                        force_y -= repulsive_force * np.sin(shelfBearing) * shelf_gain

        # Calculate repulsive forces from walls
        if wallsRB is not None:
            for wall in wallsRB:
                if wall is not None:
                    wallRange = wall[0]
                    wallBearing = wall[1]
                    if wallRange < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / wallRange - 1.0 / safe_distance) / (wallRange ** 2)
                        force_x -= repulsive_force * np.cos(wallBearing) * wall_gain
                        force_y -= repulsive_force * np.sin(wallBearing) * wall_gain
        
        # Calculate repulsive forces from packing bay
        if packingBayRB is not None:
            packingBayRange = packingBayRB[0]
            packingBayBearing = packingBayRB[1]
            if packingBayRange < safe_distance:
                repulsive_force = repulsive_gain * (1.0 / packingBayRange - 1.0 / safe_distance) / (packingBayRange ** 2)
                force_x -= repulsive_force * np.cos(packingBayBearing) * packingStation_gain
                force_y -= repulsive_force * np.sin(packingBayBearing) * packingStation_gain

        # Calculate the resultant velocity commands
        x_dot = force_x  # Linear speed in x direction
        theta = np.arctan2(force_y, force_x)  # Rotational speed (direction of the resultant force)

        # Normalize and scale the velocities to ensure they are within the robot's limits
        max_linear_speed = self.max_forward_vel  # Example max speed (adjust based on your robot)
        max_rotation_speed = self.max_rot_vel  # Example max rotational speed (adjust based on your robot)

        # Adjust gain factor to determine the responsiveness of the rotation
        rotational_gain = 1.0  # You can tune this value

        # Calculate rotational velocity proportional to the force angle
        theta_dot = self.calculate_smooth_rotational_velocity(theta, x_dot)

        # Clamp the rotational velocity to the maximum allowed value
        max_rotation_speed = self.max_rot_vel
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed
        
        # Normalize the linear velocity
        speed = np.hypot(force_x, force_y)
        if speed > max_linear_speed:
            x_dot = max_linear_speed * (force_x / speed)

        # Ensure theta_dot is within the allowed range
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed

        theta_dot+=left_bias

        # Set the target velocities to the robot
        return x_dot, theta_dot

    def pf_packing_bay(self):
        # Define parameters for the potential fields
        attractive_gain = 1  # Gain for the attractive force (towards the packing bay)
        repulsive_gain = 0   # Gain for the repulsive force (away from obstacles, walls, and shelves)
        safe_distance = 0.15    # Distance at which repulsive force starts to take effect
        obstacle_gain = 0     # Specific gain for obstacles
        wall_gain = 1           # Specific gain for walls
        shelf_gain = 1          # Specific gain for shelves
        packingStation_gain = 1  # Specific gain for packing station
        right_bias = -0.3

        # Initialize the resultant force (x, y) components
        force_x = 0.0
        force_y = 0.0

        packingBayRB = self.dataDict['packingBayRB']
        obstaclesRB = self.dataDict['obstaclesRB']
        wallsRB = self.dataDict['wallPoints']
        shelvesRB = self.dataDict['shelvesRB']

        # Calculate attractive force towards the packing bay (if detected)
        if packingBayRB is not None:
            packingBayRange = packingBayRB[0]
            packingBayBearing = packingBayRB[1]
            force_x += attractive_gain * (1.0 / packingBayRange) * np.cos(packingBayBearing)
            force_y += attractive_gain * (1.0 / packingBayRange) * np.sin(packingBayBearing)

        # Calculate repulsive forces from walls
        if wallsRB is not None:
            for wall in wallsRB:
                if wall is not None:
                    wallRange = wall[0]
                    wallBearing = wall[1]
                    if wallRange < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / wallRange - 1.0 / safe_distance) / (wallRange ** 2)
                        force_x -= repulsive_force * np.cos(wallBearing) * wall_gain
                        force_y -= repulsive_force * np.sin(wallBearing) * wall_gain

        # Calculate repulsive forces from shelves
        if shelvesRB is not None:
            for shelf in shelvesRB:
                if shelf is not None:
                    shelfRange = shelf[0]
                    shelfBearing = shelf[1]
                    if shelfRange < safe_distance:
                        repulsive_force = repulsive_gain * (1.0 / shelfRange - 1.0 / safe_distance) / (shelfRange ** 2)
                        force_x -= repulsive_force * np.cos(shelfBearing) * shelf_gain
                        force_y -= repulsive_force * np.sin(shelfBearing) * shelf_gain

        # Calculate the resultant velocity commands
        x_dot = force_x  # Linear speed in x direction
        theta = np.arctan2(force_y, force_x)  # Rotational speed (direction of the resultant force)

        # Normalize and scale the velocities to ensure they are within the robot's limits
        max_linear_speed = self.max_forward_vel  # Example max speed (adjust based on your robot)
        max_rotation_speed = self.max_rot_vel  # Example max rotational speed (adjust based on your robot)

        # Adjust gain factor to determine the responsiveness of the rotation
        rotational_gain = 1.0  # You can tune this value

        # Calculate rotational velocity proportional to the force angle
        theta_dot = rotational_gain * theta * abs(x_dot) + right_bias

        # Clamp the rotational velocity to the maximum allowed value
        max_rotation_speed = self.max_rot_vel
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed

        # Normalize the linear velocity
        speed = np.hypot(force_x, force_y)
        if speed > max_linear_speed:
            x_dot = max_linear_speed * (force_x / speed)

        # Set the target velocities to the robot
        return x_dot, theta_dot

    
    def back_out_of_row(self):
        # Base gain parameters
        row_marker_gain = 1  # Base gain for keeping the row marker centered
        shelf_evasion_base_gain = 10  # Base gain for evading shelves
        forward_gain = -0.1  # Gain for moving backward
        max_rotation_speed = 0.6  # Maximum rotational velocity

        # Get the row marker range-bearing data
        if self.dataDict['rowMarkerRB'][self.objectiveRow] is not None:
            row_marker_rb = self.dataDict['rowMarkerRB'][self.objectiveRow]
        else:
            row_marker_rb = None
        shelvesRB = self.dataDict['shelvesRB']
        if shelvesRB is not None:
            rowNo = self.objectiveRow
            if rowNo == 0:
                left_shelf = shelvesRB[0]  # Shelf 0 is left
                right_shelf = shelvesRB[1]  # Shelf 1 is right
            elif rowNo == 1:
                left_shelf = shelvesRB[2]  # Shelf 2 is left
                right_shelf = shelvesRB[3]  # Shelf 3 is right
            elif rowNo == 2:
                left_shelf = shelvesRB[4]  # Shelf 4 is left
                right_shelf = shelvesRB[5]  # Shelf 5 is right
            else:
                raise ValueError("Invalid row number. Row number must be 0, 1, or 2.")

        force_x = 0.0
        force_y = 0.0

        if row_marker_rb is None or len(row_marker_rb) == 0:
            return 0, 0  # No row marker detected, stop

        row_marker_range = row_marker_rb[0]
        row_marker_bearing = row_marker_rb[1]

        # Step 1: Keep the row marker centered
        force_x += row_marker_gain * np.cos(row_marker_bearing)
        force_y += row_marker_gain * np.sin(row_marker_bearing)

        # Step 2: Adjust the shelf evasion gain dynamically based on the distance to the row marker
        # The further the row marker, the stricter the robot is about avoiding shelves
        dynamic_shelf_evasion_gain = shelf_evasion_base_gain * (1 + row_marker_range)

        # Step 3: Evade the shelves if they become visible
        if left_shelf is not None:
            # If the left shelf is visible (bearing close to 0), push it out to the left
            shelf_range, shelf_bearing = left_shelf
            force_x += dynamic_shelf_evasion_gain * np.cos(shelf_bearing + np.pi / 2)  # Move away from the left shelf
            force_y += dynamic_shelf_evasion_gain * np.sin(shelf_bearing + np.pi / 2)

        if right_shelf is not None:
            # If the right shelf is visible (bearing close to 0), push it out to the right
            shelf_range, shelf_bearing = right_shelf
            force_x += dynamic_shelf_evasion_gain * np.cos(shelf_bearing - np.pi / 2)  # Move away from the right shelf
            force_y += dynamic_shelf_evasion_gain * np.sin(shelf_bearing - np.pi / 2)

        # Step 4: Calculate the resultant velocities
        x_dot = forward_gain  # Constant backward velocity
        theta_dot = np.arctan2(force_y, force_x)  # Adjust rotational velocity based on combined forces

        # Normalize the rotational velocity
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed

        return x_dot, theta_dot

    def build_virtual_wall(self):
        """
        Builds a virtual wall based on the available data (wall points or row marker).
        Returns the midpoint of the virtual wall, and the angle relative to the robot.
        """
        # Get wall points and row marker data
        wall_points = self.dataDict['wallPoints']
        row_marker_rb = self.dataDict['rowMarkerRB']
        
        # If we have two wall points, build the virtual wall using them
        if wall_points is not None and len(wall_points) == 2:
            wall_point1 = wall_points[0]
            wall_point2 = wall_points[1]

            if wall_point1 is not None and wall_point2 is not None:
                # Calculate the midpoint and orientation of the virtual wall
                virtual_wall_midpoint = self.calculate_midpoint([wall_point1, wall_point2])
                wall_bearing = virtual_wall_midpoint[1]  # Angle of the wall relative to the robot

                return virtual_wall_midpoint, wall_bearing
        
        # If no wall points are available, fallback to using the row marker
        if row_marker_rb is not None and len(row_marker_rb) > 0:
            row_marker = row_marker_rb[self.objectiveRow]
            row_marker_bearing = row_marker[1]

            # Assume the wall is perpendicular to the row marker
            virtual_wall_bearing = row_marker_bearing + np.pi / 2  # Wall is perpendicular to row marker

            return row_marker, virtual_wall_bearing

        return None, None  # No wall or row marker data available


    def back_out_with_virtual_wall(self):
        # Gain parameters
        alignment_gain = 5  # Gain for aligning the robot's bearing with the virtual wall
        forward_gain = -0.1  # Gain for moving backward
        max_rotation_speed = 0.1  # Maximum rotational velocity

        # Build the virtual wall
        virtual_wall_midpoint, virtual_wall_bearing = self.build_virtual_wall()

        if virtual_wall_midpoint is None or virtual_wall_bearing is None:
            return 0, 0  # No virtual wall or row marker detected, stop

        # Step 1: Keep the robot aligned with the virtual wall
        theta_dot = alignment_gain * (-virtual_wall_bearing)  # Correct any deviation from the virtual wall

        # Step 2: Move backward in a straight line
        x_dot = forward_gain  # Constant backward velocity

        # Normalize rotational velocity
        if abs(theta_dot) > max_rotation_speed:
            theta_dot = np.sign(theta_dot) * max_rotation_speed

        return x_dot, theta_dot

    def calculate_smooth_rotational_velocity(self, force_angle, x_dot):
        # Calculate raw rotational velocity proportional to the force angle
        theta_dot = self.rotational_gain * force_angle * abs(x_dot)

        # Clamp rotational velocity to max limits
        theta_dot = np.clip(theta_dot, -self.max_rot_vel, self.max_rot_vel)

        # Apply low-pass filter to smooth the rotational velocity
        smoothed_theta_dot = (1 - self.alpha) * self.prev_theta_dot + self.alpha * theta_dot

        # Update previous theta_dot for the next iteration
        self.prev_theta_dot = smoothed_theta_dot

        return smoothed_theta_dot

