from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wellbeing.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")  # for flash msgs

db = SQLAlchemy(app)

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    stress = db.Column(db.Integer, nullable=False)           # 1-10
    workload = db.Column(db.Integer, nullable=False)         # 1-10
    satisfaction = db.Column(db.Integer, nullable=False)     # 1-10
    notes = db.Column(db.Text, nullable=True)

    def as_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "stress": self.stress,
            "workload": self.workload,
            "satisfaction": self.satisfaction,
            "notes": self.notes or ""
        }

def compute_metrics():
    """Compute averages and the overall Wellbeing Score (0-100)."""
    avg_stress = db.session.query(func.avg(SurveyResponse.stress)).scalar() or 0.0
    avg_workload = db.session.query(func.avg(SurveyResponse.workload)).scalar() or 0.0
    avg_satisfaction = db.session.query(func.avg(SurveyResponse.satisfaction)).scalar() or 0.0

    # Weighted wellbeing score
    wellbeing_score = (
        ((10 - avg_stress) * 0.4) +
        ((10 - avg_workload) * 0.2) +
        (avg_satisfaction * 0.4)
    ) * 10  # scale to 0-100
    wellbeing_score = round(max(0, min(100, wellbeing_score)), 2)

    return {
        "avg_stress": round(avg_stress, 2),
        "avg_workload": round(avg_workload, 2),
        "avg_satisfaction": round(avg_satisfaction, 2),
        "wellbeing_score": wellbeing_score
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        stress = int(request.form.get("stress", 0))
        workload = int(request.form.get("workload", 0))
        satisfaction = int(request.form.get("satisfaction", 0))
        notes = request.form.get("notes", "").strip()

        # basic validation
        for val in (stress, workload, satisfaction):
            if val < 1 or val > 10:
                raise ValueError("All scores must be in 1-10.")

        entry = SurveyResponse(
            stress=stress,
            workload=workload,
            satisfaction=satisfaction,
            notes=notes
        )
        db.session.add(entry)
        db.session.commit()
        flash("Thanks! Your response was recorded.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    # Fetch last 30 responses
    recent = SurveyResponse.query.order_by(SurveyResponse.created_at.desc()).limit(30).all()
    recent = list(reversed(recent))  # chronological order

    metrics = compute_metrics()

    # Prepare data for Chart.js
    dates = [r.created_at.strftime("%b %d") for r in recent]
    stress_data = [r.stress for r in recent]
    workload_data = [r.workload for r in recent]
    satisfaction_data = [r.satisfaction for r in recent]

    return render_template(
        "dashboard.html",
        avg_stress=metrics["avg_stress"],
        avg_workload=metrics["avg_workload"],
        avg_satisfaction=metrics["avg_satisfaction"],
        wellbeing_score=metrics["wellbeing_score"],
        dates=dates,
        stress_data=stress_data,
        workload_data=workload_data,
        satisfaction_data=satisfaction_data,
        recent=[r.as_dict() for r in recent]
    )

@app.route("/api/metrics")
def api_metrics():
    return jsonify(compute_metrics())

@app.route("/api/responses")
def api_responses():
    rows = SurveyResponse.query.order_by(SurveyResponse.created_at.desc()).all()
    return jsonify([r.as_dict() for r in rows])

@app.cli.command("init-db")
def init_db_cmd():
    """flask init-db: initialize database tables."""
    db.create_all()
    print("Initialized the database.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
