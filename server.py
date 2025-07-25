# Save as webhook_server.py
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/api/webhook/recall/transcript")
async def recall_webhook(request: Request):
    data = await request.json()
    print("Received webhook:", data)
    return {}

# if __name__ == "__main__":
#     uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)