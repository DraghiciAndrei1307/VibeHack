from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configurații din variabile de mediu
EVOLUTION_API = os.getenv("EVOLUTION_API_URL")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("INSTANCE_NAME")


@app.route("/webhook", methods=["POST"])
def webhook():
    # Preluăm datele JSON trimise de Evolution API
    payload = request.get_json()

    if not payload:
        return jsonify({"ignored": True}), 400

    try:
        # Navigăm prin structura payload-ului Evolution API
        message = payload["data"]["message"]["conversation"].lower()
        remote_jid = payload["data"]["key"]["remoteJid"]
        # Extragem doar numărul de telefon
        number = remote_jid.split("@")[0]
    except (KeyError, TypeError):
        # Dacă structura nu coincide (ex: mesaje de tip imagine sau status), ignorăm
        return jsonify({"ignored": True}), 200

    # Logică de răspuns
    reply = "👋 Hi!\n1️⃣ Book appointment\n2️⃣ Help"

    if "hi" in message or "hello" in message:
        reply = "👋 Hello! What would you like to do?\n1️⃣ Book appointment\n2️⃣ Help"
    elif "help" in message:
        reply = "ℹ️ I can help you book appointments via WhatsApp."

    # Trimitem răspunsul înapoi
    send_status = send_message(number, reply)

    return jsonify({"status": "sent", "evolution_response": send_status}), 200


@app.route("/", methods=["GET"])
def home():
    return "Botul este online!", 200

def send_message(number, text):
    url = f"{EVOLUTION_API}/message/sendText/{INSTANCE}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "number": number,
        "text": text,
        "delay": 1200,  # Opțional: adaugă o mică întârziere pentru aspect natural
        "linkPreview": False
    }

    response = requests.post(url, json=data, headers=headers)
    return response.status_code


if __name__ == "__main__":
    # Rulăm pe portul 5000 (standard Flask) sau cel definit în mediu
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


