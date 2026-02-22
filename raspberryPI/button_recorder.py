from gpiozero import Button
import signal
from stt import get_text
import subprocess
import time
import sys
from threading import Thread

from bluetooth_mod import BluetoothUART


class VoiceRecordButton:
    def __init__(self,
                 button_pin=17,   # BCM 17 (physical pin 11)
                 device="plughw:2,0",
                 stereo_wav="temp.wav",
                 mono_wav="command.wav"):

        self.button = Button(button_pin, pull_up=True, bounce_time=0.2)

        self.device = device
        self.stereo_wav = stereo_wav
        self.mono_wav = mono_wav
        self.script = ""
        self.record_process = None

        print("[GPIO] Button ready on BCM 17 (physical pin 11)")
        print("[GPIO] Press button to record...")

        # attach event
        self.button.when_pressed = self.start_recording
        self.button.when_released = self.stop_recording
        
    # --------------------------------------------------
    def start_recording(self):
        print("[BTN] Recording Started")
        # Step 1 ? Record stereo (INMP441 works better this way)
        cmd_record = [
            "arecord",
            "-D", self.device,
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "2",                 # record stereo
            self.stereo_wav
        ]

        self.record_process = subprocess.Popen(cmd_record)

    def stop_recording(self):

        print("BTN Recording Stopped")

        if self.record_process:
            self.record_process.send_signal(signal.SIGINT)
            self.record_process.wait()
            self.record_process = None

        Thread(target=self.process_audio).start()


    def process_audio(self):
        self.convert_to_mono()
        self.script = self.stt()
    
    def convert_to_mono(self):
        cmd_convert = [
            "sox", self.stereo_wav,
            "-r", "16000",
            "-b", "16",
            "-c", "1",
            self.mono_wav,
            "remix", "1"               
        ]

        subprocess.run(cmd_convert, check=True)
        print(f"[SOX] Converted to mono: {self.mono_wav}")

    # --------------------------------------------------
    def stt(self):
        print("[STT] Running VOSK...")
        text = get_text(self.mono_wav)
        print(text)
        return text
        


