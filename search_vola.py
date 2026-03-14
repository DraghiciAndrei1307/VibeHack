import requests
from selenium import webdriver
from selenium.webdriver.common.by import By


class Prompt:
    def __init__(self, fromm, to, dep_date, ret_date, adults, dedupl, cls):
        self.fromm = fromm
        self.to = to
        self.dep_date = dep_date
        self.ret_date = ret_date
        self.adults = adults
        self.dedupl = dedupl
        self.cls = cls
        


class Request:
    def __init__(self):
        self.url = "https://api.ith.toys/gateway/discover"

        self.headers = {
            "accept": "application/json",
            "accept-language": "ro",
            "api-key": "7f6c921c-d7f8-4303-b9ad-b60878ca12ed",
            "content-type": "application/json",
            "origin": "https://www.vola.ro",
            "referer": "https://www.vola.ro/",
            "slot": "volaFW6142",
            "user-agent": "Mozilla/5.0",
            "x-affiliate": "vola",
            "x-app-origin": "new-front-end",
            "x-ab-test-token": "eyJpdiI6IkllYjE3Sm9udk9QbXFjSjZqaGpZa2c9PSIsInZhbHVlIjoibFdwU2ZMRnQyYjM5WnlzUHE5ck14UlpEWk9OTTM2OFZkcUlnaUczUUdzU1VOMWlUMDNPRzNYTWlKTU9nLzhuNVVBc0s3TDhaL3EvbWloU29XRXJNa1QrYklpTXlnZXpqcEdNWDZieTRGYXlwRFVQUDA4d0dwQjhIaWRnZ3QxSGxwa0JNbk52RUFjYU5hVW9lL1RlTTQwTkVMZ2lZaG1mYXhYUURyWFhsN2c1TWhsVmswVG15WEF2RDVxamdVQWtOZmdudUVKUXpLOVZPSnNnZUVsZEZPbW9sRjBwUTZZZ00xWk9BcmhOZlpGOEtJakFQSWw2UHkvM09LS0pTb0MrVW82bmJ4NlpYOUpjY0c2UEVWWWhZcHpKU1pidlBNaTMwZmJUR3BiL2hLSU8yUUdnUmVQVmcxYWJhc2tlRWloa1g5ZEd3Qlo5aHdNd3RFMlJuSnYrRTRWcHVmdGFUSHpJUVFHdHl1MWdNNDh1UlRkWWZoL0FWUi9CUFIrM3p4WGk0YnlBWmFpUzB4VzB0TzdZK0poQ2VkS2tLUGIrZWpmejNUYVYwUzN6N1dNL05FWUViemdIT0NLOGlweEJYT0FhcmxtdTA0SkRxMlh4QXlLdmhBZ2gwdFVpRnlkNkJvdUVGTE1MekpMYkFrY3BzNGplajcrc1dzdm94Q0dld084dWlhWXUzbHk5UzZpNnhxWEVDMVN1R3Z6RzY5Q0tydXFReHFhcVpGVHRsd2VtUUJtUWE1SnUzaTRReHRGbFNjMmM4IiwibWFjIjoiZDc1YTJlNzU5YzkwNWNhODJmMGNjMzIyZDY0MzhiMjVjYWU1MWQ2NTBjNjAxZGFjNmQ5ZDFmYmU1ZTllZmYzZiIsInRhZyI6IiJ9"
        }

        self.payload = {
            "dates": {
                "departureFrom": "",
                "departureTo": "",
                "returnFrom": "",
                "returnTo": "",
                "anytime": True,
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
                    {"code": "*", "type": "ANYWHERE"}
                ]
            },
            "deduplicate": False,
            "luggageOptions": {
                "personalItemCount": 1,
                "cabinTrolleyCount": 0,
                "checkedBaggageCount": 0
            }
        }

    def search(self, prompt):
        if prompt.fromm != None:
            self.payload["locations"]["origins"][0]["code"] = prompt.fromm
        if prompt.to != None:
            self.payload["locations"]["destinations"][0]["code"] = prompt.to
            self.payload["locations"]["destinations"][0]["type"] = "CITY"
        if prompt.dep_date != None:
            self.payload["dates"]["departureFrom"] = prompt.dep_date
            self.payload["dates"]["departureTo"] = prompt.dep_date
        if prompt.ret_date != None:
            self.payload["dates"]["returnFrom"] = prompt.ret_date
            self.payload["dates"]["returnTo"] = prompt.ret_date 
        if prompt.adults != None:
            self.payload["passengers"]["adults"] = str(prompt.adults)
        if prompt.dedupl != None:
            self.payload["deduplicate"] = prompt.dedupl


        response = requests.post(self.url, headers=self.headers, json=self.payload)
        return response.json()


prompt = Prompt("BUH", "ROM", "", "", 1, False, "ECONOMY")
client = Request()
response = client.search(prompt)
search_id = response["search"]["searchId"]
discovery_id = response["discoveryId"]
frontend_url = f"https://www.vola.ro/flight-search/{search_id}"
    
print(f"Search ID: {search_id}")
print(f"Discovery ID: {discovery_id}")
print(client.search(prompt))
print(f"Frontend URL: {frontend_url}")



