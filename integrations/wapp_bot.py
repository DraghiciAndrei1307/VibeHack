from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client # Importă clientul REST
from agent.agent import Agent
import threading

app = Flask(__name__)

# Datele tale de la Twilio
account_sid = 'cheie'
auth_token = 'token'
client = Client(account_sid, auth_token)


def process_agent_logic(user_msg, sender_number):
    try:
        new_agent = Agent()
        flights = new_agent.talk(user_msg)

        if not flights or not isinstance(flights, list):
            response_text = "Nu am găsit zboruri pentru cererea ta."
        else:
            # Construim un mesaj frumos formatat
            msg_parts = ["✈️ *Zboruri găsite:* \n"]

            # Luăm doar primele 5 zboruri ca să nu depășim limita de caractere WhatsApp
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

    except Exception as e:
        print("ERROR:", e)
        response_text = "⚠️ Ups! A apărut o eroare la procesarea zborurilor."

    # Trimitem mesajul formatat
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=response_text[:1600],  # Limita WhatsApp este de ~1600 caractere
        to=sender_number
    )

@app.route("/message", methods=["POST"])
def message():
    user_msg = request.values.get('Body', '').lower()
    sender_number = request.values.get('From') # Păstrăm numărul utilizatorului

    # Pornim un thread nou pentru procesarea grea
    thread = threading.Thread(target=process_agent_logic, args=(user_msg, sender_number))
    thread.start()

    # Răspundem IMEDIAT lui Twilio ca să nu dea timeout
    response = MessagingResponse()
    response.message("Caut zborurile solicitate... revin imediat cu un mesaj.")
    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)