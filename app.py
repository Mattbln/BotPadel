from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///reservations.db'
db = SQLAlchemy(app)

class ReservationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    last_run = db.Column(db.DateTime, nullable=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_reservation():
    status = ReservationStatus.query.first()
    if not status:
        status = ReservationStatus(is_active=True)
        db.session.add(status)
    else:
        status.is_active = True
    db.session.commit()
    return jsonify({"status": "Réservation activée"})

@app.route('/stop', methods=['POST'])
def stop_reservation():
    status = ReservationStatus.query.first()
    if status:
        status.is_active = False
        db.session.commit()
    return jsonify({"status": "Réservation désactivée"})

@app.route('/status', methods=['GET'])
def get_status():
    status = ReservationStatus.query.first()
    if status:
        return jsonify({
            "status": "Réservation active" if status.is_active else "Réservation inactive",
            "isRunning": status.is_active,
            "lastRun": status.last_run.isoformat() if status.last_run else None
        })
    else:
        return jsonify({"status": "Aucune réservation configurée", "isRunning": False, "lastRun": None})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)