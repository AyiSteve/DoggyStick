import time
from api.mapapi import MapNavigator
from navigation import Navigation
from mygps import myGPS
import threading
from mygps import myGPS
from bluetooth_mod import BluetoothUART
from button_recorder import VoiceRecordButton
from server import start_debug_server

class NavigationSupervisor:
    def __init__(self, mode="walk", period=1.0):
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

    def reset(self, destination):
        # keep same map_nav object
        self.map_nav.updateDestination(destination)
        self.map_nav.updateDirection()

        # update navigation path
        self.nav_agent.path = self.map_nav.WalkPath
        self.nav_agent.index = 0
        self.nav_agent.target = None

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

        self.map_nav.updateCurrentLocation(self.gps.lowPassFilter(pos))

    def read_ultrasonic(self):
        self.ultrasonicLine = self.stm32.readline()
        print(ns.ultrasonicLine)

    def send_angleServo(self, angle):
        self.stm32.send(angle)

# PipLineGetPath function will be run independently on capturing the data from mic, asking user for correct addres + update the destination location
    def pipLineGetPath(self, numPlace=5):

        text = self.read_Mic()
        print()
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

        choice = input("\nSelect destination number: ")

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(result):

                selected = result[index]

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
            gps = self.map_nav.currentLocation
            self.state = self.nav_agent.navigate(gps)


    # def read_gps(self):
    #     try:
    #         lat = float(input("Enter latitude  : "))
    #         lon = float(input("Enter longitude : "))
    #         self.map_nav.updateCurrentLocation((lat,lon))
    #     except ValueError:
    #         print("Invalid input. Please enter numeric values.")
    #         return None

    def stop_navigation(self):
        self.navigating = False
        print("[Navigation Supervisor] Navigation Stopped")

    # --------------------------------------------------
    # STATE MACHINE OUTPUT
    # --------------------------------------------------
    def stateMachine(self, state):

        if state == None:
            return
        
        if state == "FOLLOW_ROUTE":
            target = self.nav_agent.target
            print(f"[FOLLOW] target={target}")

        elif state == "WRONG_DIRECTION":
            angle = self.nav_agent.turn_angle
            if angle > 0:
                print(f"Turn RIGHT {angle:.1f}ï¿½")
            else:
                print(f"Turn LEFT {abs(angle):.1f}ï¿½")

        elif state == "OFF_ROUTE":
            self.nav_agent.updatePath()

            print("[WARN] Off route ? stop + reroute suggestion")

        elif state == "DESTINATION_REACHED":
            print("[DONE] Destination reached ? stopping navigation")
            self.stop_navigation()
            
# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    ns = NavigationSupervisor()
    ns.lock = threading.Lock()

    # -------------------------
    # GPS Thread
    # -------------------------
    def gps_loop():
        while True:
            with ns.lock:
                ns.read_gps()

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
                ns.pipeLineStatusPath()
                if ns.state:
                    ns.stateMachine(ns.state)
            time.sleep(0.5)

    # Start all threads
    threading.Thread(target=gps_loop, daemon=True).start()
    # threading.Thread(target=ultrasonic_loop, daemon=True).start()
    threading.Thread(target=voice_loop, daemon=True).start()
    threading.Thread(target=navigation_loop, daemon=True).start()
    # Debug web server (runs in background)
    threading.Thread(
        target=start_debug_server,
        args=(ns, "0.0.0.0", 8080),   # 0.0.0.0 lets you view from another device on same WiFi
        daemon=True
    ).start()

    
    # Keep main thread alive
    while True:
        time.sleep(1)