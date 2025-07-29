import asyncio
import argparse
import os
import sys
from typing import Dict, Any
from datetime import datetime
import logging
import json
import base64
import tempfile
import numpy as np
import torch
import whisperx
import soundfile as sf
import websockets
from websockets.server import serve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriptionServer:
    def __init__(self, port: int = 3456, model_name: str = "base.en", device: str = None):
        self.port = port
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.align_model = None
        self.metadata = None
        self.clients = set()
        
        # Audio configuration
        self.sample_rate = 16000  # 16 kHz as specified in the API
        self.channels = 1  # Mono
        self.sample_width = 2  # 16-bit = 2 bytes
        
        logger.info(f"Initializing server on port {port} with device: {self.device}")
        
    async def initialize_whisperx(self):
        """Initialize WhisperX model and alignment model"""
        try:
            logger.info(f"Loading WhisperX model: {self.model_name}")
            self.model = whisperx.load_model(self.model_name, self.device, compute_type="float16" if self.device == "cuda" else "int8")
            
            # Load alignment model
            logger.info("Loading alignment model...")
            self.align_model, self.metadata = whisperx.load_align_model(language_code="en", device=self.device)
            
            logger.info("WhisperX models loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing WhisperX: {e}")
            raise
    
    def process_audio_buffer(self, audio_buffer: bytes) -> np.ndarray:
        """Convert raw audio buffer to numpy array suitable for WhisperX"""
        try:
            # Convert bytes to numpy array (16-bit signed little-endian PCM)
            audio_array = np.frombuffer(audio_buffer, dtype=np.int16)
            
            # Convert to float32 and normalize to [-1, 1] range
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            return audio_float
            
        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")
            return np.array([])
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using WhisperX"""
        try:
            if len(audio_data) == 0:
                return ""
            
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write audio data to temporary file
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe with WhisperX
                result = self.model.transcribe(temp_file_path, batch_size=16)
                
                # Align the transcription
                if self.align_model and len(result["segments"]) > 0:
                    result = whisperx.align(result["segments"], self.align_model, self.metadata, temp_file_path, self.device, return_char_alignments=False)
                
                # Extract text from segments
                transcript = ""
                if "segments" in result:
                    for segment in result["segments"]:
                        if "text" in segment:
                            transcript += segment["text"] + " "
                
                return transcript.strip()
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    async def handle_audio_message(self, message_data: Dict[str, Any]):
        """Handle incoming audio message and transcribe it"""
        try:
            if message_data.get("event") == "audio_mixed_raw.data":
                # Extract audio data
                buffer_b64 = message_data["data"]["data"]["buffer"]
                timestamp = message_data["data"]["data"]["timestamp"]
                recording_id = message_data["data"]["recording"]["id"]
                bot_id = message_data["data"]["bot"]["id"]
                
                # Decode base64 audio data
                audio_buffer = base64.b64decode(buffer_b64)
                
                # Process audio buffer
                audio_array = self.process_audio_buffer(audio_buffer)
                
                # Only transcribe if we have sufficient audio data
                if len(audio_array) > self.sample_rate * 0.5:  # At least 0.5 seconds of audio
                    transcript = await self.transcribe_audio(audio_array)
                    
                    if transcript:
                        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        logger.info(f"[{timestamp_str}] Recording ID: {recording_id}")
                        logger.info(f"[{timestamp_str}] Bot ID: {bot_id}")
                        logger.info(f"[{timestamp_str}] Relative Timestamp: {timestamp.get('relative', 'N/A')}")
                        logger.info(f"[{timestamp_str}] TRANSCRIPT: {transcript}")
                        print(f"\n{'='*60}")
                        print(f"RECORDING: {recording_id}")
                        print(f"TIMESTAMP: {timestamp_str}")
                        print(f"TRANSCRIPT: {transcript}")
                        print(f"{'='*60}\n")
                
        except Exception as e:
            logger.error(f"Error handling audio message: {e}")
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        client_address = websocket.remote_address
        logger.info(f"New client connected: {client_address}")
        
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    # Parse JSON message
                    message_data = json.loads(message)
                    
                    # Handle different message types
                    if message_data.get("event") == "audio_mixed_raw.data":
                        await self.handle_audio_message(message_data)
                    else:
                        logger.info(f"Received message: {message_data.get('event', 'unknown')}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_address}")
        except Exception as e:
            logger.error(f"Error with client {client_address}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            # Initialize WhisperX models
            await self.initialize_whisperx()
            
            logger.info(f"Starting WebSocket server on port {self.port}")
            async with serve(self.handle_client, "0.0.0.0", self.port):
                logger.info(f"WebSocket server is running on ws://0.0.0.0:{self.port}")
                logger.info("Server is ready to receive audio streams from Recall.ai")
                await asyncio.Future()  # Run forever
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Audio Transcription WebSocket Server")
    parser.add_argument("--port", type=int, default=None, help="Port to run the server on")
    parser.add_argument("--model", type=str, default="base.en", help="WhisperX model to use")
    parser.add_argument("--device", type=str, default=None, help="Device to use (cpu/cuda)")
    
    args = parser.parse_args()
    
    # Use environment variable PORT if available (for Render deployment)
    port = args.port or int(os.getenv("PORT", 3456))
    
    server = AudioTranscriptionServer(
        port=port,
        model_name=args.model,
        device=args.device
    )
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
