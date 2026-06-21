import sqlite3

conn = sqlite3.connect("rvdss.db")
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS library(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file TEXT
)
''')

conn.commit()
conn.close()

print("Library table created ✅")