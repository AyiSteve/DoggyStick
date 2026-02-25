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
        self.heading = None


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

        self.target = self.path[self.index]



    # --------------------------------------------------
    # Wrong direction detection
    # --------------------------------------------------
    def checkDirection(self, gps, speed_mps):

        if gps is None or self.heading is None or self.target is None:
            return False

        # Desired direction toward target
        desired = self.map.bearing(gps, self.target)

        # Signed turn angle (-180 to 180)
        turn = (desired - self.heading + 540) % 360 - 180
        self.turn_angle = turn
        error = abs(turn)

        # Dynamic threshold (walking vs standing)
        threshold = 20 if speed_mps > .7 else 40

        if error > threshold:
            self.wrong_dir_counter += 1
        else:
            self.wrong_dir_counter = 0

        return self.wrong_dir_counter >= 2

    # --------------------------------------------------
    # Off-route detection (windowed)
    # --------------------------------------------------
    def offRoute(self, gps, target_thresh=20.0, snap_thresh=15.0, max_dist=30.0):

        if not self.path or self.target is None:
            return False

        # ---------------------------------------------
        # Step 1: Check distance to current target
        # ---------------------------------------------
        dist_to_target = self.map.distance(gps, self.target)

        # If still reasonably close ? stay on course
        if dist_to_target < target_thresh:
            return False

        # ---------------------------------------------
        # Step 2: Search forward waypoints
        # ---------------------------------------------
        nearest_index = self.index
        nearest_dist = dist_to_target

        for i in range(self.index + 1, len(self.path)):
            d = self.map.distance(gps, self.path[i])
            if d < nearest_dist:
                nearest_dist = d
                nearest_index = i

        # ---------------------------------------------
        # Step 3: Snap forward if closer point found
        # ---------------------------------------------
        if nearest_index > self.index and nearest_dist < snap_thresh:
            self.index = nearest_index
            self.target = self.path[self.index]
            return False

        # ---------------------------------------------
        # Step 4: Too far from everything ? off route
        # ---------------------------------------------
        if nearest_dist > max_dist:
            return True

        return False

    def targetReached(self):
        if self.dist_to_target < 7.0:
            if self.index < len(self.path) - 1:
                self.state = "TARGET_REACHED"
                self.index+=1
            else:
                self.state = "DESTINATION_REACHED"

    # --------------------------------------------------
    # MAIN NAVIGATION LOOP
    # --------------------------------------------------
    def navigate(self, gps, speed_mps):
        prevLocation = self.prevGPS
        if prevLocation is None or not self.path:
            return self.state

        # --------------------------------------------------
        # OFF ROUTE CHECK FIRST (no snapping yet)
        # --------------------------------------------------
        self.updateTarget()

        if self.state == "TARGET_REACHED" or self.state == "DESTINATION_REACHED":
            return self.state

        if self.offRoute(gps):
            self.state = "OFF_ROUTE"
            return self.state

        # --------------------------------------------------
        # WRONG DIRECTION
        # --------------------------------------------------
        if self.checkDirection(gps, speed_mps):
            self.state = "WRONG_DIRECTION"
        else:
            self.turn_angle = 0.0
            self.state = "FOLLOW_ROUTE"

        return self.state