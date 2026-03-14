from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client # Importă clientul REST
from agent.agent import Agent
from agent.agent_image import AgentImage
import threading

app = Flask(__name__)

# Datele tale de la Twilio
account_sid = 'AC12757e86a8c931c80f749acf65269e6a'
auth_token = '946766f0839235186b57ec01e9ffe9b1'
client = Client(account_sid, auth_token)


def process_logic(user_msg, media_url, sender_number):
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
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=response_text[:1600],
            to=sender_number
        )

    except Exception as e:
        print(f"THREAD ERROR: {e}")
        client.messages.create(
            from_='whatsapp:+14155238886',
            body="⚠️ A apărut o problemă la procesarea cererii tale.",
            to=sender_number
        )


@app.route("/message", methods=["POST"])
def message():
    user_msg = request.values.get('Body', '').lower()
    sender_number = request.values.get('From')
    num_media = int(request.values.get('NumMedia', 0))

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
    return str(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)