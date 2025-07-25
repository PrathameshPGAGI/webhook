from fastapi import FastAPI, Request
import uvicorn
import os, asyncio, base64, aiohttp
from gtts import gTTS
import io
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

RECALL_API_KEY = os.getenv('RECALL_API_KEY')
RECALL_BASE = "https://us-west-2.recall.ai/api/v1"

@app.post("/join_meet")
async def join_meet(
    request: Request
):
    body = await request.json()
    meeting_url = body.get("meeting_url")
    if not meeting_url:
        return {"error": "meeting_url is required"}

    async def run_bot(meeting_url):
        headers = {"Authorization": f"Token {RECALL_API_KEY}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            silent_mp3 = base64.b64encode(b'\x00'*1000).decode()
            cfg = {
                "bot_name": "VoiceBot",
                "meeting_url": meeting_url,
                "automatic_audio_output": {
                    "in_call_recording": {
                        "data": {"kind": "mp3", "b64_data": silent_mp3}
                    }
                },
                "recording_config": {
                    "transcript": {
                        "provider": {
                            "deepgram_streaming": {}
                        }
                    },
                    "realtime_endpoints": [
                        {
                            "type": "webhook",
                            "url": "https://webhook-vt1r.onrender.com/transcript",
                            "events": ["transcript.data", "transcript.partial_data"]
                        }
                    ]
                }
            }
            r = await session.post(f"{RECALL_BASE}/bot", json=cfg, headers=headers)
            r.raise_for_status()
            bot_id = (await r.json())["id"]
            print("Bot created:", bot_id)

            # Wait until bot joins meeting
            for _ in range(20):
                await asyncio.sleep(3)
                st = await session.get(f"{RECALL_BASE}/bot/{bot_id}", headers=headers)
                js = await st.json()
                if js.get("status_changes") and js["status_changes"][-1]["code"]=="in_call_recording":
                    break
            print("Bot joined")

            # Play TTS into Google Meet
            text = 'Toing bot is turned on.'
            tts = gTTS(text=text, lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_bytes = audio_buffer.getvalue()
            b64_audio = base64.b64encode(audio_bytes).decode()
            payload = {"kind":"mp3", "b64_data": b64_audio}
            out = await session.post(f"{RECALL_BASE}/bot/{bot_id}/output_audio/", json=payload, headers=headers)
            if out.status == 200:
                print("✅ TTS audio played!")
            else:
                print("Playback failed:", await out.text())

    asyncio.create_task(run_bot(meeting_url))
    return {"status": "Bot joining the meeting", "meeting_url": meeting_url}


@app.post("/transcript")
async def recall_webhook(request: Request):
    data = await request.json()
    # Extract participant name
    participant = data["data"]["data"]["participant"].get("name", "Unknown")
    # Extract spoken words and join them
    words = data["data"]["data"]["words"]
    spoken_text = " ".join([w["text"] for w in words])
    print(f"{participant} said: {spoken_text}")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)