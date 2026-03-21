
"""
    Module that takes an image from the user
    and tries to guess the place.
"""

import json
import os
import re
import sys
from datetime import datetime

import requests
import easyocr
from openai import OpenAI
from integrations import url_gen_and_parsing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TIME_NOW = datetime.now()

reader = easyocr.Reader(
    ['en', 'ro'],
    gpu=True
)


class AgentImage:

    """
    Class that takes an image from the user
    and tries to guess the place.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=os.environ.get("API_KEY")
        )

    def extract_text_from_screenshot(self, image_url: str):

        """
            Method that extracts text from screenshot.
        """

        print(f"\n[~] OCR processing for: {image_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        rezultate = reader.readtext(response.content, detail=0, paragraph=True)
        extrase = "\n".join(rezultate)

        p = re.split(r'€|\$|lei', extrase)
        pret_initial = 0.0
        if len(p) > 1:
            pret_str = re.sub(r'[^\d.]', '', p[1])
            if pret_str:
                pret_initial = float(pret_str)

        return extrase, pret_initial

    def generate_json_from_ocr(self, ocr_text: str) -> dict:

        """
            Method that generates JSON from OCR.
        """

        instruction_prompt = (
            "You are an expert travel data parser. "
            "I will provide you with raw, messy OCR text "
            "extracted from a flight screenshot. "
            "Your job is to ignore the garbage characters "
            "(like '«', '2?', 'x') and extract the origin "
            "city, destination city, and stay duration. "
            "1. Convert city names to their 3-letter "
            "IATA codes (e.g., Bucharest -> BUH, "
            "Rome -> ROM, Larnaca -> LCA). "
            "2. If you see a stay duration like "
            "'4 nights', set 'stayTime' min and max to 4. "
            "3. Return ONLY a valid JSON using double quotes,"
            " with the following structure: "
            '{"dates": {"departureFrom": "", "departureTo": "",'
            ' "returnFrom": "", "returnTo": "", "anytime": false,'
            ' "stayTime": {"min": "", "max": ""}}, '
            '"passengers": {"adults": 1, "children": 0,'
            ' "infants": 0, "youth": 0}, '
            '"locations": {"origins": [{"code": "BUH", "type": "CITY"}],'
            ' "destinations": [{"code": "*", "type": "ANYWHERE"}]}, '
            '"deduplicate": false, '
            '"luggageOptions": {'
            '"personalItemCount": 1, '
            '"cabinTrolleyCount": 0,'
            ' "checkedBaggageCount": 0'
            '}}. '
            "If user input for destination and departure "
            "matches an airport code,"
            " use that code, and the type field should be "
            "'AIRPORT'. Do not add any"
            " text, markdown, or explanation outside of the "
            "JSON block. Leave default"
            " values if data is missing. "
            f"Give results after the current_date: {TIME_NOW}"
        )

        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.1",
            messages=[
                {"role": "system", "content": instruction_prompt},
                {"role": "user", "content": ocr_text}
            ],
            temperature=0.0
        )
        match = re.search(
            r'\{.*\}',
            response.choices[0].message.content, re.DOTALL
        )
        if not match:
            raise ValueError("JSON not found!")
        return json.loads(match.group(0))

    def find_cheaper_flight(self, image_input):

        """
            Method that finds the cheaper flight.
        """

        text_extras, pret_initial = (
            self.extract_text_from_screenshot(image_input)
        )
        if not text_extras:
            return "❌ Image not found!"

        try:
            payload_dict = self.generate_json_from_ocr(text_extras)
            flights = url_gen_and_parsing.extract_flights(payload_dict)

            if not flights:
                return ("✈️ We could not find similar flights "
                        "with the ones provided by your image.")

            pret_nou = float(
                flights[0]['price'].replace(
                    '€', '').replace('\xa0', '').strip()
            )

            # CREATE THE RESPONSE MESSAGE

            msg = "🔍 *Image Analysis Image*\n"
            msg += f"💰 Price extracted from the image: {pret_initial}€\n"

            if pret_nou < pret_initial:
                msg += ("🔥 *we found a cheaper flight!"
                        f"* New price: {int(pret_nou)}€\n")
            else:
                msg += ("✅ You've found a nice deal! "
                        f"The best offer found: {pret_nou}€\n")

            f = flights[0]
            departure = f.get('departure', {})
            ret = f.get('return', {})

            dep_takeoff = departure.get('takeoff', {})
            dep_landing = departure.get('landing', {})
            ret_takeoff = ret.get('takeoff', {})
            ret_landing = ret.get('landing', {})

            msg = "*Details of the best flight:*\n"
            msg += f"*{f.get('price', 'N/A')}*\n"

            msg += (
                f"🛫 *Departure:* {departure.get('date', 'N/A')}\n"
                f"   _{dep_takeoff.get('time', 'N/A')} "
                f"({dep_takeoff.get('city', 'N/A')})_ -> "
                f"_{dep_landing.get('time', 'N/A')} "
                f"({dep_landing.get('airport', 'N/A')})_\n"
            )

            msg += (
                f"🛬 *Return:* {ret.get('date', 'N/A')}\n"
                f"   _{ret_takeoff.get('time', 'N/A')} "
                f"({ret_takeoff.get('city', 'N/A')})_ -> "
                f"_{ret_landing.get('time', 'N/A')} "
                f"({ret_landing.get('airport', 'N/A')})_\n"
            )

            msg += f"⏳ *Time:* {f.get('stay_duration', 'N/A')}\n"

            return msg

        except Exception as e:
            return f"⚠️ Error while AI processing: {str(e)}"
