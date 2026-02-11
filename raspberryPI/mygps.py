import serial
import pynmea2

class myGPS:
    def __init__(self, PORT="/dev/serial0", BAUD=9600):
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=1)
        except serial.SerialException:
            self.ser = None
        # Quality
        self.quality = 0
        self.numSatellites = 0
        self.valid_fix = False

        # Position
        self.latitude = None
        self.longitude = None
        self.altitude = None

        # Navigation
        self.speed_knots = None
        self.timestamp = None
        self.datestamp = None

        print("Reading GPS data\n")

    def read(self):
        """Read one line from serial and parse it"""
        try:
            line = self.ser.readline().decode("ascii", errors="ignore").strip()
            if line:
                self.read_line(line)
        except serial.SerialException:
            pass

    def read_line(self, line):
        """Parse a provided NMEA line (for testing)"""
        if not line.startswith("$"):
            return

        try:
            msg = pynmea2.parse(line)

            if isinstance(msg, pynmea2.types.talker.GGA):
                self.quality = int(msg.gps_qual or 0)
                self.numSatellites = int(msg.num_sats or 0)
                self.altitude = msg.altitude
                self.valid_fix = self.quality > 0

            elif isinstance(msg, pynmea2.types.talker.RMC):
                if msg.status == "A":
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude
                    self.speed_knots = msg.spd_over_grnd
                    self.timestamp = msg.timestamp
                    self.datestamp = msg.datestamp
                    self.valid_fix = True

        except pynmea2.ParseError:
            pass
                
    def has_fix(self):
        """Safe check for usable GPS"""
        return self.valid_fix and self.latitude is not None

    def get_position(self):
        """Return tuple or None"""
        if self.has_fix():            
            return (float(self.latitude), float(self.longitude))
        return None

def test_myGPS():
    gps = myGPS()   # serial not used for test

    while True:
        gps.read()

        print("---- TEST RESULTS ----")
        print("Fix quality   :", gps.quality)
        print("Satellites    :", gps.numSatellites)
        print("Valid fix     :", gps.valid_fix)
        print("Latitude      :", gps.latitude)
        print("Longitude     :", gps.longitude)
        print("Altitude (m)  :", gps.altitude)
        print("Speed (knots) :", gps.speed_knots)
        print("Timestamp     :", gps.timestamp)
        print("Date          :", gps.datestamp)

