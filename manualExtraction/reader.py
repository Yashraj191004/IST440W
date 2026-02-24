import fitz
import re
import os
import json
import sqlite3

# ==================================================
# CONFIGURATION & REGEX
# ==================================================

OIL_PATTERN = r"\b\d{1,2}W-?\d{2}\b"
ENGINE_PATTERN = r"\b\d\.\dL\b|\bV6\b|\bV8\b|\bI4\b|\b4-cylinder\b|\b6-cylinder\b"

# ==================================================
# HELPERS & CLEANING
# ==================================================

def clean_ocr(text):
    """Fixes common OCR errors where 0 is read as O."""
    text = re.sub(r"\bOW-(\d{2})\b", r"0W-\1", text)
    text = re.sub(r"\b1OW-(\d{2})\b", r"10W-\1", text)
    text = re.sub(r"\b(\d)O(W-?\d{2})\b", r"\g<1>0\g<2>", text)
    return text

def f_to_c(f):
    """Converts Fahrenheit to Celsius for standardized data."""
    return round((f - 32) * 5 / 9)

# ==================================================
# EXTRACTION & CLASSIFICATION LOGIC
# ==================================================

def extract_vehicle_info(full_text, expected_make, expected_model, expected_year):
    """Verifies if the manual text matches the database record."""
    year_found = str(expected_year) in full_text
    make_found = re.search(rf"\b{re.escape(expected_make)}\b", full_text, re.IGNORECASE) is not None
    model_found = re.search(rf"\b{re.escape(expected_model)}\b", full_text, re.IGNORECASE) is not None

    engine_match = re.search(ENGINE_PATTERN, full_text, re.IGNORECASE)
    engine = engine_match.group(0) if engine_match else None

    return {
        "verified": year_found and make_found and model_found,
        "engine": engine
    }

def extract_temperature(text):
    """Extracts temperature conditions from the context of an oil mention."""
    match = re.search(r"(below|above|under|over)\s*(-?\d+)\s*°?\s*F", text, re.IGNORECASE)
    if match:
        direction = match.group(1).lower()
        f_value = int(match.group(2))
        return { direction: {"value": f_to_c(f_value), "unit": "degreeCelsius"} }
    return "normal"

def classify(context):
    """Determines if the oil mentioned is recommended or restricted."""
    lower = context.lower()
    if re.search(r"(do not use|avoid|never use)", lower):
        return False
    if any(k in lower for k in ["recommended", "should use", "is best", "consider"]):
        return True
    return None

# ==================================================
# DATABASE UPDATE ENGINE
# ==================================================

def update_database_with_oil_info(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Prepare database columns (adding engine_type as well for extra utility)
    try:
        cursor.execute("ALTER TABLE models ADD COLUMN oil_data TEXT")
        cursor.execute("ALTER TABLE models ADD COLUMN engine_type TEXT")
        print("Columns added successfully (or already exist).")
    except sqlite3.OperationalError:
        pass 

    # Query pulls path directly from 'local_path'
    query = """
        SELECT m.id, m.local_path, mk.make_name, m.model_name, m.year 
        FROM models m
        JOIN makes mk ON m.make_id = mk.make_id
        WHERE m.local_path IS NOT NULL
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        print("No records with 'local_path' found in the database.")
        return

    for m_id, manual_path, db_make, db_model, db_year in rows:
        # Check if the file path from the DB actually exists on the drive
        if not os.path.exists(manual_path):
            print(f"Skipping ID {m_id}: File not found at '{manual_path}'")
            continue

        print(f"Processing ID {m_id}: {db_year} {db_make} {db_model}...")
        
        oil_results = {}
        detected_engine = None

        try:
            with fitz.open(manual_path) as doc:
                full_text = ""
                for page in doc:
                    full_text += clean_ocr(page.get_text("text")) + "\n"

                # 1. Verification
                v_info = extract_vehicle_info(full_text, db_make, db_model, db_year)
                detected_engine = v_info["engine"]

                if not v_info["verified"]:
                    print(f"  ⚠️ Content Check Failed: Keywords for {db_year} {db_make} {db_model} not found in PDF.")

                # 2. Extract Oil Details
                lines = full_text.split("\n")
                for i, line in enumerate(lines):
                    oils = re.findall(OIL_PATTERN, line, re.IGNORECASE)
                    if not oils:
                        continue

                    # Get 7-line context window
                    context = " ".join(lines[max(0, i-3):i+4])
                    rec = classify(context)
                    temp = extract_temperature(context)

                    if rec is not None:
                        for oil in oils:
                            # Standardize format to '0W-20'
                            oil_key = oil.upper().replace("W", "W-") if "-" not in oil.upper() else oil.upper()
                            oil_results[oil_key] = {
                                "recommended": rec,
                                "temp_condition": temp
                            }

            # 3. Update the DB for this specific record
            cursor.execute("""
                UPDATE models 
                SET oil_data = ?, engine_type = ?
                WHERE id = ?
            """, (json.dumps(oil_results), detected_engine, m_id))
            
            conn.commit()
            print(f"  ✅ Data saved for ID {m_id}")

        except Exception as e:
            print(f"  ❌ Error processing '{manual_path}': {e}")

    conn.close()
    print("\nExtraction process finished.")

# ==================================================
# EXECUTION
# ==================================================

if __name__ == "__main__":
    # Point this to your vehicles.db file
    TARGET_DB = "vehicles.db" 
    update_database_with_oil_info(TARGET_DB)