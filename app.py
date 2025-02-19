import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ✅ Load API keys from environment variables (recommended for security)
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/563469153515061/messages"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")  # Load from Glitch env
VECTARA_API_URL = "https://api.vectara.io/v2/corpora"
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")  # Load from Glitch env

# ✅ Verified token (Must match Meta Developer Console)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "MySecretToken123!")

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

# ✅ Function to send WhatsApp message
def send_whatsapp_message(recipient, message):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"[INFO] Message sent to {recipient}: {message}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] WhatsApp API Error: {e}")

# ✅ Webhook Verification
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"[INFO] Received verification request: mode={mode}, token={token}")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("[INFO] Webhook verified successfully!")
            return challenge, 200
        else:
            print("[ERROR] Invalid verification token received.")
            return jsonify({"error": "Invalid verification token"}), 403

    return jsonify({"error": "Missing verification parameters"}), 400

# ✅ Webhook for Receiving WhatsApp Messages
@app.route("/webhook", methods=["POST"])
def receive_message():
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

                                # Send the response back to WhatsApp
                                send_whatsapp_message(sender, response)
                                print(f"[INFO] Message sent to {sender}: {response}")

    except Exception as e:
        print(f"[ERROR] Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"}), 200

# ✅ Simple Test Route
@app.route("/")
def home():
    return "Hello, Vectara WhatsApp Bot is Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)  # Use port 3000 for Glitch
