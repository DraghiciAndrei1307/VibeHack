
"""
    Module that contains the logic for WhatsApp bot.
"""

import os
import sys
import traceback
import threading

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client  # Twilio REST client

from agent.agent import Agent
from agent.agent_image import AgentImage
from agent.location_finder import (
    _download_media_to_temp,
    identify_location_from_url,
    encode_and_resize_image,
    client as gemma_client,
    MODEL_NAME as GEMMA_MODEL,
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




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
            "Look at this image. "
            "Reply with exactly one word: "
            "either SCREENSHOT or PLACE."
            "SCREENSHOT = the image is a screenshot "
            "from a phone or computer showing flight details, "
            "booking confirmation, flight search results, or"
            " airline/booking app content. "
            "PLACE = the image is a photo of a real-world "
            "location (street, building, landscape, "
            "city, nature) that could be identified by its appearance."
            " Reply only with the word SCREENSHOT or PLACE."
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,"
                                   f"{base64_image}"
                        }
                    },
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

# Your data from Twilio
account_sid = os.environ.get("SID")
auth_token = os.environ.get("AUTH_TOKEN")
client = Client(account_sid, auth_token)


def process_logic(user_msg, media_url, sender_number):

    """
    Function that decides if the message input contains:
    text, screenshot or image.
    """

    print(
        f"[THREAD] Started processing for {sender_number}:"
        f" text={user_msg[:50]!r}... media={bool(media_url)}"
    )
    try:
        if media_url:
            # Case 1: User sends an image – we clasify: flight screenshot or image of a place
            image_kind = classify_image_type(media_url)
            if image_kind == "PLACE":
                response_text = identify_location_from_url(media_url)
            else:
                # Flight details Screenshot
                img_agent = AgentImage()
                response_text = img_agent.find_cheaper_flight(media_url)
        else:
            # Case 2: User sends only text
            new_agent = Agent()
            flights = new_agent.talk(user_msg)

            if not flights or not isinstance(flights, list):
                response_text = "we couldn't identify flights."
            else:
                msg_parts = ["✈️ *Flights found:* \n"]
                for i, f in enumerate(flights[:5], 1):
                    departure = f.get('departure', {})
                    ret = f.get('return', {})

                    flight_info = (
                    f"*{i}. {f.get('price', 'N/A')}*\n"
                    f"🛫 *Departure:* {departure.get('date')}\n"
                    f"   _{departure.get('takeoff', {}).get('time')} "
                    f"({departure.get('takeoff', {}).get('city')})_ -> "
                    f"_{departure.get('landing', {}).get('time')} "
                    f"({departure.get('landing', {}).get('airport')})_\n"
                    f"🛬 *Return:* {ret.get('date')}\n"
                    f"   _{ret.get('takeoff', {}).get('time')} "
                    f"({ret.get('takeoff', {}).get('city')})_ -> "
                    f"_{ret.get('landing', {}).get('time')} "
                    f"({ret.get('landing', {}).get('airport')})_\n"
                    f"⏳ *Time:* {f.get('stay_duration')}\n"
                    f"{'─' * 15}"
                    )
                    msg_parts.append(flight_info)
                response_text = "\n".join(msg_parts)

        client.messages.create(
            from_='whatsapp:+14155238886',
            body=response_text[:1600],
            to=sender_number
        )
        print("[THREAD] Follow-up message sent OK")

    except Exception as e:
        print(f"[THREAD] ERROR: {e}")
        traceback.print_exc()
        try:
            client.messages.create(
                from_='whatsapp:+14155238886',
                body="⚠️ An error occured while processing your request.",
                to=sender_number
            )
            print("[THREAD] Error fallback message sent")
        except Exception as send_err:
            print(f"[THREAD] Failed to send error message to user: {send_err}")


@app.route("/message", methods=["POST"])
def message():

    """Function that contains the WhatsApp message logic."""

    print("[FLASK] Incoming POST /message (request reached this Flask app)")
    user_msg = (request.values.get('Body') or '').lower()
    sender_number = request.values.get('From') or ''
    try:
        num_media = int(request.values.get('NumMedia') or 0)
    except (TypeError, ValueError):
        num_media = 0

    media_url = request.values.get('MediaUrl0') if num_media > 0 else None

    # Start the thread which decides we deal with image or text
    thread = threading.Thread(
        target=process_logic,
        args=(user_msg, media_url, sender_number)
    )
    thread.start()

    response = MessagingResponse()
    msg = "Image analysis..." if media_url else "Searching the requested flights..."
    response.message(msg)
    print(f"[FLASK] Sending immediate TwiML reply, thread started for {sender_number}")
    return str(response)


if __name__ == "__main__":
    print(
        "Starting Flask server on http://0.0.0.0:5001 "
        "(use ngrok http 5001 and set Twilio webhook "
        "to https://YOUR_URL/message)"
    )
    # use_reloader=False is required when using background threads:
    # otherwise the reloader can restart the process and kill the thread
    # before it sends the follow-up WhatsApp message.
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
