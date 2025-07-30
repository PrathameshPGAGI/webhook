# Recall.ai Meeting Bot

A FastAPI-based application that integrates with Recall.ai to join Google Meet calls, record audio streams, and provide text-to-speech functionality.

## Features

- 🤖 **Automated Meeting Bot**: Join Google Meet calls programmatically
- 🎵 **Real-time Audio Recording**: Stream and store audio data in MongoDB
- 🗣️ **Text-to-Speech**: Play AI-generated speech in meetings
- 💾 **Audio Export**: Download recorded meeting audio as WAV files
- 🔗 **WebSocket Integration**: Real-time audio data streaming

## Prerequisites

- Python 3.8+
- MongoDB database
- Recall.ai API key
- Required Python packages (see requirements.txt)

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd recall.ai
```

2. **Install dependencies**
```bash
pip install fastapi uvicorn requests numpy wave pymongo python-dotenv gtts aiohttp
```

3. **Set up environment variables**
Create a `.env` file in the project root:
```env
RECALL_API_KEY=your_recall_api_key_here
MONGO_URI=mongodb://localhost:27017/
```

4. **Start MongoDB**
Ensure MongoDB is running on your system.

## Usage

### Starting the Server

```bash
python server.py
```

The server will start on `http://localhost:5000` with the following endpoints:

### API Endpoints

#### 1. Join Meeting
```http
POST /join_meet
Content-Type: application/json

{
    "meeting_url": "https://meet.google.com/xxx-xxxx-xxx"
}
```

**Response:**
```json
{
    "status": "Bot joined the meeting",
    "bot_id": "bot_12345"
}
```

#### 2. Play Audio (Text-to-Speech)
```http
POST /play_audio
Content-Type: application/json

{
    "text": "Hello everyone, this is an AI assistant",
    "bot_id": "bot_12345"
}
```

#### 3. Get Recorded Audio
```http
GET /audio/{bot_id}
```

Returns combined audio data for the specified bot in base64 format.

#### 4. WebSocket Audio Stream
```
ws://localhost:5000/ws
```

Real-time audio data streaming endpoint.

### Audio Export Tool

Use the `audiosaver.py` script to download and save meeting audio:

```bash
python audiosaver.py
```

The script will:
1. Prompt for a bot_id
2. Fetch audio data from the server
3. Convert to WAV format
4. Save as `meeting_audio_{bot_id}.wav`

## Project Structure

```
recall.ai/
├── server.py          # Main FastAPI server
├── audiosaver.py      # Audio export utility
├── README.md          # This file
└── .env              # Environment variables (create this)
```

## Configuration

### Audio Settings
- **Sample Rate**: 16 kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit PCM
- **Format**: WAV for exports, base64 for API transfers

### MongoDB Schema
Audio data is stored in the `meetingbooking.audiostreams` collection:
```json
{
    "bot_id": "string",
    "buffer": "base64_audio_data",
    "timestamp": "iso_timestamp"
}
```

## Audio Quality Analysis

The audio export tool provides detailed analysis:
- **Amplitude Analysis**: Max and average audio levels
- **Duration Verification**: Compares expected vs actual audio length
- **Data Integrity**: Checks for silent or corrupted audio
- **Quality Warnings**: Alerts for potential audio issues

## Error Handling

The application includes comprehensive error handling for:
- Network connectivity issues
- Invalid audio data
- MongoDB connection problems
- Recall.ai API errors
- WebSocket disconnections

## Development

### Running in Development Mode
```bash
python server.py
```
The server runs with auto-reload enabled for development.

### Testing Audio Export
```bash
python audiosaver.py
```
Enter a valid bot_id when prompted to test audio retrieval.

## Troubleshooting

### Common Issues

1. **Bot fails to join meeting**
   - Verify Recall.ai API key
   - Check meeting URL format
   - Ensure meeting is accessible

2. **No audio data**
   - Verify WebSocket connection
   - Check MongoDB connectivity
   - Confirm bot is recording

3. **Audio quality issues**
   - Check network stability
   - Verify audio codec settings
   - Monitor amplitude levels in export tool

4. **Silent audio output**
   - Verify microphone permissions in the meeting
   - Check participant audio levels
   - Ensure bot has recording permissions

## API Dependencies

- **Recall.ai**: Meeting bot integration and audio recording
- **MongoDB**: Audio data storage
- **Google TTS**: Text-to-speech generation
- **FastAPI**: Web framework
- **WebSocket**: Real-time communication

