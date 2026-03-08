import time
from api.mapapi import MapNavigator
from navigation import Navigation
from mygps import myGPS
import threading
from bluetooth_mod import BluetoothUART
from button_recorder import VoiceRecordButton
from server import start_debug_server
from api.object_detection import PedestrianLightDetector
from cameraNobjectdec import capture_detection

class NavigationSupervisor:
    def __init__(self, mode="walk", period=0.2):
        self.period = period
        self.mode = mode

        self.gps = myGPS()

        self.map_nav = MapNavigator(None)
        self.nav_agent = Navigation(self.map_nav)

        self.navigating = False


        self.stm32 = BluetoothUART()
        self.stm32.connect()
        self.ultrasonicLine = None


        self.voiceRecord = VoiceRecordButton()

        self.state = None
        self.light_state = False

    def reset(self, destination):
        # keep same map_nav object
        self.map_nav.updateDestination(destination)
        self.map_nav.updateDirection()

        # update navigation path
        self.nav_agent.path = self.map_nav.WalkPath
        self.nav_agent.index = 0
        if not self.nav_agent.path:
            print("No path returned from Map API")
            self.navigating = False
            return
        self.nav_agent.target = self.nav_agent.path[0]

    # --------------------------------------------------
    # INPUT SOURCES
    # --------------------------------------------------
    def read_Mic(self):
        # Replace later
        read = self.voiceRecord.script
        self.voiceRecord.script = None   # clear after reading
        return read

    # This function will be run independently to update the current location
    def read_gps(self):
        self.gps.read()
        pos = self.gps.get_position()

        if pos is None:
            self.map_nav.updateCurrentLocation(None)
            return

        self.map_nav.updateCurrentLocation(self.map_nav.lowPassFilter(pos))

        if self.nav_agent.prevGPS is None:
            self.nav_agent.prevGPS = self.map_nav.currentLocation
        if self.map_nav.distance(self.nav_agent.prevGPS, self.map_nav.currentLocation) > 0.8:
            self.nav_agent.heading = self.map_nav.bearing(self.nav_agent.prevGPS, self.map_nav.currentLocation)
            self.nav_agent.prevGPS = self.map_nav.currentLocation


    def read_ultrasonic(self):
        self.stm32.read_ultrasonic()

# PipLineGetPath function will be run independently on capturing the data from mic, asking user for correct addres + update the destination location
    def pipLineGetPath(self, numPlace=5):

        text = self.read_Mic()
        if text is None or self.map_nav.currentLocation is None:
            return

        result = self.map_nav.text_search(text)

        if not result:
            print("No results found.")
            return

        # Show options
        for i, place in enumerate(result[:numPlace]):
            name = place["displayName"]["text"]
            addr = place.get("formattedAddress", "")
            print(f"{i+1}. {name} — {addr}")

        selected = result[0]

        name = selected["displayName"]["text"]

        lat = selected["location"]["latitude"]
        lng = selected["location"]["longitude"]

            # Store coordinates
        with self.lock:
            self.reset((lat,lng))
            self.navigating = True
        print(f"Destination set: {name}")
        print(f"Coordinates: ({lat}, {lng})")

    def pipeLineStatusPath(self):
        if self.map_nav.currentLocation == None or self.nav_agent.path == None:
            return
        
        if self.navigating:
            u = self.stm32.ultrasonic

            if not u or "front" not in u:
                return
            self.state = self.nav_agent.navigate(u["front"],u["left"],u["right"], self.light_state)



    # def read_gps(self):
    #     try:
    #         lat = float(input("Enter latitude  : "))
    #         lon = float(input("Enter longitude : "))
    #         self.map_nav.updateCurrentLocation((lat,lon))
    #     except ValueError:
    #         print("Invalid input. Please enter numeric values.")
    #         return None

    # --------------------------------------------------
    # STATE MACHINE OUTPUT
    # --------------------------------------------------
    def stateMachine(self, state):
        if state is None:
            return

        if state == "EMStop":
            self.navigating = False
            self.stm32.send(4, 0)
            print("RED LIGHT Detected")

        elif state == "FOLLOW_ROUTE":
            angle = self.nav_agent.turn_angle
            if abs(angle) < 10:
                self.stm32.send(3, 300)
            else:
                self.stm32.send_drive_command(angle)
            print(f"[FOLLOW] angle={angle:.1f}")

        elif state == "WRONG_DIRECTION":
            angle = self.nav_agent.turn_angle
            self.stm32.send_drive_command(angle)
            print(f"[TURN] angle={angle:.1f}")

        elif state == "OFF_ROUTE":
            self.stm32.send(4, 0)
            self.nav_agent.updatePath()
            print("[WARN] Off route — rerouting")

        elif state == "DESTINATION_REACHED":
            self.stm32.send(4, 0)
            print("[DONE] Destination reached")
            self.navigating = False
            
# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    ns = NavigationSupervisor()
    ns.lock = threading.Lock()

    # The period of the run is 0.6 second
    # def gps_loop():
    #     while True:
    #         with ns.lock:
    #             ns.read_gps()
    # -------------------------
    # Ultrasonic Thread
    # -------------------------
    def ultrasonic_loop():
        while True:
            with ns.lock:
                ns.read_ultrasonic()
            time.sleep(0.05)

    # -------------------------
    # Voice / Destination Thread
    # -------------------------

    # Period when not voice is .5
    # period when voice is 3.69 including time to enter number
    def voice_loop():
        while True:
            ns.pipLineGetPath()
            time.sleep(0.5)

    # -------------------------
    # Navigation Thread
    # -------------------------
    def navigation_loop():
        while True:
            with ns.lock:
                ns.read_gps()
                ns.pipeLineStatusPath()
                state = ns.state
                navigating = ns.navigating

            if state and navigating:
                ns.stateMachine(state)

            time.sleep(ns.period)

    def camera_loop():
        while True:
            try:
                result = capture_detection()
                if result and result.get("label", "") != "":
                    with ns.lock:
                        ns.light_state = True
                else:
                    with ns.lock:
                        ns.light_state = False
            except Exception as e:
                print("camera error:", e)
                ns.light_state = False

            time.sleep(0.2)
    # Start all threads
    threading.Thread(target=ultrasonic_loop, daemon=True).start()
    threading.Thread(target=voice_loop, daemon=True).start()
    # threading.Thread(target=gps_loop, daemon=True).start()
    threading.Thread(target=navigation_loop, daemon=True).start()
    threading.Thread(target=camera_loop, daemon=True).start()
    # Debug web server (runs in background)
    threading.Thread(
        target=start_debug_server,
        args=(ns, "0.0.0.0", 8080),   # 0.0.0.0 lets you view from another device on same WiFi
        daemon=True
    ).start()

    
    # Keep main thread alive
    while True:
        time.sleep(1)