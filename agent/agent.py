import json
import os
import re
import sys
from openai import OpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import url_gen_and_parsing

from datetime import datetime

TIME_NOW = datetime.now()

class Agent:
    def __init__(self):

        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=""
        )

        self.instruction_prompt = (
            "You are a helpful chatbot. "
            "Return ONLY a valid JSON using double quotes, with the following structure: "
            '{"dates": {"departureFrom": "", "departureTo": "", "returnFrom": "", "returnTo": "", "anytime": false, "stayTime": {"min": "", "max": ""}}, '
            '"passengers": {"adults": 1, "children": 0, "infants": 0, "youth": 0}, '
            '"locations": {"origins": [{"code": "BUH", "type": "CITY"}], "destinations": [{"code": "*", "type": "ANYWHERE"}]}, '
            '"deduplicate": false, '
            '"luggageOptions": {"personalItemCount": 1, "cabinTrolleyCount": 0, "checkedBaggageCount": 0}}. '
            "If user input for destination and departure matches an airport code, use that code, and the type field should be 'AIRPORT'. Do not add any text outside of this JSON. Leave default values if user does not provide them."
            f"Give results after the current_date: {TIME_NOW}"
        )

    def talk(self, input_data):
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=[
                {"role": "system", "content": self.instruction_prompt},
                {"role": "user", "content": input_data}
            ],
            max_tokens=400,
            temperature=0.0  # mai determinist ca să respecte JSON-ul
        )

        payload = response.choices[0].message.content
        print("Raw payload:", payload)

        # --- Curățare: extragem doar JSON-ul dintre acolade ---
        match = re.search(r'\{.*\}', payload, re.DOTALL)
        if not match:
            raise ValueError("Nu am putut găsi JSON în răspunsul modelului")

        json_str = match.group(0)

        # --- Parsare ---
        payload_dict = json.loads(json_str)

        # --- Folosire în funcția ta ---
        flights = url_gen_and_parsing.extract_flights(payload_dict)

        return flights

# if __name__ == '__main__':
#
#     while True:
#         input_query = input("Ask me a question: ")
#
#         if input_query == "exit":
#             break
#
#         talk(input_query)

