import sqlite3
from datetime import datetime

def mark_attendance(name):

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS attendance
                      (name TEXT, date TEXT, time TEXT)""")

    now = datetime.now()

    cursor.execute("INSERT INTO attendance VALUES (?,?,?)",
                   (name, now.date(), now.time()))

    conn.commit()
    conn.close()