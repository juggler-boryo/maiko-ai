#!/usr/bin/env python3
import json
import struct
import pyaudio
import pvporcupine
import threading
from playsound import playsound
import threading
import signal
from typing import Optional

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface


class VoiceAssistant:
    def __init__(self):
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.conversation: Optional[Conversation] = None
        self.client: Optional[ElevenLabs] = None
        self.running = True
        
        # Initialize ElevenLabs client
        self._setup_elevenlabs()
        
        # Setup clean shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _load_access_key(self, credentials_path: str) -> str:
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)['ACCESS_KEY']
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load access key from {credentials_path}: {e}")

    def _setup_elevenlabs(self) -> None:
        self.client = ElevenLabs(api_key=self._load_access_key('credentials/maiko-ai/elevenlabs.json'))
        
    def _handle_shutdown(self, *args) -> None:
        self.running = False
        self.end_conversation()
        self.cleanup_resources()
        
    def start_conversation(self) -> None:
        self._cleanup_audio()
            
        self.conversation = Conversation(
            self.client,
            "5U8wP5flTL2jwkmjtkKO",
            requires_auth=False,
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=lambda response: print(f"Agent: {response}"),
            callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
            callback_user_transcript=lambda transcript: print(f"User: {transcript}"),
            callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
        )
        
        self.conversation.start_session()
        signal.signal(signal.SIGINT, lambda sig, frame: self.conversation.end_session())
        conversation_id = self.conversation.wait_for_session_end()
        print(f"Conversation ID: {conversation_id}")
        
        self.initialize_audio()

    def end_conversation(self) -> None:
        if self.conversation:
            self.conversation.end_session()
            self.conversation = None

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
            stream_callback=None
        )

    def cleanup_resources(self) -> None:
        self._cleanup_audio()
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

    def play_sound(self) -> None:
        try:
            playsound('yoo.mp3')
        except Exception as e:
            print(f"Failed to play sound: {e}")

    def run(self) -> None:
        try:
            access_key = self._load_access_key('credentials/maiko-ai/picovoice.json')
            
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=['maiko_ja_mac.ppn'],
                sensitivities=[0.5],
                model_path="porcupine_params_ja.pv"
            )

            self.initialize_audio()

            print("running")
            
            while self.running:
                try:
                    pcm = self.audio_stream.read(self.porcupine.frame_length)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                    if self.porcupine.process(pcm) >= 0:
                        threading.Thread(target=self.play_sound, daemon=True).start()
                        self.start_conversation()
                        if not self.running:
                            break
                        self.initialize_audio()
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
