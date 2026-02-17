from flask import Flask, render_template, jsonify
import random
import datetime
import requests

app = Flask(__name__)

# Pushbullet API Key
import os
PUSHBULLET_API_KEY = os.environ.get("PUSHBULLET_API_KEY")

last_alert_time = None
ALERT_COOLDOWN_SECONDS = 60

history = []
incident_log = []

def send_push_notification(title, message):
    if not PUSHBULLET_API_KEY:
        return
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
    data = {"type":"note","title":title,"body":message}
    requests.post(url, json=data, headers=headers)

def calculate_risk(lpg,temp,humidity,alcohol):
    lpg_w = 0.4*lpg
    temp_w = 0.2*(temp*2)
    hum_w = 0.2*humidity
    alc_w = 0.2*alcohol
    risk = lpg_w + temp_w + hum_w + alc_w
    if lpg>70 and alcohol>50: risk+=15
    return min(round(risk,2),100), {"lpg":round(lpg_w,2),"temp":round(temp_w,2),"humidity":round(hum_w,2),"alcohol":round(alc_w,2)}

def classify_risk(risk):
    if risk<30: return "Safe"
    elif risk<60: return "Moderate"
    elif risk<80: return "High"
    else: return "Critical"

def generate_explanation(lpg,humidity,alcohol,status):
    if status=="Safe": return "Air quality within safe limits."
    if lpg>70 and alcohol>50: return "Combined flammable gases detected. Explosion probability increased."
    if lpg>70: return "Elevated LPG detected. Possible gas leakage."
    if humidity>80: return "Excess humidity detected. Risk of mold and respiratory issues."
    if alcohol>60: return "High alcohol vapors detected. Ensure ventilation."
    return "Air quality deviation detected. Monitor closely."

def predict_risk(history_list):
    if len(history_list)<5: return history_list[-1] if history_list else 0
    return round(sum(history_list[-5:])/5,2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/data")
def data():
    global last_alert_time
    lpg = random.randint(10,100)
    temp = random.randint(20,45)
    humidity = random.randint(30,90)
    alcohol = random.randint(5,100)

    risk, breakdown = calculate_risk(lpg,temp,humidity,alcohol)
    status = classify_risk(risk)
    explanation = generate_explanation(lpg,humidity,alcohol,status)

    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")

    if status in ["High","Critical"]:
        if last_alert_time is None or (now-last_alert_time).total_seconds()>ALERT_COOLDOWN_SECONDS:
            message = f"Status: {status}\nRisk: {risk}%\n{explanation}\nLPG: {lpg} | Alcohol: {alcohol}"
            send_push_notification("Indoor Hazard Alert", message)
            last_alert_time = now
            incident_log.append({"time":time_str,"status":status,"reason":explanation})
            if len(incident_log)>10: incident_log.pop(0)

    history.append(risk)
    if len(history)>20: history.pop(0)
    predicted_risk = predict_risk(history)

    return jsonify({
        "current": {"lpg":lpg,"temp":temp,"humidity":humidity,"alcohol":alcohol,"risk":risk,"status":status,"explanation":explanation,"predicted_risk":predicted_risk},
        "breakdown": breakdown,
        "history": history,
        "incident_log": incident_log
    })
import os
if __name__=="__main__":
    port= int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)


    



    

   

