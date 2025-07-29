# Audio Transcription WebSocket Server

This project contains a WebSocket server that receives real-time audio streams from Recall.ai bots and transcribes them using WhisperX.

## Features

- **Real-time Audio Processing**: Receives audio streams via WebSocket connections
- **WhisperX Transcription**: Uses state-of-the-art WhisperX for accurate speech-to-text conversion
- **Alignment Support**: Provides word-level alignment for better accuracy
- **Multi-device Support**: Runs on both CPU and GPU (CUDA)
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. For GPU support (optional but recommended):
```bash
# Install CUDA-compatible PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Usage

### Starting the Server

Run the WebSocket server:

```bash
python websocket.py
```

**Command line options:**
- `--port`: Port to run the server on (default: 3456)
- `--model`: WhisperX model to use - options: `tiny`, `base`, `small`, `medium`, `large` (default: base)
- `--device`: Device to use - `cuda` or `cpu` (auto-detected by default)

**Examples:**

```bash
# Start server on default port with base model
python websocket.py

# Start server on port 8080 with large model
python websocket.py --port 8080 --model large

# Force CPU usage
python websocket.py --device cpu
```

### Using with Recall.ai

1. **Start your WebSocket server** (as shown above)

2. **Expose your server publicly** using ngrok or similar:
```bash
ngrok http 3456
```

3. **Create a bot with real-time endpoint** using Recall.ai API:

```bash
curl --request POST \
     --url https://us-east-1.recall.ai/api/v1/bot/ \
     --header "Authorization: $RECALLAI_API_KEY" \
     --header "accept: application/json" \
     --header "content-type: application/json" \
     --data '{
       "meeting_url": "https://meet.google.com/your-meeting-id",
       "recording_config": {
         "audio_mixed_raw": {},
         "realtime_endpoints": [
           {
             "type": "websocket",
             "url": "wss://your-ngrok-domain.ngrok-free.app",
             "events": ["audio_mixed_raw.data"]
           }
         ]
       }
     }'
```

### Testing

Run the test script to simulate audio data:

```bash
python test_websocket.py
```

This will send test audio data to your running WebSocket server.

## Audio Format

The server expects audio in the following format:
- **Sample Rate**: 16 kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit signed little-endian PCM
- **Encoding**: Base64 encoded in the WebSocket message

## Message Format

The server expects messages in this format:

```json
{
  "event": "audio_mixed_raw.data",
  "data": {
    "data": {
      "buffer": "base64-encoded-audio-data",
      "timestamp": {
        "relative": 0.0,
        "absolute": "2023-12-01T10:00:00Z"
      }
    },
    "realtime_endpoint": {
      "id": "endpoint-id",
      "metadata": {}
    },
    "recording": {
      "id": "recording-id", 
      "metadata": {}
    },
    "bot": {
      "id": "bot-id",
      "metadata": {}
    },
    "audio_mixed_raw": {
      "id": "audio-id",
      "metadata": {}
    }
  }
}
```

## Output

The server will print transcriptions in real-time:

```
============================================================
RECORDING: rec_123456789
TIMESTAMP: 2023-12-01 10:30:15
TRANSCRIPT: Hello, this is a test transcription
============================================================
```

## Performance Notes

- **Model Selection**: 
  - `tiny`: Fastest, least accurate
  - `base`: Good balance of speed and accuracy (recommended)
  - `small`: Better accuracy, slower
  - `medium`: High accuracy, much slower
  - `large`: Best accuracy, slowest

- **GPU vs CPU**: GPU acceleration significantly improves performance, especially for larger models

- **Memory Usage**: Larger models require more memory. Monitor your system resources.

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**: Use a smaller model or switch to CPU
2. **Connection Issues**: Ensure the WebSocket server is running and accessible
3. **Audio Quality**: Poor transcription quality may indicate audio encoding issues

### Debugging

Enable debug logging by modifying the logging level in `websocket.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

Key dependencies include:
- `websockets`: WebSocket server implementation
- `whisperx`: Advanced speech recognition
- `torch`: PyTorch for deep learning
- `numpy`: Numerical computations
- `soundfile`: Audio file I/O

See `requirements.txt` for the complete list.

## License

This project is provided as-is for demonstration purposes.
