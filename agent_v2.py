import json
import re
from openai import OpenAI
import url_gen_and_parsing

from datetime import datetime

from agent import generate

TIME_NOW = datetime.now()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="rc_d19a3d709759a2023185f5d7f7c0d0386791612fbf32d028a79603cae7e7d763"
)

instruction_prompt = (
    "You are a helpful chatbot. "
    "Return ONLY a valid JSON using double quotes, with the following structure: "
    '{"dates": {"departureFrom": "", "departureTo": "", "returnFrom": "", "returnTo": "", "anytime": false, "stayTime": {"min": "", "max": ""}}, '
    '"passengers": {"adults": 1, "children": 0, "infants": 0, "youth": 0}, '
    '"locations": {"origins": [{"code": "BUH", "type": "CITY"}], "destinations": [{"code": "*", "type": "ANYWHERE"}]}, '
    '"deduplicate": false, '
    '"luggageOptions": {"personalItemCount": 1, "cabinTrolleyCount": 0, "checkedBaggageCount": 0}}. '
    "Do not add any text outside of this JSON. Leave default values if user does not provide them."
    f"Give results after the current_date: {TIME_NOW}"
)

def talk(input_data):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=[
            {"role": "system", "content": instruction_prompt},
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
    url_gen_and_parsing.extract_flights(payload_dict)

if __name__ == '__main__':

    while True:
        input_query = input("Ask me a question: ")

        if input_query == "exit":
            break

        talk(input_query)

