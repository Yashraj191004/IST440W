import os
import sqlite3
import time
import requests
from google import genai
from google.genai import types
from api_key import apiKey

os.environ["GOOGLE_API_KEY"] = apiKey

client = genai.Client()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "manuals")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_car_manual(url: str, filename: str):
    clean_filename = filename.replace(" ", "_")
    path = os.path.join(DOWNLOAD_FOLDER, clean_filename)

    try:
        print(f"[*] Downloading: {url}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Validate PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            print("[!] URL did not return a PDF.")
            return None

        with open(path, "wb") as f:
            f.write(response.content)

        print(f"[+] Saved to {path}")
        return path

    except Exception as e:
        print(f"[!] Download failed: {e}")
        return None


def run_automation():

    db_path = "vehicles.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "ALTER TABLE models ADD COLUMN looked_up INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()

    query = """
        SELECT makes.make_name, models.model_name, models.year, models.model_id
        FROM models
        JOIN makes ON models.make_id = makes.make_id
        WHERE models.local_path IS NULL AND models.looked_up = 0
    """

    cursor.execute(query)
    cars = cursor.fetchall()

    if not cars:
        print("No new cars to process.")
        conn.close()
        return

    for make, model_name, year, m_id in cars:

        car_full_name = f"{year} {make} {model_name}"
        print(f"\n[>] Processing: {car_full_name}")

        prompt = (
            f"Give me the owners manuals of {car_full_name} in pdf format"
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

            saved_path = None

            if pdf_url.startswith("http"):
                filename = f"{make}_{model_name}_{year}.pdf"
                saved_path = download_car_manual(pdf_url, filename)
            else:
                print("[!] No valid URL returned.")

            cursor.execute(
                "UPDATE models SET looked_up = 1 WHERE model_id = ?",
                (m_id,),
            )

            if saved_path:
                cursor.execute(
                    "UPDATE models SET local_path = ? WHERE model_id = ?",
                    (saved_path, m_id),
                )
                print("[*] Database updated with local path.")

            conn.commit()

            time.sleep(5)

        except Exception as e:
            print(f"[!] Error: {e}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run_automation()