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
        self.record_in_mono()
        self.script = self.stt()

    # --------------------------------------------------
    def record_in_mono(self):
        temp_wav = "temp.wav"  # intermediate file
        
        # Record in high-quality native format
        cmd_record = [
            "arecord", "-D", self.device,
            "-c", "1",         # mono
            "-r", "48000",     # native 48kHz
            "-f", "S32_LE",    # 32-bit PCM
            "-t", "wav",
            "-d", str(self.duration),
            temp_wav
        ]
        subprocess.run(cmd_record, check=True)
        print(f"[REC] Saved temp file: {temp_wav}")
        
        # Downsample to 16 kHz, 16-bit PCM for VOSK
        cmd_sox = [
            "sox", temp_wav,
            "-r", "16000", "-b", "16", "-c", "1",
            self.mono_wav
        ]
        subprocess.run(cmd_sox, check=True)
        print(f"[SOX] Converted to mono: {self.mono_wav}")
        
        # Optional: boost volume
        cmd_gain = [
            "sox", self.mono_wav,
            self.mono_wav,
            "gain", "10"
        ]
        subprocess.run(cmd_gain, check=True)
        print(f"[SOX] Volume boosted: {self.mono_wav}")




    # --------------------------------------------------
    def stt(self):
        print("[STT] Running VOSK...")
        text = get_text(self.mono_wav)
        print(f"[STT] Recognized text: {text}")   # <-- add this line
        return text
        


