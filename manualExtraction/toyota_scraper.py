import re
import requests
from playwright.sync_api import Playwright, sync_playwright, expect
import sqlite3
import os

def run(playwright: Playwright) -> None:
    db_path = 'vehicles.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE models ADD COLUMN local_path TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        SELECT model_id, model_name, year 
        FROM models 
        WHERE make_id = (SELECT make_id FROM makes WHERE make_name = 'TOYOTA')
        AND local_path IS NULL
    """)
    toyota_models = cursor.fetchall()

    target_folder = os.path.join("manuals", "toyota")
    os.makedirs(target_folder, exist_ok=True)


    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    pub_pattern = re.compile(r'[A-Z]{2}\d{5}[A-Z]')

    for m_id, db_model, db_year in toyota_models:
        search_model = str(db_model).title()
        search_year = str(db_year)

        print(f"--- Processing {search_year} {search_model} ---")
        
        try:
            page.goto("https://www.toyota.com/owners/warranty-owners-manuals/", wait_until="networkidle")
            
            try:
                page.get_by_role("button", name="Accept").click(timeout=3000)
            except:
                pass 

            browse_btn = page.get_by_role("link").filter(has_text="Browse Vehicles")
            browse_btn.wait_for(state="visible", timeout=10000)
            browse_btn.click()
            
            page.locator("select[name=\"model\"]").select_option(label=search_model)
            page.locator("select[name=\"year\"]").select_option(label=search_year)
            page.get_by_role("button", name="Continue").click()
            
            page.wait_for_selector("text=View PDF", timeout=15000)

            target_link = None

            old_layout_box = page.locator("#ownerssmanual")
            if old_layout_box.count() > 0:
                target_link = old_layout_box.get_by_role("link").filter(has_text="View PDF").first
            
            if not target_link:
                pdf_links = page.locator("a").filter(has_text="View PDF")
                for i in range(pdf_links.count()):
                    container_text = pdf_links.nth(i).locator("xpath=..").inner_text()
                    if pub_pattern.search(container_text) or "Owner's Manual" in container_text:
                        target_link = pdf_links.nth(i)
                        break
                
                if not target_link and pdf_links.count() > 0:
                    target_link = pdf_links.first

            if target_link:
                with page.expect_popup() as page1_info:
                    target_link.scroll_into_view_if_needed()
                    target_link.click(force=True)
                
                page1 = page1_info.value
                page1.wait_for_load_state()
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
                page1.close()
            else:
                print(f"No PDF found for {search_model}")

        except Exception as e:
            print(f"Error skipping {search_model}: {e}")
            page.goto("about:blank")

    context.close()
    browser.close()
    conn.close()
    print("All tasks finished.")

with sync_playwright() as playwright:
    run(playwright)