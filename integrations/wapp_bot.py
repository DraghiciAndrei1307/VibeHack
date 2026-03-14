from re import search

import OpenAI
from openai import OpenAI
from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse


app = Flask(__name__)

@app.route("/", methods=["POST"])

# chatbot logic
def bot():
    response = MessagingResponse()
    msg = response.message()
    msg.body('this is the response/reply  from the bot.')


@app.route("/message", methods=["POST"])
def message():
    incoming_msg = request.values.get('Body', '').lower()
    print(incoming_msg)

    client = OpenAI(
        base_url="https://api.featherless.ai/v1",
        api_key="rc_d19a3d709759a2023185f5d7f7c0d0386791612fbf32d028a79603cae7e7d763"
    )

    response = MessagingResponse()
    msg = response.message()
    msg.body('this is the response/reply  from the bot.')
    return str(response)

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5001, debug = True)