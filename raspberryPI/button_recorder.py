import RPi.GPIO as GPIO 
import subprocess
import os
import time

from bluetooth_mod import BluetoothUART 

"""
1st: make sure in /home/doggystick/doggystick/DoggyStick/raspberryPI
2nd: enter venv envirment: sudo venv/bin/acticate
3rd: run it by: python button_recorder.py
"""
class VoiceRecordButton:
    def __init__(self, button_pin=11, device="plughw:2,0",
                 stereo_wav="test_stereo.wav",
                 mono_wav="command.wav", duration=6,
                 model_path="vosk-model-small-en-us-0.15",
                 venv_python="./venv/bin/python",
                 stt_scipt="./stt.py",
                 debounce_ms=200):
        GPIO.cleanup()
        time.sleep(0.1)
        self.button_pin = button_pin
        self.device = device
        self.stereo_wav= stereo_wav
        self.mono_wav = mono_wav
        self.duration = duration
        self.model_path =model_path
        self.debounce_ms = debounce_ms
        self.venv_python = venv_python
        self.stt_script=stt_scipt


        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print("Button readyon pin11")
        print("[GPIO] Press button to record...")
    
    def _on_press(self, channel):
        self._on_press = True


    def record_stereo_audio(self):
        print("recording stereo audio...." )
        cmd = ["arecord", "-D", self.device,
               "-c", "2", "-r","48000",
               "-f", "S32_LE", "-t", "wav", "-d", str(self.duration),
               self.stereo_wav

        ]

        subprocess.run(cmd, check=True)
        print(f"[REC] saved: {self.stereo_wav}")
    
    def convert_to_mono(self):
        print("[SOX] converting to mono")

        cmd = [
            "sox", self.stereo_wav, "-r", "16000", "-c",
            "1", "-b", "16", self.mono_wav, "remix", "1"
        ]
        subprocess.run(cmd, check=True)
        print(f"[SOX] saved: {self.mono_wav}")
    
    def stt(self):
        print("[STT] Running VOSK...")
        subprocess.run([
            self.venv_python,
            self.stt_script,
            self.mono_wav
        ], check= True) 

    def run_forever(self):
        try:
            print("[GPIO] Ready to press button to record...")
            while True:
                if GPIO.input(self.button_pin) == GPIO.LOW:
                    time.sleep(0.05)
                    if GPIO.input(self.button_pin) == GPIO.LOW:
                        continue
                    print("[BIN] Press detect")
                    self.record_stereo_audio()

                    print("[BIN] waiting release....")
                    while GPIO.input(self.button_pin) == GPIO.LOW:
                            time.sleep(0.05)
                    time.sleep(0.05)
                    print("[BIN] Release wait for converting")
                    self.convert_to_mono()
                    self.stt()
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n[Exit] Stopping")
        finally:
            GPIO.cleanup()
            print("[GPIO] Clean up")
    # def run_forever(self):
    #     try:
    #         while True:
    #             if GPIO.input(self.button_pin) == GPIO.LOW:
    #                 time.sleep(0.05)
    #                 if GPIO.input(self.button_pin) == GPIO.LOW:
    #                     print("[BIN] Press detect")
    #                     self.record_stereo_audio()
    #                     self.convert_to_mono()
    #                     self.stt()

    #                     while GPIO.input(self.button_pin) == GPIO.LOW:
    #                         time.sleep(0.05)
    #                     time.sleep(self.debounce_ms)
    #             time.sleep(0.01)
    #     except KeyboardInterrupt:
    #         print("\n[Exit] Stopping")
    #     finally:
    #         GPIO.cleanup()
    #         print("[GPIO] Clean up")
        

if __name__ == "__main__":
    # recorder = VoiceRecordButton()
    # recorder.run_forever()

    HC06 = "00:23:09:01:63:00"
    bt = BluetoothUART(mac=HC06)

    try:
        bt.connect()
        print("[BT] connect  to Bluetooth HC-06")

        bt.send("Hello STM32")
        reply = bt.readline()
        print("STM32 say:", reply)
        recorder = VoiceRecordButton()
        recorder.run_forever()
    except KeyboardInterrupt:
        print("\n[exit] Stopping..")
    finally:
        bt.close()

        

# downlaod GPIO pakage
# sudo apt-get install -y python3-rpi.gpio alsa-utils


# test button code 

# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# try:
#     while True:
#         print(GPIO.input(11))
#         time.sleep(0.2)
# finally:
#     GPIO.cleanup()




