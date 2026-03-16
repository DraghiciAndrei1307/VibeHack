import base64
import io
import os
import tempfile
from PIL import Image
from openai import OpenAI
import requests

# ==========================================
# 1. API CREDENTIALS
# ==========================================
client = OpenAI(
    api_key= os.environ.get("API_KEY"),
    base_url="https://api.featherless.ai/v1" 
)

# You can use "google/gemma-3-27b-it", "google/gemma-3-11b-it", or "google/gemma-3-4b-it"
# depending on which one you accepted the agreement for.
MODEL_NAME = "google/gemma-3-27b-it"


def _download_media_to_temp(url, timeout=15):
    """Download image from URL (e.g. Twilio MediaUrl) to a temp file. Returns path."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    f.write(resp.content)
    f.close()
    return f.name


def identify_location_from_url(image_url):
    """Download image from URL, run identify_location, then delete temp file."""
    path = None
    try:
        path = _download_media_to_temp(image_url)
        return identify_location(path)
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception:
                pass


def encode_and_resize_image(image_path, max_size=(1024, 1024)):
    """Compresses the image to prevent Connection Errors and API Timeouts."""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            # Resize the image so it doesn't break the API connection
            img.thumbnail(max_size)
            
            # Save it compressed to a buffer
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"[!] Eroare la procesarea pozei: {e}")
        return None

def identify_location(image_path):
    print(f"[~] Comprim și uploadez {image_path}...")
    
    base64_image = encode_and_resize_image(image_path)
    if not base64_image:
        return "Nu am putut citi poza."

    prompt_text = (
        "You are an expert OSINT investigator and geoguesser. "
        "Examine this photo carefully and tell me where it was taken. "
        "Analyze the architecture, street signs, vegetation, weather, "
        "and landmarks. Walk me through your visual deductions step-by-step, "
        "and conclude with your best estimate of the city and country. Respond in Romanian, max 1600 characters."
    )

    # Notice that for Gemma, the text is listed BEFORE the image. 
    # This is exactly how Featherless formats multimodal requests for Gemma 3.
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ]

    print(f"[~] Send image to {MODEL_NAME} on Featherless...")
    
    try:
        chat_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1500,
            temperature=0.2,
            timeout=75.0
        )
        content = chat_response.choices[0].message.content
        return content if content else "Could not analyze the image."
    except Exception as e:
        return f"[!] API Error: {e}"

if __name__ == "__main__":
    print("=== Gemma 3 Vision OSINT Agent ===\n")
    
    target_image = input("Image path: ").strip()
    result = identify_location(target_image)
    
    print("\n=== AI Analysis ===\n")
    print(result)