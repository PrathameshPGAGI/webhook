# Save as webhook_server.py
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/api/webhook/recall/transcript")
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