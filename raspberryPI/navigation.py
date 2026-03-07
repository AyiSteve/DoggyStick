from api.mapapi import MapNavigator
from cameraNobjectdec import capture_detection
# States:
# FOLLOW_ROUTE, DESTINATION_REACHED, OFF_ROUTE, WRONG_DIRECTION

class Navigation:
    def __init__(self, map_nav: MapNavigator, mode="walk"):
        self.mode = mode
        self.map = map_nav

        self.path = None
        self.target = None
        self.index = 0

        self.state = "FOLLOW_ROUTE"
        self.heading = None

        self.turn_angle = 0.0
        self.offroute_counter = 0
        self.wrong_dir_counter = 0
        self.dist_to_target = 0

        self.prevGPS = None
        self.heading = None


    def updatePath(self):
        self.map.updateDirection()
        self.index = 0
        self.target = None
        self.state =  "FOLLOW_ROUTE"
        self.path = self.map.WalkPath
        self.wrong_dir_counter = 0
        self.offroute_counter = 0
        self.dist_to_target = 0
        self.heading = None

    # --------------------------------------------------
    # Target update
    # --------------------------------------------------
    def updateTarget(self):
        if not self.path or len(self.path) == 0:
            raise RuntimeError("Navigation path not initialized")

        self.target = self.path[self.index]

    def obstacleAvoidance(self, front, left, right):

        STOP_THRESHOLD = 20
        SAFE_FRONT = 40

        # Emergency: too close
        if front < STOP_THRESHOLD:

            # Choose turn direction
            if left > right:
                return "RECOVER_LEFT", -40
            else:
                return "RECOVER_RIGHT", 40

        # Normal avoidance
        side_bias = (left - right)
        angle = max(min(side_bias * 0.5, 45), -45)

        if front < SAFE_FRONT:
            return "AVOID", angle

        return "CLEAR", 0

    def detectLight(self):
        result = capture_detection()
        label = result["label"]
        if label == "":
            return True
        return False
    # --------------------------------------------------
    # Wrong direction detection
    # --------------------------------------------------
    def checkDirection(self, gps):

        if gps is None or self.heading is None or self.target is None:
            return False

        # Desired direction toward target
        desired = self.map.bearing(gps, self.target)

        # Signed turn angle (-180 to 180)
        turn = (desired - self.heading + 540) % 360 - 180
        self.turn_angle = turn
        error = abs(turn)

        # Dynamic threshold (walking vs standing)
        threshold = 40

        if error > threshold:
            self.wrong_dir_counter += 1
        else:
            self.wrong_dir_counter = 0

        return self.wrong_dir_counter >= 2

        # --------------------------------------------------
        # Off-route detection (windowed)
        # --------------------------------------------------
    def offRoute(self, gps, max_dist=30.0):

        if not self.path or self.target is None:
            return False

        # Distance to current target
        dist = self.map.distance(gps, self.target)

        if (self.index > 0):
            max_dist += self.map.distance(self.target, self.path[self.index-1])

        return dist > max_dist

    def targetReached(self, reach_dist=7.0):
        if self.target is None:
            return False

        if self.dist_to_target < reach_dist:
            if self.index < len(self.path) - 1:
                self.state = "TARGET_REACHED"
                self.index+=1
                return True
            else:
                self.state = "DESTINATION_REACHED"
        return False

    # --------------------------------------------------
    # MAIN NAVIGATION LOOP
    # --------------------------------------------------
    def navigate(self):
        if self.prevGPS is None or not self.path or self.map.currentLocation is None:
            return self.state

        if self.detectLight():
            return "EMStop"
        

        status, angle = self.obstacleAvoidance(front, left, right)

        if status == "RECOVER_LEFT":
            self.state = "RECOVER"
            self.turn_angle = angle
            return "MOVE_BACK_AND_TURN"

        if status == "RECOVER_RIGHT":
            self.state = "RECOVER"
            self.turn_angle = angle
            return "MOVE_BACK_AND_TURN"
        
        if status == "AVOID":
            self.turn_angle += angle
            return "AVOID"
        
        self.updateTarget()

        # check reached using CURRENT gps + CURRENT target
        if self.targetReached():
            return self.state

        if self.state in ("DESTINATION_REACHED"):
            return self.state

        if self.offRoute(self.map.currentLocation):
            self.state = "OFF_ROUTE"
            return self.state

        if self.checkDirection(self.map.currentLocation):
            self.state = "WRONG_DIRECTION"
        else:
            self.turn_angle = 0.0
            self.state = "FOLLOW_ROUTE"

        return self.state