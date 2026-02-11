import sys
import wave
import json
import numpy as np
from vosk import Model, KaldiRecognizer

MODEL_PATH = "vosk-model-small-en-us-0.15"

def speech_to_text(wav_file: str) -> str:
    wf = wave.open(wav_file, "rb")
    if wf.getnchannels() != 1:
        raise ValueError("Audio needs to be mono")
    if wf.getsampwidth() != 2:
        raise ValueError("Audio must be 16bit PCM")
    if wf.getframerate() != 16000:
        raise ValueError("Audio must be 16kHz")
    

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, wf.getframerate())
    
    result_text = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result.get("text"):
                result_text.append(result["text"])
    final = json.loads(recognizer.FinalResult())
    if final.get("text"):
        result_text.append(final["text"])
    return " ".join(result_text)

def main():
    if len(sys.argv) !=2:
        print("Usage: python stt.py <wav_file>")
        sys.exit(1)
    wav_file = sys.argv[1]
    print(f"[STT] Processing {wav_file}")
    text = speech_to_text(wav_file)
    print("[STT Recognized text: ]")
    print(text)
    
if __name__ == "__main__":
    main()
                 











# def audio_text(wav_path, model_path):
# 	wf = wave.open(wav_path, "rb")
# 	model = Model("vosk-model-small-en-us-0.15")
# 	rec = KaldiRecognizer(model, wf.getframerate())
# 	while True:
# 		data = wf.readframes(4000)
# 		if len(data) == 0:
# 			break
# 		rec.AcceptWaveform(data)
# 	result = json.loads(rec.FinalResult())
# 	return "[RESULT] " + result.get("text", "")
