import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Load API keys from environment variables (recommended for security)
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/563469153515061/messages"
WHATSAPP_ACCESS_TOKEN = os.getenv("EAAQwfmEhplQBOybxM3LjK4rSKwFqalivj0vFStpU3ybZAFgEvMjrtBBNTlNYaJCVag4ZBOxKudOaWTo3O5Jh9XwJdoQLewY0NbhihXVKowMSImWYK4DrvTmEEp3M2uusstErMJdJ7xMBwjZCZCZAUlatrZAdkoDp6ihBNymc44ecooeZBbxz5jVPkA7DLdoZA05QjzGHZASve790lZB24yF0DnUyDyeecKB1Xjj2RxmVVLodoZD")
VECTARA_API_URL = "https://api.vectara.io/v2/corpora"
VECTARA_API_KEY = os.getenv("zwt__4OdcLYkSOvnvUk1pg3HBaR116CseKBaGt1-cw")

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

@app.route("/webhook", methods=["POST"])
def webhook():
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)


