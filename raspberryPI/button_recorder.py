from gpiozero import Button
from signal import pause
from stt import get_text
import subprocess
import time
import sys

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

        self.record_stereo_audio()
        self.convert_to_mono()
        self.script = self.stt()

    # --------------------------------------------------
    def record_stereo_audio(self):
        print("[REC] Recording...")
        cmd = [
            "arecord", "-D", self.device,
            "-c", "2", "-r", "48000",
            "-f", "S32_LE", "-t", "wav",
            "-d", str(self.duration),
            self.stereo_wav
        ]
        subprocess.run(cmd, check=True)
        print(f"[REC] Saved: {self.stereo_wav}")

    # --------------------------------------------------
    def convert_to_mono(self):
        print("[SOX] Converting to mono...")
        cmd = [
            "sox", self.stereo_wav,
            "-r", "16000",
            "-c", "1",
            "-b", "16",
            self.mono_wav,
            "remix", "1"
        ]
        subprocess.run(cmd, check=True)
        print(f"[SOX] Saved: {self.mono_wav}")

    # --------------------------------------------------
    def stt(self):
        print("[STT] Running VOSK...")
        text = get_text(self.mono_wav)
        return text
        


