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

        self.record_in_mono()
        self.script = self.stt()

    # --------------------------------------------------
    def record_in_mono(self):
        print("[REC] Recording mono audio...")
        cmd_record = [
            "arecord", "-D", self.device,
            "-c", "1",          # mono
            "-r", "16000",      # 16 kHz for VOSK
            "-f", "S16_LE",     # 16-bit PCM
            "-t", "wav",
            "-d", str(self.duration),
            self.mono_wav
        ]
        subprocess.run(cmd_record, check=True)  # waits until done
        print(f"[REC] Saved: {self.mono_wav}")

        # Optional: boost volume safely
        cmd_gain = [
            "sox", self.mono_wav,
            self.mono_wav,
            "gain", "10"
        ]
        subprocess.run(cmd_gain, check=True)  # waits until done
        print(f"[SOX] Volume boosted: {self.mono_wav}")
        time.sleep(2)



    # --------------------------------------------------
    def stt(self):
        print("[STT] Running VOSK...")
        text = get_text(self.mono_wav)
        return text
        


