"""
Smart Energy Tracker — Flask API
Run: python app.py
Endpoints:
  GET    /api/entries              list all entries (optional ?type=electricity|water&days=N)
  POST   /api/entries              add entry          { date, type, amount, note }
  DELETE /api/entries/<id>         delete entry
  GET    /api/dashboard            summary stats + last-7-day chart data
  GET    /api/trends?view=weekly|monthly   grouped trend data
  GET    /api/bill?period=7|30|all&elec_rate=&water_rate=&fixed=   bill estimate
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from database import init_db, get_db
from datetime import date, timedelta
import traceback

app = Flask(__name__)
CORS(app)          # allows the HTML file to call the API when opened directly in a browser

# ── Init ──────────────────────────────────────────────────────────────────────

@app.before_request
def _ensure_db():
    pass   # DB is initialised at startup; nothing extra needed per-request

# ── Entries ───────────────────────────────────────────────────────────────────

@app.route("/api/entries", methods=["GET"])
def list_entries():
    type_filter = request.args.get("type")        # electricity | water | None
    days_filter = request.args.get("days", type=int)   # integer number of days

    db = get_db()
    query = "SELECT * FROM entries"
    params = []
    conditions = []

    if type_filter:
        conditions.append("type = ?")
        params.append(type_filter)
    if days_filter:
        cutoff = (date.today() - timedelta(days=days_filter)).isoformat()
        conditions.append("date >= ?")
        params.append(cutoff)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date DESC, id DESC"

    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/entries", methods=["POST"])
def add_entry():
    body = request.get_json(force=True)
    entry_date = body.get("date")
    entry_type = body.get("type")
    amount     = body.get("amount")
    note       = body.get("note", "")

    # Basic validation
    if not entry_date or entry_type not in ("electricity", "water"):
        return jsonify({"error": "Invalid date or type"}), 400
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a positive number"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO entries (date, type, amount, note) VALUES (?, ?, ?, ?)",
        (entry_date, entry_type, amount, note)
    )
    db.commit()

    new_row = db.execute("SELECT * FROM entries WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(new_row)), 201


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    db = get_db()
    row = db.execute("SELECT id FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Entry not found"}), 404
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    return jsonify({"deleted": entry_id})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    db   = get_db()
    today = date.today()

    def cutoff(days):
        return (today - timedelta(days=days)).isoformat()

    def sum_type(type_, days=None):
        if days:
            rows = db.execute(
                "SELECT COALESCE(SUM(amount),0) as s FROM entries WHERE type=? AND date>=?",
                (type_, cutoff(days))
            ).fetchone()
        else:
            rows = db.execute(
                "SELECT COALESCE(SUM(amount),0) as s FROM entries WHERE type=?",
                (type_,)
            ).fetchone()
        return rows["s"]

    def count_days(type_, days):
        rows = db.execute(
            "SELECT COUNT(DISTINCT date) as c FROM entries WHERE type=? AND date>=?",
            (type_, cutoff(days))
        ).fetchone()
        return rows["c"] or 1  # avoid division by zero

    elec_7  = sum_type("electricity", 7)
    water_7 = sum_type("water", 7)
    elec_30 = sum_type("electricity", 30)
    water_30= sum_type("water", 30)
    total_entries = db.execute("SELECT COUNT(*) as c FROM entries").fetchone()["c"]

    avg_elec  = round(elec_7  / count_days("electricity", 7),  1)
    avg_water = round(water_7 / count_days("water",        7),  0)
    est_bill  = round(elec_30 * 11.80 + water_30 * 0.035 + 150, 2)

    # Last-7-days per-day breakdown for bar charts
    daily_elec  = {}
    daily_water = {}
    for i in range(6, -1, -1):
        ds = (today - timedelta(days=i)).isoformat()
        daily_elec[ds]  = 0.0
        daily_water[ds] = 0.0

    rows = db.execute(
        "SELECT date, type, SUM(amount) as total FROM entries WHERE date >= ? GROUP BY date, type",
        (cutoff(7),)
    ).fetchall()
    for r in rows:
        if r["date"] in daily_elec:
            if r["type"] == "electricity":
                daily_elec[r["date"]]  = round(r["total"], 1)
            else:
                daily_water[r["date"]] = round(r["total"], 0)

    days_sorted = sorted(daily_elec.keys())
    return jsonify({
        "summary": {
            "avg_daily_electricity": avg_elec,
            "avg_daily_water":       int(avg_water),
            "est_monthly_bill":      est_bill,
            "total_entries":         total_entries,
        },
        "chart": {
            "labels":      [d for d in days_sorted],
            "electricity": [daily_elec[d]  for d in days_sorted],
            "water":       [daily_water[d] for d in days_sorted],
        }
    })


# ── Trends ────────────────────────────────────────────────────────────────────

@app.route("/api/trends", methods=["GET"])
def trends():
    view = request.args.get("view", "weekly")   # weekly | monthly
    db   = get_db()

    if view == "monthly":
        # Group by YYYY-MM
        rows = db.execute(
            "SELECT strftime('%Y-%m', date) as key, type, SUM(amount) as total "
            "FROM entries GROUP BY key, type ORDER BY key"
        ).fetchall()
    else:
        # Group by ISO week start (Monday)
        rows = db.execute(
            """
            SELECT
              date(date, 'weekday 1', '-7 days') as key,
              type,
              SUM(amount) as total
            FROM entries
            GROUP BY key, type
            ORDER BY key
            """,
        ).fetchall()

    # Pivot into {key: {electricity:x, water:y}}
    map_ = {}
    for r in rows:
        k = r["key"]
        if k not in map_:
            map_[k] = {"electricity": 0.0, "water": 0.0}
        map_[k][r["type"]] = round(r["total"], 1)

    keys = sorted(map_.keys())[-12:]   # last 12 periods
    return jsonify({
        "labels":      keys,
        "electricity": [map_[k]["electricity"] for k in keys],
        "water":       [map_[k]["water"]       for k in keys],
    })


# ── Bill estimator ────────────────────────────────────────────────────────────

@app.route("/api/bill", methods=["GET"])
def bill():
    elec_rate = float(request.args.get("elec_rate", 11.80))
    water_rate= float(request.args.get("water_rate", 0.035))
    fixed     = float(request.args.get("fixed", 150))
    period    = request.args.get("period", "30")  # "7", "30", or "all"

    db = get_db()

    if period == "all":
        where, params = "", []
    else:
        cutoff = (date.today() - timedelta(days=int(period))).isoformat()
        where  = "AND date >= ?"
        params = [cutoff]

    def total(type_):
        row = db.execute(
            f"SELECT COALESCE(SUM(amount),0) as s FROM entries WHERE type=? {where}",
            [type_] + params
        ).fetchone()
        return row["s"]

    total_elec  = total("electricity")
    total_water = total("water")
    cost_elec   = round(total_elec  * elec_rate,  2)
    cost_water  = round(total_water * water_rate, 2)
    total_bill  = round(cost_elec + cost_water + fixed, 2)

    return jsonify({
        "total":       total_bill,
        "electricity": {"kwh": round(total_elec, 1),  "cost": cost_elec},
        "water":       {"liters": round(total_water, 0), "cost": cost_water},
        "fixed":       fixed,
    })


# ── Error handler ─────────────────────────────────────────────────────────────

@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return "", 204
# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("✅  DB initialised.  Starting server on http://localhost:5000")
    app.run(debug=True, port=5000)
