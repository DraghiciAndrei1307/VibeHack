
"""
    Module that uses Evolution API instead of Twilio.
"""

import os

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ENV VARIABLES
EVOLUTION_API = os.getenv("EVOLUTION_API_URL")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("INSTANCE_NAME")


@app.route("/webhook", methods=["POST"])
def webhook():

    """
        Get JSON data from the Evolution API
    """

    payload = request.get_json()

    if not payload:
        return jsonify({"ignored": True}), 400

    try:
        # Parse Evolution API's payload
        message = payload["data"]["message"]["conversation"].lower()
        remote_jid = payload["data"]["key"]["remoteJid"]
        # Get the phone number
        number = remote_jid.split("@")[0]
    except (KeyError, TypeError):
        # Wrong structure -> IGNORE
        return jsonify({"ignored": True}), 200

    # Response logic
    reply = "👋 Hi!\n1️⃣ Book appointment\n2️⃣ Help"

    if "hi" in message or "hello" in message:
        reply = ("👋 Hello! What would you like to do?\n"
                 "1️⃣ Book appointment\n2️⃣ Help"
        )
    elif "help" in message:
        reply = "ℹ️ I can help you book appointments via WhatsApp."

    # Send the answer
    send_status = send_message(number, reply)

    return jsonify({"status": "sent", "evolution_response": send_status}), 200


def send_message(number, text):

    """
        Function to send a message to the Evolution API.
    """

    url = f"{EVOLUTION_API}/message/sendText/{INSTANCE}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "number": number,
        "text": text,
        "delay": 1200,
        "linkPreview": False
    }

    response = requests.post(
        url=url,
        json=data,
        headers=headers,
        timeout=10
    )
    return response.status_code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
