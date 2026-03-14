from PIL import Image
import pytesseract

def extract_text_from_image(image_path):
    try:
        # 1. Open the image using Pillow
        img = Image.open(image_path)

        print("Extracting text. This might take a second...")
        extracted_text = pytesseract.image_to_string(img)
        
        return extracted_text

    except Exception as e:
        return f"An error occurred: {e}"


if __name__ == "__main__":
    
    image_file = "Screenshot 2026-03-14 154321.png" 
    
    text = extract_text_from_image(image_file)
    
    print("\n--- Extracted Text ---\n")
    print(text)