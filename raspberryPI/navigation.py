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

        self.state = "IDLE"
        self.heading = None
        self.prevGPS = None

        self.turn_angle = 0.0
        self.dist_to_target = 0.0
        self.wrong_dir_counter = 0

    def updatePath(self):
        self.map.updateDirection()
        self.path = self.map.WalkPath
        self.index = 0
        self.target = self.path[0] if self.path else None

        self.state = "IDLE"
        self.turn_angle = 0.0
        self.dist_to_target = 0.0
        self.wrong_dir_counter = 0
        self.heading = None
        self.prevGPS = None

    def updateTarget(self):
        if not self.path:
            self.target = None
            return
        self.target = self.path[self.index]

    def avoidObstacle(self, front, left, right):
        STOP = 20
        SAFE_FRONT = 50
        SIDE_MIN = 20
        CART_HALF = 20

        left_safe = left - CART_HALF
        right_safe = right - CART_HALF

        if front < STOP:
            return -60 if left > right else 60

        if front < SAFE_FRONT or left_safe < SIDE_MIN or right_safe < SIDE_MIN:
            bias = right_safe - left_safe

            if abs(bias) < 5:
                return -45 if left_safe > right_safe else 45

            return max(min(bias * 2.5, 60), -60)

        return None

    def routeAngle(self, gps):
        if self.target is None:
            return 0.0

        desired = self.map.bearing(gps, self.target)

        if self.heading is None:
            return 0.0

        nav_angle = (desired - self.heading + 540) % 360 - 180
        print(nav_angle)
        return nav_angle

    def wrongDirection(self, nav_angle):
        ERROR_THRESHOLD = 35
        if abs(nav_angle) > ERROR_THRESHOLD:
            self.wrong_dir_counter += 1
        else:
            self.wrong_dir_counter = 0

        return self.wrong_dir_counter >= 2

    def offRoute(self, gps, max_dist=20.0):
        if not self.path:
            return False

        nearest = min(self.map.distance(gps, wp) for wp in self.path)
        return nearest > max_dist

    def targetReached(self, reach_dist=7.0):
        if self.target is None:
            return False

        if self.dist_to_target >= reach_dist:
            return False

        if self.index < len(self.path) - 1:
            self.index += 1
            self.target = self.path[self.index]
            return False

        return True

    def navigate(self, front, left, right, lightStatus):
        gps = self.map.currentLocation

        if gps is None or not self.path:
            self.state = "IDLE"
            self.turn_angle = 0.0
            return self.state

        self.updateTarget()

        if self.target is None:
            self.state = "IDLE"
            self.turn_angle = 0.0
            return self.state

        self.dist_to_target = self.map.distance(gps, self.target)


        # Priority 1: emergency stop
        if lightStatus:
            self.state = "EMStop"
            self.turn_angle = 0.0
            return self.state

        # Priority 2: destination reached
        if self.targetReached():
            self.state = "DESTINATION_REACHED"
            self.turn_angle = 0.0
            return self.state

        # Priority 3: off route
        if self.offRoute(gps):
            self.state = "OFF_ROUTE"
            self.turn_angle = 0.0
            return self.state

        # Priority 4: obstacle avoidance
        avoid_angle = self.avoidObstacle(front, left, right)
        if avoid_angle is not None:
            self.turn_angle = avoid_angle
            self.state = "AVOID"
            return self.state

        # Priority 5: route following / wrong direction
        nav_angle = self.routeAngle(gps)
        self.turn_angle = nav_angle

        if self.heading is None:
            self.state = "FOLLOW_ROUTE"
            return self.state

        if self.wrongDirection(nav_angle):
            self.state = "WRONG_DIRECTION"
        else:
            self.state = "FOLLOW_ROUTE"

        return self.state