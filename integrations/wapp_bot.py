import os
import sys
import tempfile
import requests

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client  # Twilio REST client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.agent import Agent
from agent.agent_image import AgentImage
from location_finder import (
    _download_media_to_temp,
    identify_location_from_url,
    encode_and_resize_image,
    client as gemma_client,
    MODEL_NAME as GEMMA_MODEL,
)
import threading

def classify_image_type(media_url):
    """
    Use the same Gemma vision model as location_finder to classify the image:
    SCREENSHOT = flight/booking screenshot, PLACE = photo of a real-world location.
    Returns "SCREENSHOT" or "PLACE". Defaults to "SCREENSHOT" on any error.
    """
    path = None
    try:
        path = _download_media_to_temp(media_url)
        base64_image = encode_and_resize_image(path)
        if not base64_image:
            return "SCREENSHOT"
        prompt_text = (
            "Look at this image. Reply with exactly one word: either SCREENSHOT or PLACE. "
            "SCREENSHOT = the image is a screenshot from a phone or computer showing flight details, "
            "booking confirmation, flight search results, or airline/booking app content. "
            "PLACE = the image is a photo of a real-world location (street, building, landscape, "
            "city, nature) that could be identified by its appearance. Reply only with the word SCREENSHOT or PLACE."
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        ]
        chat_response = gemma_client.chat.completions.create(
            model=GEMMA_MODEL,
            messages=messages,
            max_tokens=20,
            temperature=0.0,
            timeout=30.0,
        )
        text = (chat_response.choices[0].message.content or "").strip().upper()
        return "PLACE" if "PLACE" in text else "SCREENSHOT"
    except Exception:
        return "SCREENSHOT"
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception:
                pass

app = Flask(__name__)

# Datele tale de la Twilio
account_sid = ''
auth_token = ''
client = Client(account_sid, auth_token)


def process_logic(user_msg, media_url, sender_number):
    try:
        if media_url:
            # Caz 1: Utilizatorul a trimis o poză – clasificăm: screenshot de zbor sau poză de loc
            image_kind = classify_image_type(media_url)
            if image_kind == "PLACE":
                response_text = identify_location_from_url(media_url)
            else:
                # Screenshot cu detalii de zbor – tratament neschimbat
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

        # Trimitere finală pe WhatsApp (4096 = limit Twilio WhatsApp; răspuns complet pentru location_finder)
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