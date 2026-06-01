from flask import Flask, render_template, request, jsonify
from agents.signal_agent import run_signal_agent
from utils.db import get_db
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    match_result = request.json.get("match_result", "")
    if not match_result:
        return jsonify({"error": "No match result provided"}), 400
    try:
        report = run_signal_agent(match_result)
        if not report:
            report = "Report generated successfully. Check history for details."
        return jsonify({"report": report})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/history")
def history():
    db = get_db()
    reports = list(db.signal_reports.find().sort("created_at", -1).limit(10))
    for r in reports:
        r["_id"] = str(r["_id"])
    return jsonify(reports)

if __name__ == "__main__":
    app.run(debug=True)