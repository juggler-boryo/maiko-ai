from __future__ import annotations

import base64
import asyncio
import json
from typing import Any, cast

from src.audio_util import CHANNELS, SAMPLE_RATE, AudioPlayerAsync
from openai import AsyncOpenAI
from openai.types.beta.realtime.session import Session
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

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

    def _load_access_key(self, credentials_path: str) -> str:
        try:
            with open(credentials_path, "r") as f:
                return json.load(f)["ACCESS_KEY"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to load access key from {credentials_path}: {e}"
            )

    async def handle_realtime_connection(self) -> None:
        async with self.client.beta.realtime.connect(model="gpt-4o-mini-realtime-preview-2024-12-17") as conn:
            self.connection = conn
            self.connected.set()
            print("Connected to realtime session")

            await conn.session.update(session={"turn_detection": {"type": "server_vad"}})
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

                    print(f"\rTranscript: {acc_items[event.item_id]}", end="", flush=True)
                    continue

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

        stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype="int16",
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
