import subprocess
import time
import serial
import os

class BluetoothUART:

    def __init__(self, mac="00:23:09:01:63:2A", rfcomm_port=0, baud=9600, timeout=0.2):
        self.mac = mac
        self.rfcomm_port = rfcomm_port
        self.dev = f"/dev/rfcomm{rfcomm_port}"
        self.baud = baud
        self.timeout = timeout

        self.ser = None
        self.ultrasonic = None


    def connect(self):

        subprocess.run(
            ["sudo", "rfcomm", "release", str(self.rfcomm_port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["sudo", "rfcomm", "bind", str(self.rfcomm_port), self.mac],
            check=True
        )

        # wait for device file
        for _ in range(20):
            if os.path.exists(self.dev):
                break
            time.sleep(0.2)

        print("Opening serial:", self.dev)

        self.ser = serial.Serial(
            self.dev,
            self.baud,
            timeout=self.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

        time.sleep(1)

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()


    def readline(self):

        if self.ser is None:
            raise RuntimeError("BluetoothUART not connected")

        line = self.ser.readline().decode(errors="ignore").strip()

        if line:
            print("RX:", line)

        return line if line else None


    def read_ultrasonic(self):

        line = self.readline()

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
            pass


    def compute_turn_time(self, angle, TURN_RATE=1.85):

        seconds = abs(angle) * (TURN_RATE / 90)
        ms = int(seconds * 1000)

        direction = 2 if angle > 0 else 1

        return direction, ms


    def send_drive_command(self, angle):

        direction, ms = self.compute_turn_time(angle)

        if abs(angle) < 10:
            self.send(3, 300)
        else:
            self.send(direction, ms)


    def send(self, direction, ms=100):

        if self.ser is None:
            raise RuntimeError("BluetoothUART not connected")


        data = f"{direction},{ms}\n"

        for c in data:
            self.ser.write(c.encode())
            self.ser.flush()
            time.sleep(0.005)   


    def close(self):

        try:
            if self.ser:
                self.ser.close()

        finally:
            self.ser = None

            subprocess.run(
                ["sudo", "rfcomm", "release", str(self.rfcomm_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )


# ----------------------------
# TEST
# ----------------------------

# bt = BluetoothUART()

# bt.connect()

# time.sleep(2)

# while True:

#     bt.send_drive_command(180)

#     time.sleep(100)

