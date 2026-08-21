import qrcode
import sqlite3
import os

# Create the folder for QR images if it doesn't exist
os.makedirs("static/qr", exist_ok=True)

# Connect to the SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect("raffle.db")
c = conn.cursor()

# Create both tables if they don't exist
c.execute("""
CREATE TABLE IF NOT EXISTS qr_codes (
    id INTEGER PRIMARY KEY,
    code_value INTEGER,
    image_path TEXT,
    is_assigned INTEGER DEFAULT 0,
    assigned_to_entry_id INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    qr_code_id INTEGER,
    created_at TEXT
)
""")

# Generate 500 QR codes and store them in the database
for i in range(1, 501):
    img = qrcode.make(str(i))
    path = f"static/qr/{i}.png"
    img.save(path)
    c.execute("INSERT INTO qr_codes (code_value, image_path) VALUES (?, ?)", (i, path))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Generated 500 QR codes and populated database.")
