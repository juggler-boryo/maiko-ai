#!/usr/bin/env python3
import json
import struct
import pyaudio
import pvporcupine
from typing import Optional

def load_access_key(credentials_path: str) -> str:
    """Load Picovoice access key from credentials file."""
    with open(credentials_path, 'r') as f:
        credentials = json.load(f)
        return credentials['ACCESS_KEY']

def initialize_audio(porcupine: pvporcupine.Porcupine) -> tuple[pyaudio.PyAudio, pyaudio.Stream]:
    """Initialize PyAudio and open audio stream."""
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    return pa, audio_stream

def cleanup_resources(porcupine: Optional[pvporcupine.Porcupine] = None,
                     audio_stream: Optional[pyaudio.Stream] = None,
                     pa: Optional[pyaudio.PyAudio] = None) -> None:
    """Cleanup and release audio resources."""
    if porcupine:
        porcupine.delete()
    if audio_stream:
        audio_stream.close()
    if pa:
        pa.terminate()

def main():
    porcupine = None
    pa = None
    audio_stream = None
    
    try:
        access_key = load_access_key('credentials/maiko-ai/picovoice.json')
        
        # Initialize Porcupine
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=['hey-maiko_en_mac_v3_0_0.ppn'],
            sensitivities=[0.5]
        )

        # Initialize audio
        pa, audio_stream = initialize_audio(porcupine)

        # Main detection loop
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            if porcupine.process(pcm) >= 0:
                print("Detected keyword")

    finally:
        cleanup_resources(porcupine, audio_stream, pa)

if __name__ == "__main__":
    main()
