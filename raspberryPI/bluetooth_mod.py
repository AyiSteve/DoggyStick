import subprocess
import time 
import serial

class BluetoothUART:
    def __init__(self, mac, rfcomm_port=0, baud=9600, timeout=1):
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

    def send(self,msg:str):
        if self.ser is None:
            raise RuntimeError("BluetoothUART not connect, call connect() first")
        self.ser.write((msg + "\n").encode())

    def readline(self):
        if self.ser is None:
            raise RuntimeError("BluetoothUART not connect, call connect() first")
        line = self.ser.readline().decode(errors="ignore").strip()
        return line if line else None
    
    def close(self):
        try:
            if self.ser:
                self.ser.close()
        finally:
            self.ser =None
            subprocess.run(["sudo", "rfcomm", "release", str(self.rfcomm_port)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
