import requests
import sqlite3
import time

conn = sqlite3.connect('vehicles.db')
cursor = conn.cursor()

def fetch_makes():
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/car?format=json"
    try: 
        r = requests.get(url).json()
        # print(r)
        results = r.get('Results', [])
        for item in results:
            cursor.execute('''
                insert or ignore into makes (make_id, make_name)
                        values (?, ?)
            ''', (item['MakeId'], item['MakeName']))
        conn.commit()
        print("All good")
    except Exception as e:
        print("error")
    finally:
        conn.close()

def fetch_models():
    years = list(range(2000, 2027))
    cursor.execute("select make_id, make_name from makes")
    all_makes = cursor.fetchall()
    
    for make_id, make_name in all_makes:
        for year in years:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeIdYear/makeId/{make_id}/modelyear/{year}?format=json"
            try:
                r = requests.get(url)
                
                if r.status_code == 403:
                    print(f"Rate limit hit! Sleeping for 30 seconds...")
                    time.sleep(30)
                    continue
                
                response_data = r.json()
                
                models = response_data.get('Results', [])
                if not models:
                    
                    continue
                
                model_data = []
                for m in models:
                    row = (m['Model_ID'], m['Make_ID'], m['Model_Name'], year)
                    model_data.append(row)
                
                cursor.executemany('''
                    insert or ignore into models (model_id, make_id, model_name, year)
                    values (?, ?, ?, ?)
                ''', model_data)
                
                conn.commit()
                print(f"Saved {make_name} {year}")
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error on {make_name} {year}: {e}")

# fetch_makes()
fetch_models()
print("all models done")