import json
import wave
from vosk import Model, KaldiRecognizer

import json
import wave
from vosk import Model, KaldiRecognizer

# Load model ONCE
model = Model("vosk-model-small-en-us-0.15")

def audio_text(wav_path: str) -> str:
    """
    Convert .wav (mono, 16-bit PCM, 16kHz) to plaintext
    """

    wf = wave.open(wav_path, "rb")

    if wf.getnchannels() != 1:
        raise ValueError("Audio needs to be mono")
    if wf.getsampwidth() != 2:
        raise ValueError("Audio must be 16bit PCM")
    if wf.getframerate() != 16000:
        raise ValueError("Audio must be 16kHz")

    rec = KaldiRecognizer(model, 16000)

    while True:
        data = wf.readframes(4000)
        if not data:
            break
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    return result.get("text", "")

    # microphone set up 
    """
    GND Pin6
    VDD Pin1
    SD Pin38 GPIO20

    L/R GND
    SM Pin35 GPIO19 
    SCK Pin12 GPIO180
    """
    # command in terminal to record the audio 
    # arecord -D plughw:3,0 -r16000 -f S16_LE -d10 test.wav

    # command of how to use the function in  terminal 
    # cd ~
    # source stt-env/bin/activate
    # python3 -c "from stt import audio_text; print(audio_text('testaudio_16000_test01_20s.wav', 'vosk-model-small-en-us-0.15'))"
    # python3 -c "from stt import audio_text; print(audio_text('test.wav', 'vosk-model-small-en-us-0.15'))"


    #one microphoe pass
    #arecord -D plughw:3,0 -c2 -r 48000 -f S32_LE -t wav -V stereo -v test_stereo.wav
    #sox test_stereo.wav -r 16000 -c 1 -b 16 test16.wav remix 1
    # python3 -c "from stt import audio_text; print(audio_text('test16.wav', 'vosk-model-small-en-us-0.15'))""

    # two microphone
    print(audio_text("command.wav"))