from flask import Flask, render_template, jsonify
import random
import time
import requests

app = Flask(__name__)

# ---------------- Global Variables ----------------
PUSHBULLET_TOKEN = "o.RGACT8xim6D1d0UnUDHI9xjr35iyQ7LB"
history = []
incident_log = []
last_status = "Safe"

# ---------------- PushBullet Notification ----------------
def send_pushbullet(title, message):
    try:
        requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": PUSHBULLET_TOKEN},
            json={"type": "note", "title": title, "body": message}
        )
    except:
        pass

# ---------------- Risk Calculation ----------------
def calculate_risk(lpg, temp, humidity, alcohol):
    score = 0
    if lpg > 300:
        score += 40
    if temp > 40:
        score += 20
    if humidity > 80:
        score += 15
    if alcohol > 250:
        score += 25
    return min(score, 100)

def get_status(score):
    if score < 25:
        return "Safe"
    elif score < 50:
        return "Moderate"
    elif score < 75:
        return "High"
    else:
        return "Critical"

# ---------------- Home Route ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- Data Route ----------------
@app.route("/data")
def data():
    global last_status

    # Simulate sensor readings
    lpg = random.randint(100, 600)
    temp = random.randint(20, 50)
    humidity = random.randint(40, 90)
    alcohol = random.randint(100, 500)

    risk = calculate_risk(lpg, temp, humidity, alcohol)
    status = get_status(risk)
    explanation = f"LPG:{lpg}, Temp:{temp}, Humidity:{humidity}, Alcohol:{alcohol}"

    # Update history
    history.append({"time": time.strftime("%H:%M:%S"), "risk": risk})
    if len(history) > 10:
        history.pop(0)

    alert_message = ""

    # PushBullet & incident log
    if status != last_status and status in ["High", "Critical"]:
        send_pushbullet("⚠ Indoor Hazard Alert", f"{status} risk detected!")
        incident_log.append({"time": time.strftime("%H:%M:%S"), "status": status, "reason": explanation})
        if len(incident_log) > 10:
            incident_log.pop(0)

    # Browser alert
    if status in ["High", "Critical"]:
        alert_message = "⚠ Hazard Detected! Emergency Protocol Activated."

    last_status = status

    return jsonify({
        "current": {
            "lpg": lpg,
            "temp": temp,
            "humidity": humidity,
            "alcohol": alcohol,
            "risk": risk,
            "status": status,
            "explanation": explanation,
            "alert": alert_message
        },
        "history": history,
        "incident_log": incident_log
    })

# ---------------- Run ----------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
