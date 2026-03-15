import threading
import requests
import os
from flask import Flask, request, jsonify
from agent.agent import Agent

app = Flask(__name__)

# Configurații din variabile de mediu
EVOLUTION_API = os.getenv("EVOLUTION_API_URL")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("INSTANCE_NAME")


def talk(user_msg):
    """Logica de generare a textului cu zboruri"""
    try:
        new_agent = Agent()
        flights = new_agent.talk(user_msg)

        if not flights or not isinstance(flights, list):
            return "Nu am găsit zboruri pentru cererea ta."

        msg_parts = ["✈️ *Zboruri găsite:* \n"]
        for i, f in enumerate(flights[:5], 1):
            departure = f.get('departure', {})
            ret = f.get('return', {})

            flight_info = (
                f"*{i}. {f.get('price', 'N/A')}*\n"
                f"🛫 *Plecare:* {departure.get('date')}\n"
                f"   _{departure.get('takeoff', {}).get('time')} ({departure.get('takeoff', {}).get('city')})_ -> "
                f"_{departure.get('landing', {}).get('time')} ({departure.get('landing', {}).get('airport')})_\n"
                f"🛬 *Retur:* {ret.get('date')}\n"
                f"   _{ret.get('takeoff', {}).get('time')} ({ret.get('takeoff', {}).get('city')})_ -> "
                f"_{ret.get('landing', {}).get('time')} ({ret.get('landing', {}).get('airport')})_\n"
                f"⏳ *Durată:* {f.get('stay_duration')}\n"
                f"{'─' * 15}"
            )
            msg_parts.append(flight_info)

        return "\n".join(msg_parts)
    except Exception as e:
        print(f"Eroare în funcția talk: {e}")
        return "Îmi pare rău, a apărut o eroare la căutarea zborurilor."


def background_task(number, message):
    """Această funcție rulează în fundal pentru a evita timeout-ul"""
    print(f"Încep căutarea pentru {number}...")
    response_text = talk(message)
    send_message(number, response_text)
    print(f"Răspuns trimis către {number}")


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"status": "error"}), 400

    try:
        data = payload.get("data", {})

        # Ignorăm mesajele proprii
        if data.get("key", {}).get("fromMe") is True:
            return jsonify({"status": "ignored"}), 200

        # Extragem numărul și mesajul
        remote_jid = data.get("key", {}).get("remoteJid")
        if not remote_jid:
            return jsonify({"status": "no_jid"}), 200

        number = remote_jid.split("@")[0]

        msg_obj = data.get("message", {})
        message = (msg_obj.get("conversation") or
                   msg_obj.get("extendedTextMessage", {}).get("text") or "").lower()

        if not message:
            return jsonify({"status": "empty_message"}), 200

        print(f"Am primit: '{message}' de la {number}. Pornesc căutarea în fundal...")

        # --- REPARAȚIA PRINCIPALĂ: Pornim căutarea fără să blocăm webhook-ul ---
        thread = threading.Thread(target=background_task, args=(number, message))
        thread.start()

    except Exception as e:
        print(f"Eroare în webhook: {e}")

    # Răspundem imediat 200 OK către Evolution API
    return jsonify({"status": "success"}), 200


@app.route("/", methods=["GET"])
def home():
    return "Botul este online!", 200


def send_message(number, text):
    """Trimitere mesaj prin Evolution API"""
    url = f"{EVOLUTION_API}/message/sendText/{INSTANCE}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": number,
        "text": text,
        "delay": 1200,
        "linkPreview": False
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        print(f"Eroare la trimiterea mesajului: {e}")
        return 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)