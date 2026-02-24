import re
import os
import sqlite3
import requests
from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> None:
    db_path = 'vehicles.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT model_id, model_name, year 
        FROM models 
        WHERE make_id = (SELECT make_id FROM makes WHERE make_name = 'TOYOTA')
        AND local_path IS NULL
    """)
    toyota_models = cursor.fetchall()

    target_folder = os.path.join("manuals", "toyota")
    os.makedirs(target_folder, exist_ok=True)

    # --- 2. The Loop ---
    for m_id, db_model, db_year in toyota_models:
        search_model = str(db_model).title()
        search_year = str(db_year)

        print(f"--- Processing {search_year} {search_model} (Fresh Start) ---")
        
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://www.toyota.com/owners/warranty-owners-manuals/")
            
            try:
                page.get_by_role("button", name="Accept").click(timeout=3000)
            except:
                pass 

            browse_btn = page.get_by_role("link").filter(has_text="Browse Vehicles")
            browse_btn.wait_for(state="visible", timeout=10000)
            browse_btn.click()

            page.locator("select[name=\"model\"]").select_option(search_model)
            page.locator("select[name=\"year\"]").select_option(search_year)
            page.get_by_role("button", name="Continue").click()
            
            with page.expect_popup() as page1_info:
                page.wait_for_selector("#ownerssmanual", timeout=1000)
                page.locator("#ownerssmanual").get_by_role("link").filter(has_text="View PDF").click()
            
            page1 = page1_info.value
            pdf_url = page1.url 
            
            file_name = f"Toyota_{search_model}_{search_year}.pdf".replace(" ", "_")
            save_path = os.path.join(target_folder, file_name)
            
            response = requests.get(pdf_url)
            with open(save_path, 'wb') as f:
                f.write(response.content)

            cursor.execute("""
                UPDATE models SET local_path = ? 
                WHERE model_id = ? AND year = ?
            """, (save_path, m_id, db_year))
            conn.commit()

            print(f"Success: {save_path}")

        except Exception as e:
            print(f"Error for {search_model}: {e}")
        
        finally:
            context.close()
            browser.close()

    conn.close()

with sync_playwright() as playwright:
    run(playwright)