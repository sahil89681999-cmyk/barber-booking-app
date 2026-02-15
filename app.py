from flask import Flask, render_template, request, redirect, session
import pandas as pd
import os
from datetime import datetime
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= TWILIO CONFIG =================
ACCOUNT_SID = "AC4bc26a9092d39133343b87141f33495a"
AUTH_TOKEN = "d30ff50c3e070d39d061d803fed8a5f5"
TWILIO_PHONE = "+918968199945"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ================= FILE PATHS =================
APPOINTMENT_FILE = "appointments.xlsx"
TOKEN_FILE = "current_token.xlsx"

# ================= INIT DATABASE =================
def init_files():
    if not os.path.exists(APPOINTMENT_FILE):
        df = pd.DataFrame(columns=["name","mobile","barber","service","date","token"])
        df.to_excel(APPOINTMENT_FILE, index=False)

    if not os.path.exists(TOKEN_FILE):
        df = pd.DataFrame(columns=["date","current_token"])
        df.to_excel(TOKEN_FILE, index=False)

init_files()

# ================= HOME =================
@app.route("/")
def index():
    today = str(datetime.today().date())
    df = pd.read_excel(TOKEN_FILE)

    current_token = 0
    if today in df["date"].astype(str).values:
        current_token = df[df["date"].astype(str)==today]["current_token"].values[0]

    return render_template("index.html", current_token=current_token)

# ================= BOOK =================
@app.route("/book", methods=["POST"])
def book():
    name = request.form["name"]
    mobile = request.form["mobile"]
    barber = request.form["barber"]
    service = request.form["service"]
    today = str(datetime.today().date())

    df = pd.read_excel(APPOINTMENT_FILE)

    # Prevent duplicate mobile booking
    if mobile in df[df["date"].astype(str)==today]["mobile"].astype(str).values:
        return "You already have a booking today."

    todays = df[df["date"].astype(str)==today]
    token = 1 if todays.empty else todays["token"].max() + 1

    new_row = {
        "name": name,
        "mobile": mobile,
        "barber": barber,
        "service": service,
        "date": today,
        "token": token
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_excel(APPOINTMENT_FILE, index=False)

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
    df = pd.read_excel(TOKEN_FILE)

    current_token = 0
    if today in df["date"].astype(str).values:
        current_token = df[df["date"].astype(str)==today]["current_token"].values[0]

    return render_template("admin.html", current_token=current_token)

# ================= NEXT TOKEN =================
@app.route("/next")
def next_token():
    if not session.get("admin"):
        return redirect("/login")

    today = str(datetime.today().date())
    df = pd.read_excel(TOKEN_FILE)

    if today in df["date"].astype(str).values:
        df.loc[df["date"].astype(str)==today,"current_token"] += 1
    else:
        new_row = {"date":today,"current_token":1}
        df = pd.concat([df,pd.DataFrame([new_row])])

    df.to_excel(TOKEN_FILE,index=False)
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
