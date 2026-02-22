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
    def updatePath(self):
        self.map.updateDirection()
        self.index = 0
        self.target = None
        self.path = self.map.WalkPath
        self.wrong_dir_counter = 0
        self.offroute_counter = 0

    # --------------------------------------------------
    # Target update
    # --------------------------------------------------
    def updateTarget(self):
        if not self.path or len(self.path) == 0:
            raise RuntimeError("Navigation path not initialized")

        start = self.index
        nearest_index = min(
            range(start, len(self.path)),
            key=lambda i: self.map.distance(self.map.currentLocation, self.path[i])
        )
        self.index = nearest_index
        self.target = self.path[self.index]
        print(self.index)

    # --------------------------------------------------
    # Wrong direction detection
    # --------------------------------------------------
    def checkDirection(self, gps, speed_mps):

        if gps is None:
            return False

        move_dist = self.map.distance(self.prevGPS, gps)

        # Must move at least 2 meters
        if move_dist < 1.0:
            return False

        # Signed turn angle (-180 to 180)
        turn = self.map.filtered_gps(self.target)
        error = abs(turn)

        threshold = 35 if speed_mps < 1.2 else 30

        if error > threshold:
            self.wrong_dir_counter += 1
        else:
            self.wrong_dir_counter = 0

        return self.wrong_dir_counter >= 2

    # --------------------------------------------------
    # Off-route detection (windowed)
    # --------------------------------------------------
    def offRoute(self, gps, max_dist=40.0, window=30):
        if not self.path:
            return False
        start = max(0, self.index - window)
        end   = min(len(self.path), self.index + window + 1)
        distance = min(self.map.distance(gps, self.path[i]) for i in range(start, end))
        return distance > max_dist

    def targetReached(self,gps):
        print("current", gps)
        self.dist_to_target = self.map.distance(gps, self.target)
        print(self.dist_to_target)
        if self.dist_to_target < 5.0:
            if self.index < len(self.path) - 1:
                self.state = "TARGET_REACHED"
                self.index+=1
            else:
                self.state = "DESTINATION_REACHED"
            return True
        return False

    # --------------------------------------------------
    # MAIN NAVIGATION LOOP
    # --------------------------------------------------
    def navigate(self, gps, speed_mps=0.0):
        prevLocation = self.map.filtered_gps
        if prevLocation is None or not self.path:
            return self.state

        self.updateTarget()

        # --------------------------------------------------
        # OFF ROUTE CHECK FIRST (no snapping yet)
        # --------------------------------------------------
        if self.offRoute(gps):
            self.state = "OFF_ROUTE"
            prevLocation = gps
            return self.state

        # --------------------------------------------------
        # WAYPOINT REACH CHECK
        # --------------------------------------------------

        if self.targetReached(gps):
            self.updateTarget()

        # --------------------------------------------------
        # WRONG DIRECTION
        # --------------------------------------------------
        if self.checkDirection(gps, speed_mps):
            self.turn_angle = self.map.turn_angle(self.target)
            self.state = "WRONG_DIRECTION"
        else:
            self.turn_angle = 0.0
            self.state = "FOLLOW_ROUTE"

        return self.state