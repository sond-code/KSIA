import os
from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# ✅ Load API keys from environment variables
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/563469153515061/messages"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
VECTARA_API_URL = "https://api.vectara.io/v2/corpora"
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")

# ✅ Function to query Vectara API
def query_vectara(user_message):
    headers = {
        "Authorization": f"Bearer {VECTARA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"query": [{"query": user_message, "numResults": 3}]}

    try:
        response = requests.post(VECTARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("responseSet", [{}])[0].get("response", [{}])[0].get("text", "No response found.")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Vectara API Error: {e}")
        return "Sorry, I couldn't fetch an answer."

# ✅ Webhook for receiving WhatsApp messages
@app.route("/webhook", methods=["POST"])
def receive_message():
    """Handles incoming WhatsApp messages."""
    data = request.json
    print("[INFO] Received WhatsApp message:", data)

    try:
        if data and "entry" in data:
            for entry in data["entry"]:
                for message in entry.get("changes", []):
                    msg_value = message.get("value", {})
                    if "messages" in msg_value:
                        for msg in msg_value["messages"]:
                            sender = msg.get("from")
                            text = msg.get("text", {}).get("body", "")

                            if sender and text:
                                print(f"[INFO] Received message from {sender}: {text}")

                                # Query Vectara
                                response = query_vectara(text)
                                print(f"[INFO] Response from Vectara: {response}")

                                return jsonify({"status": "success", "message": response}), 200

    except Exception as e:
        print(f"[ERROR] Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"}), 200

# ✅ Web UI Route
@app.route("/")
def home():
    return render_template("index.html")

# ✅ API for Web Chatbot UI
@app.route("/chat", methods=["POST"])
def chat():
    """Handles user messages from the web UI."""
    user_message = request.json.get("message", "")
    response = query_vectara(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
