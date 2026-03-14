import json
import re
from PIL import Image
import pytesseract
from openai import OpenAI
from datetime import datetime   

# Presupunem că acest fișier există deja în folderul tău
import url_gen_and_parsing 


# --- Configurare OpenAI (Featherless) ---
client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="rc_d19a3d709759a2023185f5d7f7c0d0386791612fbf32d028a79603cae7e7d763"
)

def extrage_text_din_poza(image_path: str) -> str:
    """
    Folosește Tesseract pentru a extrage textul brut dintr-o imagine.
    """
    try:
        img = Image.open(image_path)
        print(f"\n[~] Extrag textul din {image_path} (OCR)...")
        extrase = pytesseract.image_to_string(img).strip()
        #€
        p = re.split(r'€|\$|lei', extrase)
        pret_initial = float(p[1])
        # print(f"pret_initial: {pret_initial}")

        return extrase, pret_initial

    except Exception as e:
        print(f"[!] Eroare la citirea imaginii: {e}")
        return None

def genereaza_json_din_ocr(ocr_text: str) -> dict:
    """
    Trimite textul OCR către DeepSeek pentru a extrage intenția de zbor
    și a o formata în JSON-ul cerut.
    """
    TIME_NOW = datetime.now()
    
    # Prompt-ul a fost adaptat special pentru a ignora "gunoiul" din OCR și a extrage esențialul
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

    print("[~] Trimit textul către DeepSeek pentru analiză și formatare...")
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.1",
        messages=[
            {"role": "system", "content": instruction_prompt},
            {"role": "user", "content": f"Raw OCR Text to analyze:\n{ocr_text}"}
        ],
        max_tokens=400,
        temperature=0.0 # Temperatură 0 pentru a forța modelul să fie strict și analitic
    )

    payload = response.choices[0].message.content
    
    # Curățare: extragem doar JSON-ul dintre acolade
    match = re.search(r'\{.*\}', payload, re.DOTALL)
    if not match:
        print("Raw payload a fost:", payload)
        raise ValueError("Nu am putut găsi JSON în răspunsul modelului.")

    json_str = match.group(0)
    return json.loads(json_str)

if __name__ == '__main__':
    print("=== Agent AI pentru Căutare Zboruri din Poze ===")
    
    while True:
        # 1. Cerem poza
        image_input = input("\nIntrodu calea către poza cu zborul (sau 'exit'): ").strip()
        
        if image_input.lower() == "exit":
            break
            
        # 2. Extragem textul
        text_extras, pret_initial = extrage_text_din_poza(image_input)
        if not text_extras:
            continue
            
        print("\n--- Text OCR (Ce a văzut scriptul) ---")
        print(text_extras)
        print("--------------------------------------\n")
        
        try:
            # 3. Analiză AI
            payload_dict = genereaza_json_din_ocr(text_extras)
            
            print("[+] JSON Generat de AI cu succes:")
            print(json.dumps(payload_dict, indent=2))
            
            # 4. Apelăm funcția ta originală
            print("\n[~] Apeleaz url_gen_and_parsing.extract_flights()...")
            flights = url_gen_and_parsing.extract_flights(payload_dict)
            pret_nou = float(flights[0]['price'].replace('€', '').strip())
            # print(f"pret_nou: {pret_nou}")
            # print(type(pret_nou))
            # print(type(pret_initial))
            # print(pret_initial)
            if pret_nou < pret_initial:
                print(f"\n[!] Am găsit un preț mai mic decât cel inițial!")
            
        except Exception as e:
            print(f"[!] A apărut o eroare în timpul procesării: {e}")