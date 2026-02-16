from flask import Flask, render_template, jsonify
import random
import datetime
import requests

app = Flask(__name__)

# 🔑 Put your Pushbullet API Key here
import os
PUSHBULLET_API_KEY = os.environ.get("PUSHBULLET_API_KEY","")

last_alert_time = None
ALERT_COOLDOWN_SECONDS = 60

history = []
incident_log = []


def send_push_notification(title, message):
    if PUSHBULLET_API_KEY == ("o.RGACT8xim6D1d0UnUDHI9xjr35iyQ7LB"):
        return

    url = "https://api.pushbullet.com/v2/pushes"
    headers = {
        "Access-Token": PUSHBULLET_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "type": "note",
        "title": title,
        "body": message
    }
    requests.post(url, json=data, headers=headers)


def calculate_risk(lpg, temp, humidity, alcohol):
    lpg_weight = 0.4 * lpg
    temp_weight = 0.2 * (temp * 2)
    humidity_weight = 0.2 * humidity
    alcohol_weight = 0.2 * alcohol

    risk = lpg_weight + temp_weight + humidity_weight + alcohol_weight

    if lpg > 70 and alcohol > 50:
        risk += 15

    return min(round(risk, 2), 100), {
        "lpg": round(lpg_weight, 2),
        "temp": round(temp_weight, 2),
        "humidity": round(humidity_weight, 2),
        "alcohol": round(alcohol_weight, 2)
    }


def classify_risk(risk):
    if risk < 30:
        return "Safe"
    elif risk < 60:
        return "Moderate"
    elif risk < 80:
        return "High"
    else:
        return "Critical"


def generate_explanation(lpg, humidity, alcohol, status):
    if status == "Safe":
        return "Air quality within safe limits."
    if lpg > 70 and alcohol > 50:
        return "Combined flammable gases detected. Explosion probability increased."
    if lpg > 70:
        return "Elevated LPG detected. Possible gas leakage."
    if humidity > 80:
        return "Excess humidity detected. Risk of mold and respiratory issues."
    if alcohol > 60:
        return "High alcohol vapors detected. Ensure ventilation."
    return "Air quality deviation detected. Monitor closely."


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data")
def data():
    global last_alert_time

    lpg = random.randint(10, 100)
    temp = random.randint(20, 45)
    humidity = random.randint(30, 90)
    alcohol = random.randint(5, 100)

    risk, breakdown = calculate_risk(lpg, temp, humidity, alcohol)
    status = classify_risk(risk)
    explanation = generate_explanation(lpg, humidity, alcohol, status)

    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")

    if status in ["High", "Critical"]:
        if (last_alert_time is None or
           (now - last_alert_time).total_seconds() > ALERT_COOLDOWN_SECONDS):

            message = f"""
Status: {status}
Risk: {risk}%
{explanation}
LPG: {lpg} | Alcohol: {alcohol}
            """

            send_push_notification("Indoor Hazard Alert", message)
            last_alert_time = now

            incident_log.append({
                "time": time_str,
                "status": status,
                "reason": explanation
            })

            if len(incident_log) > 10:
                incident_log.pop(0)

    history.append({"time": time_str, "risk": risk})
    if len(history) > 20:
        history.pop(0)

    return jsonify({
        "current": {
            "lpg": lpg,
            "temp": temp,
            "humidity": humidity,
            "alcohol": alcohol,
            "risk": risk,
            "status": status,
            "explanation": explanation
        },
        "breakdown": breakdown,
        "history": history,
        "incident_log": incident_log
    })


if __name__ == "__main__":
    app.run()




