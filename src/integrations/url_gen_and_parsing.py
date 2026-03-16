import json
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import datetime
import re
import time


def generate_vola_url(payload) -> str:

    # # 1. Parse the JSON string into a Python dictionary
    # try:
    #     payload = json.loads(payload_str)
    # except json.JSONDecodeError:
    #     return "Error: Invalid JSON string provided."

    base_url = "https://www.vola.ro/search_results"

    # 2. Extract Origin and Destination safely
    try:
        origin_type = payload["locations"]["origins"][0]["type"]
        origin_code = payload["locations"]["origins"][0]["code"]
        origin_str = f"{origin_type}:{origin_code}"

        dest_type = payload["locations"]["destinations"][0]["type"]
        dest_code = payload["locations"]["destinations"][0]["code"]
        
        # Handle the "Anywhere" formatting
        if dest_type == "ANYWHERE" and dest_code == "*":
            dest_str = "ANYWHERE:*"
        else:
            dest_str = f"{dest_type}:{dest_code}"
            
    except (KeyError, IndexError):
        return "Error: Payload is missing required location data."

    # 3. Base Query Parameters
    query_params = {
        "from": origin_str,
        "to": dest_str,
        # "ad": payload["passengers"].get("adults", 1),
        # "cc": "ECONOMY" # Assuming economy as default
    }

    # 4. Handle Dates (Flexible vs. Exact)
    if payload["dates"].get("anytime"):
        query_params["fdmin"] = payload["dates"]["stayTime"]["min"]
        query_params["fdmax"] = payload["dates"]["stayTime"]["max"]
    elif payload["dates"].get("departureFrom") and payload["dates"].get("departureTo") == payload["dates"].get("departureFrom") and payload["dates"].get("returnFrom") and payload["dates"].get("returnTo") == payload["dates"].get("returnFrom"):
        query_params["dd"] = payload["dates"]["departureFrom"]
        query_params["rd"] = payload["dates"]["returnFrom"]

    else:
        # If not anytime, use the exact departure and return dates
        query_params["range"] = "1"
        if payload["dates"].get("departureFrom"):
            query_params["ddfrom"] = payload["dates"]["departureFrom"]
        if payload["dates"].get("departureTo"):
            query_params["ddto"] = payload["dates"]["departureTo"]
        if payload["dates"].get("returnFrom"):
            query_params["rdfrom"] = payload["dates"]["returnFrom"]
        if payload["dates"].get("returnTo"):
            query_params["rdto"] = payload["dates"]["returnTo"]

    query_params["ad"] = payload["passengers"].get("adults", 1)

    # 5. Handle Extra Passengers
    if payload["passengers"].get("children", 0) > 0:
        query_params["ch"] = payload["passengers"]["children"]
    if payload["passengers"].get("infants", 0) > 0:
        query_params["inf"] = payload["passengers"]["infants"]

    query_params["cc"] = "ECONOMY"

    # 6. Generate and return the final URL
    return f"{base_url}?{urllib.parse.urlencode(query_params)}"

#def extract_flight_data(search_url: str):
def parse_flight_stage(stage_element):
    """
    Helper function to parse the inner details of a 'Departure' or 'Return' stage.
    Organizes data cleanly into nested takeoff/landing dictionaries.
    """
    if not stage_element:
        return None
    
    stage_data = {}
    
    # 1. Top header: Extract just the Date (e.g., "Du, 12 Apr. • Depature" -> "Du, 12 Apr.")
    header_div = stage_element.select_one('div.justify-space-between')
    raw_header = header_div.get_text(separator=" ", strip=True) if header_div else ""
    stage_data['date'] = raw_header.split('•')[0].strip() if '•' in raw_header else raw_header
    
    # 2. Timeline locations (Takeoff and Landing)
    locations = stage_element.select('div.stage-timeline-location')
    
    if len(locations) >= 2:
        # --- Takeoff Info (First node) ---
        takeoff_node = locations[0]
        raw_t_time = takeoff_node.select_one('div.stage-timeline-location__first-line')
        t_city = takeoff_node.select_one('div.frola-text-grey-800.truncate')
        t_airport = takeoff_node.select_one('div.frola-text-grey-600.truncate')
        
        # Isolate exactly the "HH:MM" time using regex
        t_time_text = raw_t_time.get_text(separator=" ", strip=True) if raw_t_time else ""
        t_time_match = re.search(r'\d{2}:\d{2}', t_time_text)
        
        stage_data['takeoff'] = {
            'time': t_time_match.group() if t_time_match else "N/A",
            'city': t_city.get_text(strip=True) if t_city else "N/A",
            'airport': t_airport.get_text(strip=True) if t_airport else "N/A"
        }
        
        # --- Landing Info (Last node) ---
        landing_node = locations[-1]
        raw_l_time = landing_node.select_one('div.stage-timeline-location__first-line')
        l_city = landing_node.select_one('div.frola-text-grey-800.truncate')
        l_airport = landing_node.select_one('div.frola-text-grey-600.truncate')
        
        # Isolate exactly the "HH:MM" time using regex
        l_time_text = raw_l_time.get_text(separator=" ", strip=True) if raw_l_time else ""
        l_time_match = re.search(r'\d{2}:\d{2}', l_time_text)
        
        stage_data['landing'] = {
            'time': l_time_match.group() if l_time_match else "N/A",
            'city': l_city.get_text(strip=True) if l_city else "N/A",
            'airport': l_airport.get_text(strip=True) if l_airport else "N/A"
        }
        
    return stage_data


