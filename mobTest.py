from mobility import mobility as mob
import time

mob.SetTargetVelocities(0.1, 0)
time.sleep(1)
mob.stopAll()