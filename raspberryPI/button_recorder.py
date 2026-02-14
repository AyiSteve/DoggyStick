from gpiozero import Button
from signal import pause
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
                 stereo_wav="test_stereo.wav",
                 mono_wav="command.wav",
                 duration=6,
                 venv_python="./venv/bin/python",
                 stt_script="./stt.py"):

        self.button = Button(button_pin, pull_up=True, bounce_time=0.2)

        self.device = device
        self.stereo_wav = stereo_wav
        self.mono_wav = mono_wav
        self.duration = duration
        self.venv_python = venv_python
        self.stt_script = stt_script
        self.script = ""

        print("[GPIO] Button ready on BCM 17 (physical pin 11)")
        print("[GPIO] Press button to record...")

        # attach event
        self.button.when_pressed = self.handle_press

    # --------------------------------------------------
    # BUTTON EVENT
    # --------------------------------------------------
    def handle_press(self):
        print("[BTN] Press detected")

        Thread(target=self.process_audio).start()

    def process_audio(self):
        self.record_and_prepare_audio()
        self.script = self.stt()
        
    # --------------------------------------------------
    def record_and_prepare_audio(self):
        temp_wav = "temp.wav"        # raw stereo capture
        self.mono_wav = "command.wav"  # final file for VOSK

        # Step 1 ? Record stereo (INMP441 works better this way)
        cmd_record = [
            "arecord",
            "-D", self.device,
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "2",                 # record stereo
            "-d", str(self.duration),
            temp_wav
        ]
        subprocess.run(cmd_record, check=True)
        print(f"[REC] Saved stereo file: {temp_wav}")

        # Step 2 ? Extract clean channel and convert to mono
        cmd_convert = [
            "sox", temp_wav,
            "-r", "16000",
            "-b", "16",
            "-c", "1",
            self.mono_wav,
            "remix", "1"               # use LEFT channel
        ]
        subprocess.run(cmd_convert, check=True)
        print(f"[SOX] Converted to mono: {self.mono_wav}")



    # --------------------------------------------------
    def stt(self):
        print("[STT] Running VOSK...")
        text = get_text(self.mono_wav)
        print(f"[STT] Recognized text: {text}")   # <-- add this line
        return text
        


