import asyncio
import websockets
import json
import base64
import os
import numpy as np
import whisperx
import torch
from datetime import datetime

class RecallAudioReceiver:
    def __init__(self, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self.output_dir = './audio_output'
        self.transcripts_dir = './transcripts'
        
        # Create output directories if they don't exist
        for dir_path in [self.output_dir, self.transcripts_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Initialize WhisperX
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.batch_size = 16
        self.compute_type = "float16" if torch.cuda.is_available() else "int8"
        
        # Load WhisperX model
        print("Loading WhisperX model...")
        self.model = whisperx.load_model("base.en", self.device, compute_type=self.compute_type)
        print("WhisperX model loaded successfully")
        
        # Audio buffering for 10-second transcription
        self.audio_buffers = {}  # Store audio chunks per recording
        self.buffer_duration = 10.0  # Transcribe every 10 seconds
        self.sample_rate = 16000
        self.target_samples = int(self.sample_rate * self.buffer_duration)  # 160,000 samples for 10 seconds
    
    async def handle_message(self, websocket, path):
        """Handle incoming WebSocket messages"""
        print(f"Client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    # Parse the JSON message
                    ws_message = json.loads(message)
                    
                    if ws_message.get('event') == 'audio_mixed_raw.data':
                        await self.process_audio_data(ws_message)
                    else:
                        print(f"Unhandled message event: {ws_message.get('event')}")
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    async def process_audio_data(self, ws_message):
        """Process incoming audio data"""
        try:
            data = ws_message['data']
            recording_id = data['recording']['id']
            buffer_data = data['data']['buffer']
            timestamp = data['data']['timestamp']
            
            print(f"Received audio data for recording: {recording_id}")
            print(f"Timestamp - Relative: {timestamp['relative']}, Absolute: {timestamp['absolute']}")
            
            # Decode the base64 audio data
            encoded_buffer = base64.b64decode(buffer_data)
            
            # Convert raw PCM to numpy array for WhisperX
            # Recall.ai sends 16-bit PCM, mono, 16kHz
            audio_array = np.frombuffer(encoded_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Initialize buffer for this recording if it doesn't exist
            if recording_id not in self.audio_buffers:
                self.audio_buffers[recording_id] = {
                    'chunks': [],
                    'total_samples': 0,
                    'last_timestamp': timestamp
                }
            
            # Add audio chunk to buffer
            self.audio_buffers[recording_id]['chunks'].append(audio_array)
            self.audio_buffers[recording_id]['total_samples'] += len(audio_array)
            self.audio_buffers[recording_id]['last_timestamp'] = timestamp
            
            # Check if we have 10 seconds of audio
            if self.audio_buffers[recording_id]['total_samples'] >= self.target_samples:
                await self.transcribe_accumulated_audio(recording_id)
            
            # Write to file (append mode to collect all audio chunks)
            file_path = os.path.join(self.output_dir, f"{recording_id}.bin")
            with open(file_path, 'ab') as f:
                f.write(encoded_buffer)
            
            print(f"Audio data written to: {file_path} (Buffer: {self.audio_buffers[recording_id]['total_samples']}/{self.target_samples} samples)")
            
        except KeyError as e:
            print(f"Missing key in message data: {e}")
        except Exception as e:
            print(f"Error processing audio data: {e}")
    
    async def transcribe_accumulated_audio(self, recording_id):
        """Transcribe 10 seconds of accumulated audio"""
        try:
            buffer_info = self.audio_buffers[recording_id]
            
            # Combine all audio chunks
            combined_audio = np.concatenate(buffer_info['chunks'])
            
            # Take exactly 10 seconds (160,000 samples)
            audio_to_transcribe = combined_audio[:self.target_samples]
            
            print(f"Transcribing {len(audio_to_transcribe)/self.sample_rate:.1f} seconds of audio for recording: {recording_id}")
            
            # Run transcription in a thread to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.model.transcribe, audio_to_transcribe, self.batch_size
            )
            
            if result["segments"]:
                transcript_text = " ".join([segment["text"] for segment in result["segments"]])
                
                # Save transcript with timestamp
                transcript_entry = {
                    "recording_id": recording_id,
                    "timestamp": buffer_info['last_timestamp'],
                    "duration_seconds": 10.0,
                    "transcript": transcript_text,
                    "segments": result["segments"]
                }
                
                # Append to transcript file
                transcript_file = os.path.join(self.transcripts_dir, f"{recording_id}_transcript.jsonl")
                with open(transcript_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(transcript_entry, ensure_ascii=False) + '\n')
                
                print(f"✅ 10-second Transcription: {transcript_text}")
            else:
                print("No speech detected in 10-second audio chunk")
            
            # Keep remaining audio for next transcription
            remaining_audio = combined_audio[self.target_samples:]
            self.audio_buffers[recording_id] = {
                'chunks': [remaining_audio] if len(remaining_audio) > 0 else [],
                'total_samples': len(remaining_audio),
                'last_timestamp': buffer_info['last_timestamp']
            }
            
        except Exception as e:
            print(f"Error in 10-second transcription: {e}")
    
    async def transcribe_audio_chunk(self, audio_array, recording_id, timestamp):
        """Legacy method - now handled by transcribe_accumulated_audio"""
        pass
    
    async def start_server(self):
        """Start the WebSocket server"""
        print(f"Starting WebSocket server on {self.host}:{self.port}")
        print(f"Audio files will be saved to: {self.output_dir}")
        print(f"Transcripts will be saved to: {self.transcripts_dir}")
        print(f"🎙️  Transcribing every {self.buffer_duration} seconds of audio")
        print("\nTo convert audio files to MP3, use:")
        print("ffmpeg -f s16le -ar 16000 -ac 1 -i ./audio_output/{RECORDING_ID}.bin -c:a libmp3lame -q:a 2 ./audio_output/{RECORDING_ID}.mp3")
        
        async with websockets.serve(self.handle_message, self.host, self.port):
            print(f"WebSocket server is running on ws://{self.host}:{self.port}")
            # Keep the server running
            await asyncio.Future()  # Run forever

async def main():
    """Main function to run the WebSocket receiver"""
    receiver = RecallAudioReceiver()
    
    try:
        await receiver.start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    # Install required packages if not already installed:
    # pip install websockets
    
    print("Recall.ai Audio WebSocket Receiver")
    print("=" * 40)
    asyncio.run(main())