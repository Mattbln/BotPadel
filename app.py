from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
from datetime import datetime, timedelta
import time
import threading
import schedule
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

TIMEZONE = pytz.timezone('Europe/Paris')
SERVER_TIMEZONE = pytz.FixedOffset(120)  # GMT+2

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
        # Pré-chargement de la page
        driver.get('https://ballejaune.com/club/bandol')
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, 'username')))
        
        # Connexion rapide
        driver.execute_script(
            "document.getElementsByName('username')[0].value='Belin Dominique';"
            "document.getElementsByName('password')[0].value='gb74mB';"
            "document.getElementsByName('password')[0].form.submit();"
        )
        
        # Attendre jusqu'à 14:35:00 exactement (GMT+2)
        now = datetime.now(SERVER_TIMEZONE)
        target_time = now.replace(hour=14, minute=35, second=0, microsecond=0)
        time_to_wait = (target_time - now).total_seconds()
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        
        
        # Navigation rapide vers la page de réservation
        formatted_date = status.date.strftime("%d/%m/%Y")
        driver.get(f'https://ballejaune.com/reservation/#date="{formatted_date}&group=0&page=0')
        
        # Attente et clic rapides
        slot = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'a.slot-free[data-schedule="{status.court}"][data-timestart="{status.time}"]'))
        )
        driver.execute_script("arguments[0].click();", slot)
        
        # Finalisation rapide
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#with-none"]'))
        ).click()
        
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="action_type"][value="create"]'))
        ).click()
        
        print("Réservation effectuée avec succès!")
        
        status.last_run = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"Erreur lors de la réservation: {str(e)}")
    finally:
        driver.quit()

def run_scheduler():
    while True:
        now = datetime.now(SERVER_TIMEZONE)
        if now.hour == 14 and now.minute == 34:  # Démarrer le processus à 14:34 GMT+2
            reservation_padel()
            time.sleep(120)  # Attendre 2 minutes avant de vérifier à nouveau
        time.sleep(30)  # Vérifier toutes les 30 secondes



scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

@app.route('/server-time')
def server_time():
    server_now = datetime.now(SERVER_TIMEZONE)
    paris_now = datetime.now(TIMEZONE)
    return jsonify({
        "server_time": server_now.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        "paris_time": paris_now.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        "is_dst": paris_now.dst() != timedelta(0)
    })


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