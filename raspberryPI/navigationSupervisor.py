import time
from api.mapapi import MapNavigator
from navigation import Navigation
from mygps import myGPS

from mygps import myGPS
from bluetooth_mod import BluetoothUART
from button_recorder import VoiceRecordButton

class NavigationSupervisor:
    def __init__(self, mode="walk", period=1.0):
        self.period = period
        self.mode = mode

        self.gps = None

        self.map_nav = MapNavigator(None)
        self.nav_agent = Navigation(self.map_nav)

        self.navigating = False
        self.destination = None

        self.ultrasonic = BluetoothUART()
        self.ultrasonic.connect()

        self.voiceRecord = VoiceRecordButton()
    # --------------------------------------------------
    # INPUT SOURCES
    # --------------------------------------------------
    def read_Mic(self):
        # Replace later
        read = self.voiceRecord.script
        self.voiceRecord.script = None   # clear after reading
        return read

    def read_gps(self):
        self.gps.read()
        position = self.nav_agent.smoothGPS(self.gps.get_position())
        return position

    def read_ultrasonic(self):
        ultrasonicLine = self.ultrasonic.read_line()
        return [int(num) for num in ultrasonicLine.split()]
    # def read_gps(self):
    #     self.gps.read()
    #     position = self.nav_agent.smoothGPS(self.gps.get_position())
    #     return position

    def read_gps(self):
        try:
            lat = float(input("Enter latitude  : "))
            lon = float(input("Enter longitude : "))
            return (lat, lon)
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            return None

   # --------------------------------------------------
    # NAVIGATION CONTROL
    # --------------------------------------------------
    def setDestination(self, destination):
        self.destination = destination
        self.map_nav.updateDestination(destination)

    def startNavigation(self):

        self.map_nav.updateDirection()
        self.nav_agent.path = self.map_nav.WalkPath

        cl = self.map_nav.currentLocation

        if cl is None or not self.nav_agent.path:
            print("Cannot start navigation ? missing GPS or path")
            return

        # Forward nearest snapping
        nearest_index = min(
            range(len(self.nav_agent.path)),
            key=lambda i: self.map_nav.distance(cl, self.nav_agent.path[i])
        )

        self.nav_agent.index = nearest_index
        self.navigating = True

        print(f"[Supervisor] Navigation started at index {nearest_index}")

    def stop_navigation(self):
        self.navigating = False
        print("[Navigation Supervisor] Navigation Stopped")

    # --------------------------------------------------
    # STATE MACHINE OUTPUT
    # --------------------------------------------------
    def stateMachine(self, state, gps):

        if state == "FOLLOW_ROUTE":
            target = self.nav_agent.target
            desired = self.map_nav.bearing(gps, target)
            print(f"[FOLLOW] target={target} desired_heading={desired:.1f}")

        elif state == "WRONG_DIRECTION":
            angle = self.nav_agent.turn_angle
            if angle > 0:
                print(f"Turn RIGHT {angle:.1f}�")
            else:
                print(f"Turn LEFT {abs(angle):.1f}�")

        elif state == "OFF_ROUTE":
            # Recalculate route
            new_path = self.map_nav.recalculateRoute(cl)

            # Create new Navigation instance
            self.nav_agent = Navigation(self.map_nav)
            self.nav_agent.path = new_path
            self.nav_agent.updateTarget()

            print("[WARN] Off route ? stop + reroute suggestion")

        elif state == "DESTINATION_REACHED":
            print("[DONE] Destination reached ? stopping navigation")
            self.stop_navigation()

    # --------------------------------------------------
    # DESTINATION UPDATE LOGIC
    # --------------------------------------------------
    def updateNavigatingStatus(self, cl):

        potentialDestination = self.read_Mic()

        if potentialDestination == "Stop":
            self.stop_navigation()
            return

        if potentialDestination and cl:

            # Only initialize once
            if not self.map_nav:
                self.map_nav = MapNavigator(cl)
                self.nav_agent = Navigation(self.map_nav, mode=self.mode)

            # Only restart if destination changes
            if potentialDestination != self.destination:
                self.setDestination(potentialDestination)
                self.startNavigation()

    # --------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------
    def run(self):
        print("[Supervisor] Running main loop")
        while(1):
            new_text = self.read_Mic()

            if new_text is not None:
                if self.destination != new_text:
                    self.destination = new_text
                    print("New destination:", self.destination)

        # while True:
        #     start = time.time()

        #     cl = self.read_gps()
        #     if cl is None:
        #         time.sleep(0.2)
        #         continue

        #     # Initialize map navigator once GPS is ready
        #     if not self.map_nav:
        #         self.map_nav = MapNavigator(cl)
        #         self.nav_agent = Navigation(self.map_nav, mode=self.mode)

        #     self.map_nav.updateCurrentLocation(cl)

        #     self.updateNavigatingStatus(cl)

        #     if self.navigating and self.nav_agent.path:

        #         print("Current location:", cl)
        #         print("Current index:", self.nav_agent.index)

        #         state = self.nav_agent.navigate(cl)
        #         self.stateMachine(state, cl)

        #     elapsed = time.time() - start
        #     time.sleep(max(0.0, self.period - elapsed))


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    ns = NavigationSupervisor()
    ns.run()