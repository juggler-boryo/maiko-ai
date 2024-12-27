from __future__ import annotations

import base64
import asyncio
import json
import os
from typing import Any, cast
import numpy as np
from src.audio_util import CHANNELS, SAMPLE_RATE, AudioPlayerAsync
from src.function_dict import get_tools, exec_tool
from openai import AsyncOpenAI
from openai.types.beta.realtime.session import Session
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

# when user + ai are silent for 5 seconds, exit for api cost reduction
SILENCE_SECONDS = 5
RMS_THRESHOLD = 50

class RealtimeApp:
    def __init__(self) -> None:
        self.connection = None
        self.session = None
        self.client = AsyncOpenAI(api_key=self._load_access_key("credentials/maiko-ai/openai.json"))
        self.audio_player = AudioPlayerAsync()
        self.last_audio_item_id = None
        self.should_send_audio = asyncio.Event()
        self.connected = asyncio.Event()
        self.is_recording = False
        self.silence_detected = False
        self.silence_start_time = None
        

    def _load_access_key(self, credentials_path: str) -> str:
        try:
            with open(credentials_path, "r") as f:
                return json.load(f)["ACCESS_KEY"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to load access key from {credentials_path}: {e}"
            )

    async def handle_realtime_connection(self) -> None:
        async with self.client.beta.realtime.connect(
                model="gpt-4o-mini-realtime-preview-2024-12-17",
            ) as conn:
            self.connection = conn
            self.connected.set()
            print("Connected to realtime session")
            await conn.session.update(session={
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                    "create_response": True
                },
                "voice": "sage",
                "tools": get_tools(), 
                "tool_choice": "auto",
            })
            acc_items: dict[str, Any] = {}

            async for event in conn:
                if event.type == "session.created":
                    self.session = event.session
                    print(f"Session created with ID: {event.session.id}")
                    continue

                if event.type == "session.updated":
                    self.session = event.session
                    print("Session updated")
                    continue

                if event.type == "response.audio.delta":
                    if event.item_id != self.last_audio_item_id:
                        self.audio_player.reset_frame_count()
                        self.last_audio_item_id = event.item_id

                    bytes_data = base64.b64decode(event.delta)
                    self.audio_player.add_data(bytes_data)
                    continue

                if event.type == "response.audio_transcript.delta":
                    try:
                        text = acc_items[event.item_id]
                    except KeyError:
                        acc_items[event.item_id] = event.delta
                    else:
                        acc_items[event.item_id] = text + event.delta

                    print(f"\rTranscript: {acc_items[event.item_id]}")
                    # self.audio_player.clear_data()
                    continue

                if event.type == "response.output_item.done":
                    item = event.item
                    print(item)
                    if item.type == "function_call":
                        function_name = item.name
                        call_id = item.call_id
                        arguments_str = item.arguments
                        try:
                            arguments = json.loads(arguments_str)
                        except json.JSONDecodeError:
                            arguments = {}

                        result = exec_tool(function_name, arguments)

                        # TODO: 死んでる
                        await conn.conversation.create(item={
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps(result, ensure_ascii=False)
                        })
                        await conn.response.create()

    async def _get_connection(self) -> AsyncRealtimeConnection:
        await self.connected.wait()
        assert self.connection is not None
        return self.connection

    async def send_mic_audio(self) -> None:
        import sounddevice as sd

        sent_audio = False
        device_info = sd.query_devices()
        print("Available audio devices:")
        print(device_info)

        read_size = int(SAMPLE_RATE * 0.02)

        input_device_index = int(input("Enter the index of the input device: "))

        stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype="int16",
            device=input_device_index
        )
        stream.start()

        try:
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0)
                    continue

                await self.should_send_audio.wait()
                if not self.is_recording:
                    print("🔴 Recording started...")
                    self.is_recording = True

                data, _ = stream.read(read_size)

                connection = await self._get_connection()
                if not sent_audio:
                    asyncio.create_task(connection.send({"type": "response.cancel"}))
                    sent_audio = True

                await connection.input_audio_buffer.append(audio=base64.b64encode(cast(Any, data)).decode("utf-8"))
                await asyncio.sleep(0)
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_data)))
                silence_threshold = RMS_THRESHOLD

                if len(self.audio_player.queue) > 0:
                    self.silence_detected = False
                    self.silence_start_time = None
                    continue
                
                if rms < silence_threshold:
                    if not self.silence_detected:
                        self.silence_detected = True
                        self.silence_start_time = asyncio.get_event_loop().time()
                    else:
                        if asyncio.get_event_loop().time() - self.silence_start_time > SILENCE_SECONDS:
                            print(f"{SILENCE_SECONDS} seconds of silence detected, exiting...")
                            os._exit(1)
                else:
                    self.silence_detected = False

        except KeyboardInterrupt:
            print("\nRecording stopped")
        finally:
            stream.stop()
            stream.close()

    async def run(self):
        print("Starting realtime conversation...")
        print("Press Ctrl+C to stop recording and exit")
        
        tasks = [
            asyncio.create_task(self.handle_realtime_connection()),
            asyncio.create_task(self.send_mic_audio())
        ]
        
        self.should_send_audio.set()  # Start recording immediately
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    app = RealtimeApp()
    asyncio.run(app.run())
