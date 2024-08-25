from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ReservationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    last_run = db.Column(db.DateTime, nullable=True)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_reservation():
    try:
        status = ReservationStatus.query.first()
        if not status:
            status = ReservationStatus(is_active=True)
            db.session.add(status)
        else:
            status.is_active = True
        db.session.commit()
        return jsonify({"status": "Réservation activée"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": f"Erreur: {str(e)}"}), 500

@app.route('/stop', methods=['POST'])
def stop_reservation():
    try:
        status = ReservationStatus.query.first()
        if status:
            status.is_active = False
            db.session.commit()
        return jsonify({"status": "Réservation désactivée"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": f"Erreur: {str(e)}"}), 500

@app.route('/status', methods=['GET'])
def get_status():
    try:
        status = ReservationStatus.query.first()
        if status:
            return jsonify({
                "status": "Réservation active" if status.is_active else "Réservation inactive",
                "isRunning": status.is_active,
                "lastRun": status.last_run.isoformat() if status.last_run else None
            }), 200
        else:
            return jsonify({"status": "Aucune réservation configurée", "isRunning": False, "lastRun": None}), 200
    except Exception as e:
        return jsonify({"status": f"Erreur: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)