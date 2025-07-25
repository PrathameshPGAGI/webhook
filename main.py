import os, asyncio, base64
import aiohttp
from gtts import gTTS
import io

RECALL_API_KEY = '6e40b90d3fe483ed5191535e8dcc258cad4af54f'
RECALL_BASE = "https://us-west-2.recall.ai/api/v1"
MEETING_URL = "https://meet.google.com/rki-hymc-xmb"

async def main():
    headers = {"Authorization": f"Token {RECALL_API_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        # 1️⃣ Create bot with silent MP3
        silent_mp3 = base64.b64encode(b'\x00'*1000).decode()
        cfg = {
          "bot_name": "VoiceBot",
          "meeting_url": MEETING_URL,
          "automatic_audio_output": {
            "in_call_recording": {
              "data": {"kind": "mp3", "b64_data": silent_mp3}
            }
          },
          "recording_config": {
            "transcript": {
              "provider": {
                "assembly_ai_streaming": {}
              }
            },
            "realtime_endpoints": [
              {
                "type": "webhook",
                "url": "https://your-server.com/api/webhook/recall/transcript",  # <-- Replace with your webhook URL
                "events": ["transcript.data", "transcript.partial_data"]
              }
            ]
          }
        }
        r = await session.post(f"{RECALL_BASE}/bot", json=cfg, headers=headers)
        r.raise_for_status()
        bot_id = (await r.json())["id"]
        print("Bot created:", bot_id)

        # 2️⃣ Wait until bot joins meeting
        for _ in range(20):
            await asyncio.sleep(3)
            st = await session.get(f"{RECALL_BASE}/bot/{bot_id}", headers=headers)
            js = await st.json()
            if js.get("status_changes") and js["status_changes"][-1]["code"]=="in_call_recording":
                break
        print("Bot joined")
        
        text = 'Toing bot is turned on.'

        # 5️⃣ Convert text to speech using gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_bytes = audio_buffer.getvalue()

        b64_audio = base64.b64encode(audio_bytes).decode()
        payload = {"kind":"mp3", "b64_data": b64_audio}

        # 6️⃣ Play into Google Meet
        out = await session.post(f"{RECALL_BASE}/bot/{bot_id}/output_audio/",
                                 json=payload, headers=headers)
        if out.status == 200:
            print("✅ TTS audio played!")
        else:
            print("Playback failed:", await out.text())

        # 7️⃣ Continuously fetch live transcript utterances (conversation)
        for _ in range(20):  # Poll every 3 seconds for 1 minute
            transcript_url = f"{RECALL_BASE}/transcript/retrieve/"
            params = {"bot_id": bot_id}
            tr_resp = await session.get(transcript_url, headers=headers, params=params)
            if tr_resp.status == 200:
                transcript_json = await tr_resp.json()
                print("Full transcript response:", transcript_json)  # Debug print
                utterances = transcript_json.get("utterances", [])
                print("Live conversation (utterances):", utterances)
            else:
                print("Transcript fetch failed:", await tr_resp.text())
            await asyncio.sleep(3)

        await session.delete(f"{RECALL_BASE}/bot/{bot_id}", headers=headers)

asyncio.run(main())
