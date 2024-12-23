#!/usr/bin/env python3
import json
import os
import struct
import pyaudio
import pvporcupine
import threading
import winsound
import signal
from typing import Optional


class VoiceAssistant:
    def __init__(self):
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.running = True

        # Setup clean shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _load_access_key(self, credentials_path: str) -> str:
        try:
            with open(credentials_path, "r") as f:
                return json.load(f)["ACCESS_KEY"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to load access key from {credentials_path}: {e}"
            )

    def _handle_shutdown(self, *args) -> None:
        self.running = False
        self.cleanup_resources()

    def _cleanup_audio(self) -> None:
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self.pa:
            self.pa.terminate()
            self.pa = None

    def initialize_audio(self) -> None:
        self._cleanup_audio()
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
            stream_callback=None,
        )

    def cleanup_resources(self) -> None:
        self._cleanup_audio()
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

    def play_sound(self) -> None:
        try:
            if os.name == "nt":
                winsound.PlaySound("./sounds/yoo.wav", winsound.SND_FILENAME)
            else:
                from playsound import playsound

                playsound("./sounds/yoo.mp3")
        except Exception as e:
            print(f"Failed to play sound: {e}")

    def run(self) -> None:
        try:
            access_key = self._load_access_key("credentials/maiko-ai/picovoice.json")
            model_suffix = "win" if os.name == "nt" else "mac"
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[f"models/mmaiko_ja_{model_suffix}.ppn"],
                sensitivities=[0.5],
                model_path=f"models/mmaiko_ja_{model_suffix}.pv",
            )

            self.initialize_audio()

            print("running")

            while self.running:
                try:
                    pcm = self.audio_stream.read(self.porcupine.frame_length)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                    if self.porcupine.process(pcm) >= 0:
                        threading.Thread(target=self.play_sound, daemon=True).start()

                except (IOError, OSError) as e:
                    print(f"Audio stream error: {e}")
                    self.initialize_audio()
                    continue

        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            self.cleanup_resources()


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
