import sqlite3

conn = sqlite3.connect('vehicles.db')
cursor = conn.cursor()

cursor.execute('''
    create table if not exists makes(
               make_id integer primary key,
               make_name text not null
               )
''')

# cursor.execute('''
#     create table if not exists models(
#         id integer primary key autoincrement,
#         model_id integer,
#         make_id integer, 
#         model_name text,
#         year integer,
#         unique(model_id, year)
#         foreign key (make_id) references makes (make_id)
#         )
# ''')

# cursor.execute("DROP TABLE IF EXISTS models")

# 2. Create the new table with the correct constraints
cursor.execute('''
    CREATE TABLE if not exists models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id INTEGER,
        make_id INTEGER,
        model_name TEXT,
        year INTEGER,
        local_path TEXT,
        FOREIGN KEY (make_id) REFERENCES makes (make_id),
        UNIQUE(model_id, year) 
    )
''')
conn.commit()
conn.close()
print("completed")
