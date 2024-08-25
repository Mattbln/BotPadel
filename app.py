from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ReservationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    last_run = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, nullable=True)
    court = db.Column(db.String(10), nullable=True)
    time = db.Column(db.String(10), nullable=True)

@app.before_first_request
def create_tables():
    db.create_all()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=chrome_options)

def reservation_padel():
    status = ReservationStatus.query.first()
    if not status or not status.is_active:
        return

    driver = setup_driver()
    try:
        driver.get('https://ballejaune.com/club/bandol')
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'password')))
        
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        
        username_field.send_keys('Belin Dominique')
        password_field.send_keys('gb74mB')
        
        password_field.submit()
        
        formatted_date = status.date.strftime("%d/%m/%Y")
        driver.get(f'https://ballejaune.com/reservation/#date="{formatted_date}&group=0&page=0')
        
        slot = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'a.slot-free[data-schedule="{status.court}"][data-timestart="{status.time}"]'))
        )
        slot.click()
        
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#with-none"]'))
        )
        button.click()
        
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="action_type"][value="create"]'))
        )
        button.click()
        
        print("Réservation effectuée avec succès!")
        
        status.last_run = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"Erreur lors de la réservation: {str(e)}")
    finally:
        driver.quit()

def run_scheduler():
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:
            reservation_padel()
        time.sleep(60)  # Check every minute

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_reservation():
    try:
        data = request.json
        status = ReservationStatus.query.first()
        if not status:
            status = ReservationStatus()
        
        status.is_active = True
        status.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        status.court = data['court']
        status.time = data['time']
        
        db.session.add(status)
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
                "lastRun": status.last_run.isoformat() if status.last_run else None,
                "date": status.date.isoformat() if status.date else None,
                "court": status.court,
                "time": status.time
            }), 200
        else:
            return jsonify({"status": "Aucune réservation configurée", "isRunning": False, "lastRun": None}), 200
    except Exception as e:
        return jsonify({"status": f"Erreur: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)