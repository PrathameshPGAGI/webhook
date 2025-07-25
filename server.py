# Save as webhook_server.py
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/webhook/recall/transcript', methods=['POST'])
def recall_webhook():
    data = request.json
    print("Received webhook:", data)
    return '', 200

if __name__ == '__main__':
    app.run(port=5000)