from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/563469153515061/messages"
WHATSAPP_ACCESS_TOKEN = "EAAQwfmEhplQBOyEGEIfvHnfevLwUaMK1ylhEXl23nG2hcEjBI7w4o1wKZClY00wZCTyfwZBOKWKyPiZCWHfc2922CdgYuJK8tZBZAZBvqshqaV5zTrqdpp97jE10NVvuW6Brty4j6YjmMzS11UqGDVu8vBapFz9km3tMaZCKHUQqIql0KhCbGbR2SGd7J7EuHX63aKHZCpFEYhrlgeUrIREkgXLkgsSheVHIqxQBjyuzi71Bu"
VECTARA_API_URL = "https://api.vectara.io/v2/corpora"    # /v2/corpora/technology-corpus/
VECTARA_API_KEY = "zqt__4OdcJUKithvLlaOz8LiuzXULBrX8y0kmVrpbg" 

def query_vectara(user_message):
    """ Sends the WhatsApp message to Vectara API and returns the response. """
    headers = {"Authorization": f"Bearer {VECTARA_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "query": [{"query": user_message, "numResults": 3}]
    }
    response = requests.post(VECTARA_API_URL, headers=headers, json=payload)
    return response.json()["responseSet"][0]["response"][0]["text"] if response.ok else "Sorry, I couldn't fetch an answer."

def send_whatsapp_message(recipient, message):
    """ Sends a message back to WhatsApp. """
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    """ Handles incoming WhatsApp messages. """
    data = request.json
    if data.get("entry"):
        for entry in data["entry"]:
            for message in entry["changes"]:
                sender = message["value"]["messages"][0]["from"]
                text = message["value"]["messages"][0]["text"]["body"]
                response = query_vectara(text)
                send_whatsapp_message(sender, response)
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=5000)
