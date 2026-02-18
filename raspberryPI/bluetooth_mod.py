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

    def send(self, angleServo, mode = "servo"):
        if self.ser is None:
            raise RuntimeError("BluetoothUART not connect, call connect() first")
        data = f"{angleServo}\n"
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
# while True:
#     for i in [0, 45, 90, 180]:
#         bt.send(i)
#         print(i)
#         time.sleep(5)