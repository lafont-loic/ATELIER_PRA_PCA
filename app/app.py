import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")

@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )

@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)

@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)

@app.route('/status')
def status():
    import os, time, sqlite3
    
    # 1. On récupère le chemin de la BDD depuis les variables d'environnement
    db_path = os.getenv('DB_PATH', '/data/app.db')
    
    # 2. On compte les messages manuellement pour éviter l'erreur 'db not defined'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute('SELECT count(*) FROM events')
        count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        count = "Error reading DB"

    # 3. On regarde les backups
    backup_dir = '/backup'
    latest_file = None
    age = None

    try:
        if os.path.exists(backup_dir):
            files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
            if files:
                latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                age = int(time.time() - os.path.getmtime(os.path.join(backup_dir, latest_file)))
    except Exception:
        pass

    return {
        "count": count,
        "last_backup_file": latest_file,
        "backup_age_seconds": age
    }
# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
