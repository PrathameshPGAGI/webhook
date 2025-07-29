#!/usr/bin/env python3
"""
Test script for the Audio Transcription WebSocket Server

This script simulates sending audio data to test the transcription functionality.
"""

import asyncio
import websockets
import json
import base64
import wave
import numpy as np
from datetime import datetime

async def send_test_audio():
    """Send test audio data to the WebSocket server"""
    uri = "ws://localhost:3456"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Create some test audio data (silent audio for testing)
            sample_rate = 16000
            duration = 2.0  # 2 seconds
            samples = int(sample_rate * duration)
            
            # Generate a simple sine wave for testing (440 Hz tone)
            t = np.linspace(0, duration, samples, False)
            audio_data = np.sin(440 * 2 * np.pi * t) * 0.1  # Low volume
            
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # Encode as base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Create message in the format expected by the server
            message = {
                "event": "audio_mixed_raw.data",
                "data": {
                    "data": {
                        "buffer": audio_b64,
                        "timestamp": {
                            "relative": 0.0,
                            "absolute": datetime.now().isoformat()
                        }
                    },
                    "realtime_endpoint": {
                        "id": "test-endpoint-123",
                        "metadata": {}
                    },
                    "recording": {
                        "id": "test-recording-456",
                        "metadata": {}
                    },
                    "bot": {
                        "id": "test-bot-789",
                        "metadata": {}
                    },
                    "audio_mixed_raw": {
                        "id": "test-audio-000",
                        "metadata": {}
                    }
                }
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            print("Sent test audio data")
            
            # Wait a bit to see the response
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting test client...")
    asyncio.run(send_test_audio())
