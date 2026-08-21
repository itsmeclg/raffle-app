from flask import Flask, render_template, request, Response
import sqlite3
import random
import datetime
import csv

app = Flask(__name__)

# --- Registration route ---
@app.route("/register", methods=["GET", "POST"])
def register_form():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]

        conn = sqlite3.connect("raffle.db")
        c = conn.cursor()

        # Find an unassigned QR code
        c.execute("SELECT id, code_value, image_path FROM qr_codes WHERE is_assigned = 0 LIMIT 1")
        qr = c.fetchone()

        if qr:
            qr_id, code_value, image_path = qr

            # Insert the new entry
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO entries (name, phone, qr_code_id, created_at) VALUES (?, ?, ?, ?)",
                      (name, phone, qr_id, created_at))

            # Mark the QR code as assigned
            c.execute("UPDATE qr_codes SET is_assigned = 1 WHERE id = ?", (qr_id,))

            conn.commit()
            conn.close()

            return render_template("assigned.html", image_path=image_path, code_value=code_value)
        else:
            conn.close()
            return "All QR codes have been assigned."

    return render_template("register.html")


# --- Admin dashboard route ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    search_query = request.form.get("search", "").strip()

    conn = sqlite3.connect("raffle.db")
    c = conn.cursor()

    # --- Summary stats ---
    c.execute("SELECT COUNT(*) FROM entries")
    total_entries = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM qr_codes WHERE is_assigned = 0")
    remaining_qr = c.fetchone()[0]

    # --- Search functionality ---
    if search_query:
        c.execute("""
            SELECT entries.id, name, phone, qr_codes.code_value, entries.created_at
            FROM entries
            JOIN qr_codes ON entries.qr_code_id = qr_codes.id
            WHERE name LIKE ? OR phone LIKE ? OR qr_codes.code_value LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        c.execute("""
            SELECT entries.id, name, phone, qr_codes.code_value, entries.created_at
            FROM entries
            JOIN qr_codes ON entries.qr_code_id = qr_codes.id
        """)

    rows = c.fetchall()
    conn.close()

    return render_template("admin.html", rows=rows, search_query=search_query,
                           total_entries=total_entries, remaining_qr=remaining_qr)


# --- Delete entry route ---
@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    conn = sqlite3.connect("raffle.db")
    c = conn.cursor()

    # Free up the QR code linked to this entry
    c.execute("SELECT qr_code_id FROM entries WHERE id = ?", (entry_id,))
    qr_code_id = c.fetchone()
    if qr_code_id:
        c.execute("UPDATE qr_codes SET is_assigned = 0 WHERE id = ?", (qr_code_id[0],))

    # Delete the entry
    c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

    return ("", 204)  # Empty response for AJAX delete

# --- Edit entry route ---
@app.route("/edit/<int:entry_id>", methods=["POST"])
def edit_entry(entry_id):
    name = request.form.get("name")
    phone = request.form.get("phone")

    conn = sqlite3.connect("raffle.db")
    c = conn.cursor()
    c.execute("UPDATE entries SET name = ?, phone = ? WHERE id = ?", (name, phone, entry_id))
    conn.commit()
    conn.close()

    return ("", 204)


# --- CSV export route ---
@app.route("/export")
def export_csv():
    conn = sqlite3.connect("raffle.db")
    c = conn.cursor()
    c.execute("""
        SELECT entries.id, name, phone, qr_codes.code_value, entries.created_at
        FROM entries
        JOIN qr_codes ON entries.qr_code_id = qr_codes.id
    """)
    rows = c.fetchall()
    conn.close()

    output = []
    output.append(["ID", "Name", "Phone", "QR Number", "Created At"])
    output.extend(rows)

    def generate():
        for row in output:
            yield ",".join(map(str, row)) + "\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=raffle_entries.csv"})


# --- Run the app ---
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
