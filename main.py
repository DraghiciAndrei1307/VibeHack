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
    payload = request.get_json()

    if not payload:
        return jsonify({"ignored": True}), 400

    try:
        data = payload.get("data", {})

        # PASUL CRITIC: Dacă fromMe este True, înseamnă că botul a trimis mesajul.
        # Îl ignorăm ca să nu facem buclă!
        if data.get("key", {}).get("fromMe") is True:
            return jsonify({"status": "ignored", "reason": "sent_by_me"}), 200

        msg_obj = data.get("message", {})
        message = (msg_obj.get("conversation") or
                   msg_obj.get("extendedTextMessage", {}).get("text") or
                   "").lower()

        remote_jid = data.get("key", {}).get("remoteJid")
        number = remote_jid.split("@")[0]

        # Logica de răspuns (rămâne la fel)
        if "hi" in message or "hello" in message:
            reply = "👋 Hello! What would you like to do?\n1️⃣ Book appointment\n2️⃣ Help"
            send_message(number, reply)
        elif "help" in message:
            reply = "ℹ️ I can help you book appointments."
            send_message(number, reply)

    except Exception as e:
        print(f"Eroare: {e}")
        return jsonify({"ignored": True}), 200

    return jsonify({"status": "success"}), 200


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


