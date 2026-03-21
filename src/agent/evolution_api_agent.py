"""
    This module will use:
    - Evolution API
    - Ngrok / Cloudflare Tunnel (cloudflared)
    for creating a gateway to the localhost
    - Ollama to pull different models
    - Private VM
    - Docker compose
"""

import os

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


# Create webhook

@app.route('/webhook', methods=['POST'])
def webhook():
    """
        Get JSON data from the Evolution API
    """
    pass


def send_message(number, text):
    """
        Function to send a message to the Evolution API.
    """
    pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



