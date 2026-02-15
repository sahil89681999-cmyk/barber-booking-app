from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from twilio.rest import Client
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= DATABASE CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://barber_db_ovdg_user:e5uXnjpkpuDvQOdBBN94CFK08cSbcJES@dpg-d68ogrrh46gs73fi2iug-a/barber_db_ovdg"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= TWILIO CONFIG =================
ACCOUNT_SID = "AC4bc26a9092d39133343b87141f33495a"
AUTH_TOKEN = "d30ff50c3e070d39d061d803fed8a5f5"
TWILIO_PHONE = "+918968199945"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ================= MODELS =================

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    barber = db.Column(db.String(50))
    service = db.Column(db.String(50))
    date = db.Column(db.String(20))
    token = db.Column(db.Integer)

class CurrentToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), unique=True)
    current_token = db.Column(db.Integer)

# ================= CREATE TABLES =================
with app.app_context():
    db.create_all()

# ================= HOME =================
@app.route("/")
def index():
    today = str(datetime.today().date())
    token_entry = CurrentToken.query.filter_by(date=today).first()
    current_token = token_entry.current_token if token_entry else 0
    return render_template("index.html", current_token=current_token)

# ================= BOOK =================
@app.route("/book", methods=["POST"])
def book():
    name = request.form["name"]
    mobile = request.form["mobile"]
    barber = request.form["barber"]
    service = request.form["service"]
    today = str(datetime.today().date())

    # Prevent duplicate booking
    existing = Appointment.query.filter_by(mobile=mobile, date=today).first()
    if existing:
        return "You already have a booking today."

    todays = Appointment.query.filter_by(date=today).all()
    token = 1 if not todays else max(a.token for a in todays) + 1

    new_appointment = Appointment(
        name=name,
        mobile=mobile,
        barber=barber,
        service=service,
        date=today,
        token=token
    )

    db.session.add(new_appointment)
    db.session.commit()

    # Send SMS
    try:
        client.messages.create(
            body=f"Hi {name}, Your token is {token} for {service}.",
            from_=TWILIO_PHONE,
            to=f"+91{mobile}"
        )
    except:
        print("SMS failed")

    return f"Booking Confirmed! Your token number is {token}"

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    today = str(datetime.today().date())
    token_entry = CurrentToken.query.filter_by(date=today).first()
    current_token = token_entry.current_token if token_entry else 0

    return render_template("admin.html", current_token=current_token)

# ================= NEXT TOKEN =================
@app.route("/next")
def next_token():
    if not session.get("admin"):
        return redirect("/login")

    today = str(datetime.today().date())
    token_entry = CurrentToken.query.filter_by(date=today).first()

    if token_entry:
        token_entry.current_token += 1
    else:
        token_entry = CurrentToken(date=today, current_token=1)
        db.session.add(token_entry)

    db.session.commit()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