def scrape_vola_flights(url: str) -> list:
    """
    Scrapes a Vola.ro search results URL using Playwright.
    Returns a list of dictionaries containing structured flight details.
    """
    scraped_flights = []

    with sync_playwright() as p:
        # Launch browser to render Nuxt JavaScript
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating and rendering: {url}")
        
        try:
            # Render page and wait for content to stabilize
            page.goto(url, wait_until="networkidle")
            
            # CRITICAL: Wait specifically for the dynamically-rendered flight cards to appear
            page.wait_for_selector('div.flight-card__details', timeout=15000)
            time.sleep(2) # brief extra pause for final text node populating

            rendered_html = page.content()
            soup = BeautifulSoup(rendered_html, 'html.parser')

            # Find all flight detail containers in the rendered DOM
            flight_details_containers = soup.select('div.flight-card__details')
            
            if not flight_details_containers:
                print("No flight cards found.")
                return scraped_flights

            # Iterate through each flight card parent
            for details_div in flight_details_containers:
                flight_data = {}
                card = details_div.parent
                
                # --- Specific extraction from rendered DOM ---

                # Language-independent parsing of Departure and Return stages
                stages = card.select('li.stage')
                
                # Outbound is always the first stage
                flight_data['departure'] = parse_flight_stage(stages[0]) if len(stages) > 0 else None
                
                # Inbound (return) is the second stage, if it exists
                flight_data['return'] = parse_flight_stage(stages[1]) if len(stages) > 1 else None

                # Stay Info (e.g. "7 days in Rome")
                stay_elem = card.select_one('li.flight-card__stay-info')
                flight_data['stay_duration'] = stay_elem.get_text(separator=" ", strip=True) if stay_elem else "N/A"

                # Extract Price cleanly from 'flight-card__actions' using RegEx
                actions_elem = card.select_one('div.flight-card__actions')
                raw_actions_text = actions_elem.get_text(separator=" ", strip=True) if actions_elem else ""
                
                # Search for the "Price:" pattern to isolate the actual cost
                price_match = re.search(r'Preț:\s*(\d+\s*€)', raw_actions_text)
                
                if price_match:
                    flight_data['price'] = price_match.group(1)
                else:
                    # Fallback to full block if regex fails (or if the site loads in English)
                    # We also add an English fallback regex just in case
                    eng_price_match = re.search(r'Price:\s*(\d+\s*€)', raw_actions_text)
                    if eng_price_match:
                        flight_data['price'] = eng_price_match.group(1)
                    else:
                         flight_data['price_raw_actions_block'] = raw_actions_text

                scraped_flights.append(flight_data)

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        
        finally:
            browser.close()

    return scraped_flights
    

json_payload_string = """
{
    "dates": {
        "departureFrom": "",
        "departureTo": "",
        "returnFrom": "",
        "returnTo": "",
        "anytime": true,
        "stayTime": {
            "min": 3,
            "max": 7
        }
    },
    "passengers": {
        "adults": 1,
        "children": 0,
        "infants": 0,
        "youth": 0
    },
    "locations": {
        "origins": [
            {"code": "BUH", "type": "CITY"}
        ],
        "destinations": [
            {"code": "ROM", "type": "CITY"}
        ]
    },
    "deduplicate": true,
    "luggageOptions": {
        "personalItemCount": 1,
        "cabinTrolleyCount": 0,
        "checkedBaggageCount": 0
    }
}
"""

def extract_flights(json_payload_string):

    url = generate_vola_url(json_payload_string)
    print(url)
    flights = scrape_vola_flights(url)
    print(f"Scraped {len(flights)} flights:")
    for idx, flight in enumerate(flights, start=1):
        print(f"\nFlight {idx}:")
        for key, value in flight.items():
            print(f"  {key}: {value}")
    return flights
