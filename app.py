import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Load API keys from environment variables (recommended for security)
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/563469153515061/messages"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")  # Load from environment variable
VECTARA_API_URL = "https://api.vectara.io/v2/corpora"
VECTARA_API_KEY = os.getenv("VECTARA_API_KEY")  # Load from environment variable

# Verify token for WhatsApp API webhook validation
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_custom_verify_token")  # Set a verification token

def query_vectara(user_message):
    """ Sends the WhatsApp message to Vectara API and returns the response. """
    headers = {
        "Authorization": f"Bearer {VECTARA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": [{"query": user_message, "numResults": 3}]
    }

    try:
        response = requests.post(VECTARA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("responseSet", [{}])[0].get("response", [{}])[0].get("text", "No response found.")
    except requests.exceptions.RequestException as e:
        print(f"Vectara API Error: {e}")
        return "Sorry, I couldn't fetch an answer."

def send_whatsapp_message(recipient, message):
    """ Sends a message back to WhatsApp. """
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
    except requests.exceptions.RequestException as e:
        print(f"WhatsApp API Error: {e}")

# ✅ Webhook verification for WhatsApp API (Meta requires this)
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """ Handles GET requests for WhatsApp webhook verification """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verified successfully!")
            return challenge, 200
        else:
            return jsonify({"error": "Invalid verification token"}), 403

    return jsonify({"error": "Missing verification parameters"}), 400

# ✅ Webhook for receiving WhatsApp messages
@app.route("/webhook", methods=["POST"])
def receive_message():
    """ Handles incoming WhatsApp messages. """
    data = request.json
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
                                response = query_vectara(text)
                                send_whatsapp_message(sender, response)
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"}), 200

# ✅ Simple home route for testing
@app.route("/")
def home():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
