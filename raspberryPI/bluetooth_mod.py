import subprocess
import time 
import serial

class BluetoothUART:
    def __init__(self, mac = "00:23:09:01:63:2A", rfcomm_port=0, baud=9600, timeout=1):
        self.mac = mac
        self.rfcomm_port = rfcomm_port
        self.dev = f"/dev/rfcomm{rfcomm_port}"
        self.baud =baud
        self.timeout = timeout
        self.ser = None
        self.ultrasonic = None


    def connect(self):
        subprocess.run(["sudo", "rfcomm", "release", str(self.rfcomm_port)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "rfcomm", "bind", str(self.rfcomm_port), self.mac],
                       check=True)
        time.sleep(0.5)
        self.ser = serial.Serial(self.dev, self.baud, timeout=self.timeout)

    def readline(self):
        if self.ser is None:
            raise RuntimeError("BluetoothUART not connect, call connect() first")
        line = self.ser.readline().decode(errors="ignore").strip()
        return line if line else None

    def read_ultrasonic(self):
        line = self.stm32.readline()
        if not line:
            return

        try:
            front, left, right = map(float, line.split(","))
            self.ultrasonic = {
                "front": front,
                "left": left,
                "right": right,
            }
        except ValueError:
            return

    def compute_turn_time(self, angle, TURN_RATE=1.8):
        """
        angle: desired turn in degrees
            positive = right
            negative = left
        """

        seconds = abs(angle) * (TURN_RATE/90)
        direction = 2 if angle > 0 else 1

        return direction, seconds

    def send_drive_command(self, angle):
        direction, ms = self.stm32.compute_turn_time(angle)

        # small angle means go straight
        if abs(angle) < 10:
            self.stm32.send(3, 300)
        else:
            self.stm32.send(direction, ms)
            
    def send(self, direction, seconds=1):
        if self.ser is None:
            raise RuntimeError("BluetoothUART not connect, call connect() first")

        data = f"{direction},{seconds}\n"
        self.ser.write(data.encode())

    def close(self):
        try:
            if self.ser:
                self.ser.close()
        finally:
            self.ser =None
            subprocess.run(["sudo", "rfcomm", "release", str(self.rfcomm_port)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Un Comment to test send servo
# bt = BluetoothUART()
# bt.connect()
# time.sleep(5)
# print(bt.compute_turn_time(90))
# bt.send(bt.compute_turn_time(90)[0],bt.compute_turn_time(90)[1])
# print(bt.readline())