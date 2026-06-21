import sqlite3

conn = sqlite3.connect("rvdss.db")
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS alerts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT
)
''')

conn.commit()
conn.close()

print("Alerts table created ✅")