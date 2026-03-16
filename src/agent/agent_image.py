import json
import os
import re
import sys
from io import BytesIO
import sys

import requests
from PIL import Image
import easyocr
from openai import OpenAI
from datetime import datetime   

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import integrations.url_gen_and_parsing as url_gen_and_parsing

reader = easyocr.Reader(['en', 'ro'],gpu = True)

class AgentImage:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key= os.environ.get("API_KEY")
        )

    def extrage_text_din_poza(self, image_url: str):
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

    def genereaza_json_din_ocr(self, ocr_text: str) -> dict:
        TIME_NOW = datetime.now()
        instruction_prompt = (
            "You are an expert travel data parser. I will provide you with raw, messy OCR text extracted from a flight screenshot. "
            "Your job is to ignore the garbage characters (like '«', '2?', 'x') and extract the origin city, destination city, and stay duration. "
            "1. Convert city names to their 3-letter IATA codes (e.g., Bucharest -> BUH, Rome -> ROM, Larnaca -> LCA). "
            "2. If you see a stay duration like '4 nights', set 'stayTime' min and max to 4. "
            "3. Return ONLY a valid JSON using double quotes, with the following structure: "
            '{"dates": {"departureFrom": "", "departureTo": "", "returnFrom": "", "returnTo": "", "anytime": false, "stayTime": {"min": "", "max": ""}}, '
            '"passengers": {"adults": 1, "children": 0, "infants": 0, "youth": 0}, '
            '"locations": {"origins": [{"code": "BUH", "type": "CITY"}], "destinations": [{"code": "*", "type": "ANYWHERE"}]}, '
            '"deduplicate": false, '
            '"luggageOptions": {"personalItemCount": 1, "cabinTrolleyCount": 0, "checkedBaggageCount": 0}}. '
            "If user input for destination and departure matches an airport code, use that code, and the type field should be 'AIRPORT'. Do not add any text, markdown, or explanation outside of the JSON block. Leave default values if data is missing. "
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

        match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        if not match: raise ValueError("JSON not found!")
        return json.loads(match.group(0))

    def find_cheaper_flight(self, image_input):
        text_extras, pret_initial = self.extrage_text_din_poza(image_input)
        if not text_extras:
            return "❌ Image not found!"

        try:
            payload_dict = self.genereaza_json_din_ocr(text_extras)
            flights = url_gen_and_parsing.extract_flights(payload_dict)

            if not flights:
                return "✈️ We could not find similar flights with the ones provided by your image."

            pret_nou = float(flights[0]['price'].replace('€', '').replace('\xa0', '').strip())

            # CREATE THE RESPONSE MESSAGE

            msg = f"🔍 *Image Analysis Image*\n"
            msg += f"💰 Price extracted from the image: {pret_initial}€\n"

            if pret_nou < pret_initial:
                msg += f"🔥 *we found a cheaper flight!* New price: {int(pret_nou)}€\n"
            else:
                msg += f"✅ You've found a nice deal! The best offer found: {pret_nou}€\n"

            f = flights[0]
            departure = f.get('departure') or {}
            ret = f.get('return') or {}
            msg += "\n*Details of the best flight:*\n"
            msg += f"*{f.get('price', 'N/A')}*\n"
            msg += f"🛫 *Departure:* {departure.get('date', 'N/A')}\n"
            msg += f"   _{departure.get('takeoff', {}).get('time', 'N/A')} ({departure.get('takeoff', {}).get('city', 'N/A')})_ -> "
            msg += f"_{departure.get('landing', {}).get('time', 'N/A')} ({departure.get('landing', {}).get('airport', 'N/A')})_\n"
            msg += f"🛬 *Return:* {ret.get('date', 'N/A')}\n"
            msg += f"   _{ret.get('takeoff', {}).get('time', 'N/A')} ({ret.get('takeoff', {}).get('city', 'N/A')})_ -> "
            msg += f"_{ret.get('landing', {}).get('time', 'N/A')} ({ret.get('landing', {}).get('airport', 'N/A')})_\n"
            msg += f"⏳ *Time:* {f.get('stay_duration', 'N/A')}\n"
            return msg

        except Exception as e:
            return f"⚠️ Error while AI processing: {str(e)}"