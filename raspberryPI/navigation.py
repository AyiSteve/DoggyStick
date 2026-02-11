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

        self.prevGPS = None
        self.state = "FOLLOW_ROUTE"
        self.heading = None

        self.turn_angle = 0.0
        self.offroute_counter = 0
        self.wrong_dir_counter = 0

    # --------------------------------------------------
    # Target update
    # --------------------------------------------------
    def updateTarget(self):
        if not self.path or len(self.path) == 0:
            raise RuntimeError("Navigation path not initialized")

        if self.index >= len(self.path):
            self.index = len(self.path) - 1
            self.state = "DESTINATION_REACHED"
            return

        self.target = self.path[self.index]

    # --------------------------------------------------
    # Heading estimation
    # --------------------------------------------------
    def gpsHeading(self, gps):
        if self.prevGPS is None:
            return None
        return self.map.bearing(self.prevGPS, gps)



    def smoothGPS(self, gps):
        if self.prevGPS is None:
            return gps

        lat = (gps[0] + self.prevGPS[0]) / 2
        lon = (gps[1] + self.prevGPS[1]) / 2
        return (lat, lon)
        
    # --------------------------------------------------
    # Wrong direction detection
    # --------------------------------------------------
    def checkDirection(self, gps, speed_mps):

        if self.prevGPS is None:
            return False

        move_dist = self.map.distance(self.prevGPS, gps)

        # Must move at least 2 meters
        if move_dist < 1.0:
            return False

        heading = self.gpsHeading(gps)
        if heading is None:
            return False

        desired = self.map.bearing(gps, self.target)

        # Signed turn angle (-180 to 180)
        turn = (desired - heading + 540) % 360 - 180
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
    def offRoute(self, gps, max_dist=10.0):

        if not self.path:
            return False

        # Only search nearby forward window
        search_start = max(0, self.index - 5)
        search_end = min(len(self.path), self.index + 20)

        nearest = min(
            self.map.distance(gps, self.path[i])
            for i in range(search_start, search_end)
        )

        if nearest > max_dist:
            self.offroute_counter += 1
        else:
            self.offroute_counter = 0

        return self.offroute_counter >= 4
    # --------------------------------------------------
    # Turn angle computation
    # --------------------------------------------------
    def computeTurnAngle(self, gps):
        heading = self.gpsHeading(gps)
        if heading is None or self.target is None:
            return None

        desired = self.map.bearing(gps, self.target)
        return (desired - heading + 540) % 360 - 180

    # --------------------------------------------------
    # MAIN NAVIGATION LOOP
    # --------------------------------------------------
    def navigate(self, gps, speed_mps=0.0):

        if gps is None or not self.path:
            return self.state

        self.updateTarget()

        # --------------------------------------------------
        # OFF ROUTE CHECK FIRST (no snapping yet)
        # --------------------------------------------------
        if self.offRoute(gps):
            self.state = "OFF_ROUTE"
            self.prevGPS = gps
            return self.state

        # --------------------------------------------------
        # FORWARD-ONLY SNAPPING (small window)
        # --------------------------------------------------
        search_start = self.index
        search_end = min(len(self.path), self.index + 3)

        nearest_index = min(
            range(search_start, search_end),
            key=lambda i: self.map.distance(gps, self.path[i])
        )

        self.index = nearest_index
        self.updateTarget()

        # --------------------------------------------------
        # WAYPOINT REACH CHECK
        # --------------------------------------------------
        dist_to_target = self.map.distance(gps, self.target)

        if dist_to_target < 5.0:
            if self.index < len(self.path) - 1:
                self.index += 1
                self.updateTarget()
            else:
                self.state = "DESTINATION_REACHED"
                return self.state

        # --------------------------------------------------
        # WRONG DIRECTION
        # --------------------------------------------------
        if self.checkDirection(gps, speed_mps):
            self.turn_angle = self.computeTurnAngle(gps)
            self.state = "WRONG_DIRECTION"
        else:
            self.turn_angle = 0.0
            self.state = "FOLLOW_ROUTE"

        self.prevGPS = gps
        return self.state