import time
import random
import logging
import csv
from datetime import datetime
import json
import threading
import queue
import paho.mqtt.client as mqtt

# ---------------- Configuration ----------------
SIMULATION = True
READ_INTERVAL = 1        # seconds
PROCESS_INTERVAL = 5     # seconds (more responsive)
MAX_RETRIES = 3

THRESHOLDS = {
    "Temperature (°C": 30,
    "CO2 (ppm)": 1000,
    "Air Quality (AQI)": 200
}

UNITS = {
    "Temperature (°C)": "°C",
    "Humidity (%)": "%",
    "CO2 (ppm)": "ppm",
    "Oxygen (O2 %)": "%",
    "UV Index": "index",
    "Solar Radiation (W/m²)": "W/m²",
    "Air Quality (AQI)": "AQI",
    "GSR": "",
    "Atmospheric Pressure (hPa)": "hPa"
}

CSV_FILE = "sensor_data.csv"
BROKER = "127.0.0.1"
TOPIC = "weather/workstation"

logging.basicConfig(filename='sensor_errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------- Sensors ----------------
def read_temperature(): return round(random.uniform(15.0, 35.0),2)
def read_humidity(): return round(random.uniform(30.0,90.0),2)
def read_co2(): return round(random.uniform(350,2000),2)
def read_oxygen(): return round(random.uniform(19.0,21.0),2)
def read_uv_index(): return round(random.uniform(0,11),2)
def read_solar_radiation(): return round(random.uniform(0,1000),2)
def read_air_quality(): return round(random.uniform(0,500),2)
def read_gsr(): return round(random.uniform(0,100),2)
def read_atmospheric_pressure(): return round(random.uniform(950,1050),2)

class Sensor:
    def __init__(self,name,read_func):
        self.name = name
        self.read_func = read_func
    def read(self):
        for _ in range(MAX_RETRIES):
            try:
                value = self.read_func()
                if value is not None: return value
            except Exception as e:
                logging.error(f"{self.name} Sensor Error: {e}")
                time.sleep(0.1)
        logging.error(f"{self.name} failed after {MAX_RETRIES} retries")
        return None

sensors = [
    Sensor("Temperature (°C)", read_temperature),
    Sensor("Humidity (%)", read_humidity),
    Sensor("CO2 (ppm)", read_co2),
    Sensor("Oxygen (O2 %)", read_oxygen),
    Sensor("UV Index", read_uv_index),
    Sensor("Solar Radiation (W/m²)", read_solar_radiation),
    Sensor("Air Quality (AQI)", read_air_quality),
    Sensor("GSR", read_gsr),
    Sensor("Atmospheric Pressure (hPa)", read_atmospheric_pressure)
]

# ---------------- MQTT ----------------
client = mqtt.Client()
client.connect(BROKER, 1883, 60)

# ---------------- Thread-safe queue ----------------
data_queue = queue.Queue()

# ---------------- Helpers ----------------
def check_threshold(sensor_name,value):
    if value is None: return "ERROR"
    if sensor_name in THRESHOLDS and value > THRESHOLDS[sensor_name]:
        return "ALERT"
    return "Normal"

# ---------------- Sensor Reader ----------------
def sensor_reader():
    while True:
        snapshot = {s.name: s.read() for s in sensors}
        data_queue.put((datetime.now(),snapshot))
        time.sleep(READ_INTERVAL)

# ---------------- Data Processor ----------------
def data_processor():
    while True:
        batch = []
        while not data_queue.empty(): batch.append(data_queue.get())
        if not batch:
            time.sleep(1)
            continue
        timestamp, latest_data = batch[-1]

        # Console
        print(f"\n=== Weather Workstation ({timestamp}) ===")
        for n,v in latest_data.items():
            status = check_threshold(n,v)
            unit = UNITS.get(n,"")
            print(f"{n:<28} {v} {unit:<6} {status}")

        # CSV log
        with open(CSV_FILE,"a",newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp]+[latest_data[s.name] for s in sensors])

        # MQTT publish
        client.publish(TOPIC,json.dumps(latest_data))
        time.sleep(PROCESS_INTERVAL)

# ---------------- Main ----------------
if __name__=="__main__":
    try:
        with open(CSV_FILE,"x",newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp"]+[s.name for s in sensors])
    except FileExistsError: pass

    threading.Thread(target=sensor_reader,daemon=True).start()
    threading.Thread(target=data_processor,daemon=True).start()
    print("Weather backend running. Ctrl+C to stop.")
    while True: time.sleep(1)
