
"""
This module contains the logic for retrieving a list of flights
based on a text-only message from the user.
"""
import json
import os
import re
import sys
from datetime import datetime
from openai import OpenAI

from integrations import url_gen_and_parsing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TIME_NOW = datetime.now()


class Agent:

    """
    Class that emulates the logic of retrieving a list of flights
    based on a text-only message from the user.
    """

    def __init__(self):

        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key= os.environ.get("API_KEY")
        )

        self.instruction_prompt = (
            "You are a helpful chatbot. "
            "Return ONLY a valid JSON using double quotes, "
            "with the following structure: "
            '{"dates": {"departureFrom": "", "departureTo": "",'
            ' "returnFrom": "", "returnTo": "", "anytime": false,'
            ' "stayTime": {"min": "", "max": ""}}, '
            '"passengers": {"adults": 1, "children": 0, '
            '"infants": 0, "youth": 0}, '
            '"locations": {"origins": [{"code": "BUH", '
            '"type": "CITY"}], "destinations": [{"code": "*", '
            '"type": "ANYWHERE"}]}, '
            '"deduplicate": false, '
            '"luggageOptions": {"personalItemCount": 1, '
            '"cabinTrolleyCount": 0, "checkedBaggageCount": 0}}. '
            "If user input for destination and departure matches an airport code, "
            "use that code, and the type field should be 'AIRPORT'. "
            "Do not add any text outside of this JSON. Leave default values "
            "if user does not provide them."
            f"Give results after the current_date: {TIME_NOW}"
        )

    def talk(self, input_data):

        """
        Method that talks to the user to get a list of flights.
        """

        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=[
                {"role": "system", "content": self.instruction_prompt},
                {"role": "user", "content": input_data}
            ],
            max_tokens=400,
            temperature=0.0  # this makes it more deterministic
        )

        payload = response.choices[0].message.content
        print("Raw payload:", payload)

        # --- Cleaning: We extract only the JSON response ---
        match = re.search(r'\{.*\}', payload, re.DOTALL)
        if not match:
            raise ValueError("JSON not found in the AI model response. ")

        json_str = match.group(0)

        # --- Parsing ---
        payload_dict = json.loads(json_str)

        flights = url_gen_and_parsing.extract_flights(payload_dict)

        return flights
