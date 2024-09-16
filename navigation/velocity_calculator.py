import numpy as np

class VelocityCalculator:
    def __init__(self, alpha=0.8, max_accel=0.1):
        self.alpha = alpha  # Low-pass filter factor (smoothing)
        self.max_accel = max_accel  # Maximum allowed acceleration per timestep
        self.prev_forward_velocity = 0
        self.prev_rotational_velocity = 0

    def calculate_smooth_velocity(self, attractive_forces, repulsive_forces):
        """
        Calculate the robot's smooth forward and rotational velocities based on the
        sum of attractive and repulsive forces, with smoothing.

        :param attractive_forces: List of (force_x, force_y) tuples from attraction calculations.
        :param repulsive_forces: List of (force_x, force_y) tuples from repulsion calculations.
        :return: Tuple (forward_velocity, rotational_velocity).
        """
        # Sum all attractive and repulsive forces
        total_force_x = sum(f[0] for f in attractive_forces) + sum(f[0] for f in repulsive_forces)
        total_force_y = sum(f[1] for f in attractive_forces) + sum(f[1] for f in repulsive_forces)

        # Calculate target velocities based on forces
        target_forward_velocity = np.sqrt(total_force_x**2 + total_force_y**2)
        target_rotational_velocity = np.arctan2(total_force_y, total_force_x)

        # Apply a low-pass filter to smooth the velocity transitions
        forward_velocity = (1 - self.alpha) * self.prev_forward_velocity + self.alpha * target_forward_velocity
        rotational_velocity = (1 - self.alpha) * self.prev_rotational_velocity + self.alpha * target_rotational_velocity

        # Limit the acceleration to make transitions smoother
        forward_velocity = self.limit_acceleration(self.prev_forward_velocity, forward_velocity)
        rotational_velocity = self.limit_acceleration(self.prev_rotational_velocity, rotational_velocity)

        # Update the previous velocities for the next iteration
        self.prev_forward_velocity = forward_velocity
        self.prev_rotational_velocity = rotational_velocity

        return forward_velocity, rotational_velocity

    def limit_acceleration(self, previous_velocity, target_velocity):
        """
        Limit the change in velocity to ensure smoother acceleration/deceleration.

        :param previous_velocity: The velocity from the previous timestep.
        :param target_velocity: The target velocity to move toward.
        :return: The new velocity limited by max acceleration.
        """
        delta_velocity = target_velocity - previous_velocity
        if abs(delta_velocity) > self.max_accel:
            # Limit the velocity change to the maximum allowed acceleration
            delta_velocity = np.sign(delta_velocity) * self.max_accel
        return previous_velocity + delta_velocity
