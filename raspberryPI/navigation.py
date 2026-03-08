from api.mapapi import MapNavigator
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

        if front < STOP_THRESHOLD:
            if left > right:
                return "RECOVER_LEFT", -60
            else:
                return "RECOVER_RIGHT", 60

        side_bias = left - right
        angle = max(min(side_bias * 1.0, 45), -45)

        if front < SAFE_FRONT:
            return "AVOID", angle

        return "CLEAR", 0

    # --------------------------------------------------
    # Wrong direction detection
    # --------------------------------------------------
    def checkDirection(self, gps, front, left, right):

        if gps is None or self.heading is None or self.target is None:
            return False

        # -----------------------------
        # ROUTE FOLLOWING ANGLE
        # -----------------------------
        desired = self.map.bearing(gps, self.target)

        nav_angle = (desired - self.heading + 540) % 360 - 180


        # -----------------------------
        # OBSTACLE AVOIDANCE
        # -----------------------------
        STOP_THRESHOLD = 20
        SAFE_FRONT = 40

        if front < STOP_THRESHOLD:
            if left > right:
                self.turn_angle = -60
            else:
                self.turn_angle = 60
            return True   # treat as wrong direction → recovery

        avoid_angle = 0

        if front < SAFE_FRONT:
            side_bias = right - left
            avoid_angle = max(min(side_bias * 0.8, 45), -45)


        # -----------------------------
        # COMBINE ROUTE + AVOIDANCE
        # -----------------------------
        final_angle = nav_angle + 0.6 * avoid_angle

        final_angle = max(min(final_angle, 90), -90)

        self.turn_angle = final_angle


        # -----------------------------
        # WRONG DIRECTION CHECK
        # -----------------------------
        error = abs(nav_angle)
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
                self.index+=1
                return True
            else:
                self.state = "DESTINATION_REACHED"
        return False

    # --------------------------------------------------
    # MAIN NAVIGATION LOOP
    # --------------------------------------------------
    def navigate(self, front, left, right, lightStatus):

        # Basic validity check
        if self.prevGPS is None or not self.path or self.map.currentLocation is None:
            return self.state

        # Emergency stop (traffic light)
        if lightStatus:
            self.state = "EMStop"
            return self.state

        # Update next waypoint
        self.updateTarget()

        # Update distance to target
        self.dist_to_target = self.map.distance(self.map.currentLocation, self.target)

        # Check if waypoint reached
        if self.targetReached():
            return self.state

        if self.state == "DESTINATION_REACHED":
            return self.state

        # Off route detection
        if self.offRoute(self.map.currentLocation):
            self.state = "OFF_ROUTE"
            return self.state

        # Compute steering + wrong direction detection
        wrong = self.checkDirection(
            self.map.currentLocation,
            front,
            left,
            right
        )

        if wrong:
            self.state = "WRONG_DIRECTION"
        else:
            self.state = "FOLLOW_ROUTE"

        return self.state