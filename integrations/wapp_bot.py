import os
import sys
import traceback

# Force unbuffered output so logs appear immediately in the terminal
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

def log(msg):
    """Print and flush so it shows up in terminal immediately."""
    print(msg, flush=True)

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client # Importă clientul REST

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.agent import Agent
from agent.agent_image import AgentImage
import threading

app = Flask(__name__)

# Datele tale de la Twilio
account_sid = 'AC9cf9b2a16ae5022eb7e37e4bf8089a6e'
auth_token = '8fa4c911c5aae481fdda514123aeb0e9'
client = Client(account_sid, auth_token)


def process_logic(user_msg, media_url, sender_number):
    log(f"[THREAD] Started processing for {sender_number}: text={user_msg[:50]!r}... media={bool(media_url)}")
    try:
        if media_url:
            # Caz 1: Utilizatorul a trimis o poză
            img_agent = AgentImage()
            response_text = img_agent.find_cheaper_flight(media_url)
        else:
            # Caz 2: Utilizatorul a trimis doar text
            new_agent = Agent()
            flights = new_agent.talk(user_msg)

            if not flights or not isinstance(flights, list):
                response_text = "Nu am găsit zboruri pentru cererea ta."
            else:
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
                response_text = "\n".join(msg_parts)

        # Trimitere finală pe WhatsApp
        log(f"[THREAD] Sending follow-up message to {sender_number} ({len(response_text)} chars)")
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=response_text[:1600],
            to=sender_number
        )
        log(f"[THREAD] Follow-up message sent OK")

    except Exception as e:
        log(f"[THREAD] ERROR: {e}")
        traceback.print_exc()
        try:
            client.messages.create(
                from_='whatsapp:+14155238886',
                body="⚠️ A apărut o problemă la procesarea cererii tale.",
                to=sender_number
            )
            log("[THREAD] Error fallback message sent")
        except Exception as send_err:
            log(f"[THREAD] Failed to send error message to user: {send_err}")


@app.route("/message", methods=["POST"])
def message():
    log("[FLASK] Incoming POST /message (request reached this Flask app)")
    user_msg = (request.values.get('Body') or '').lower()
    sender_number = request.values.get('From') or ''
    try:
        num_media = int(request.values.get('NumMedia') or 0)
    except (TypeError, ValueError):
        num_media = 0

    media_url = request.values.get('MediaUrl0') if num_media > 0 else None

    # Pornim thread-ul care decide singur dacă procesează Imagine sau Text
    thread = threading.Thread(
        target=process_logic,
        args=(user_msg, media_url, sender_number)
    )
    thread.start()

    response = MessagingResponse()
    msg = "Analizez imaginea..." if media_url else "Caut zborurile solicitate..."
    response.message(msg)
    log(f"[FLASK] Sending immediate TwiML reply, thread started for {sender_number}")
    return str(response)


if __name__ == "__main__":
    log("Starting Flask server on http://0.0.0.0:5001 (use ngrok http 5001 and set Twilio webhook to https://YOUR_URL/message)")
    # use_reloader=False is required when using background threads:
    # otherwise the reloader can restart the process and kill the thread
    # before it sends the follow-up WhatsApp message.
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)