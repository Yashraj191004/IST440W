import os
import time
import requests
from google import genai
from google.genai import types
from api_key import apiKey

# Setup
os.environ["GOOGLE_API_KEY"] = apiKey

client = genai.Client()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "manualsGemini")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_car_manual(url: str, filename: str):
    clean_filename = filename.replace(" ", "_")
    path = os.path.join(DOWNLOAD_FOLDER, clean_filename)

    try:
        print(f"[*] Downloading: {url}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(path, "wb") as f:
            f.write(response.content)

        print(f"[+] Saved to {path}")

    except Exception as e:
        print(f"[!] Download failed: {e}")


def run():
    cars = [
        "Toyota Camry 2020",
        "Toyota 4Runner 2001",
        "Toyota Solara 2005"
    ]

    for car in cars:
        print(f"\n[>] Searching for: {car}")

        prompt = (
            f"Give me the owners manuals of {car} in pdf format"
            f"Return ONLY the direct PDF URL. No explanation."
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )

            pdf_url = response.text.strip()
            print("Found URL:", pdf_url)

            if pdf_url.startswith("http"):
                download_car_manual(pdf_url, f"{car}.pdf")
            else:
                print("[!] No valid PDF URL found.")

            time.sleep(5)

        except Exception as e:
            print(f"[!] Error: {e}")

    print("\nDone.")


if __name__ == "__main__":
    run()