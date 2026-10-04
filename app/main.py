import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            category TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def hello():
    return "IT Ticketing Platform is running!"

@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()

    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (title, description, priority, category) VALUES (%s, %s, %s, %s) RETURNING id",
        (data["title"], data.get("description", ""), data.get("priority", "MEDIUM"), data.get("category", "OTHER"))
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "status": "OPEN"}), 201

@app.route("/tickets", methods=["GET"])
def list_tickets():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, priority, category, status FROM tickets")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    tickets = []
    for row in rows:
        tickets.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "priority": row[3],
            "category": row[4],
            "status": row[5]
        })
    return jsonify(tickets)

@app.route("/tickets/<int:ticket_id>/status", methods=["PATCH"])
def update_status(ticket_id):
    data = request.get_json()
    new_status = data.get("status")

    valid_statuses = ["OPEN", "IN_PROGRESS", "RESOLVED"]
    if new_status not in valid_statuses:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET status = %s WHERE id = %s", (new_status, ticket_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": ticket_id, "status": new_status})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)