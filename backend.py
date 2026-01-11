#!/usr/bin/env python3
import os
import time
import json
import csv
import serial
import queue
import signal
import socket
import logging
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# =========================
# CONFIGURATION
# =========================
BASE_DIR = os.path.expanduser("~")
CSV_FILE = os.path.join(BASE_DIR, "sensor_data.csv")
LOG_FILE = os.path.join(BASE_DIR, "sensor_errors.log")

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC = "weather/workstation"
STATUS_TOPIC = f"weather/status/{socket.gethostname()}"

READ_INTERVAL = 2            # Arduino sends every 2s
PROCESS_INTERVAL = 2
MAX_RETRIES = 3

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# =========================
# SENSOR CALIBRATION
# =========================

def calibrate(raw):
    """Convert raw ADC readings using stable linear approximations."""
    try:
        r = int(raw)
    except:
        return None
    if r < 0: r = 0
    if r > 1023: r = 1023
    return r

def convert_values(data):
    """Convert raw ADC values to engineering units."""
    oxy   = calibrate(data["oxygen"])
    uv    = calibrate(data["uv"])
    pres  = calibrate(data["pressure"])
    solar = calibrate(data["solar"])
    th    = calibrate(data["temp_humidity"])
    co2   = calibrate(data["co2"])
    aq    = calibrate(data["air_quality"])

    return {
        "Temperature": round((th / 1023) * 50, 2),            # 0–50 °C approx
        "Humidity": round((th / 1023) * 100, 2),              # 0–100%
        "CO2": round((co2 / 1023) * 2000, 2),                 # ppm (approx)
        "Oxygen": round((oxy / 1023) * 21, 2),                # 0–21%
        "UV Index": round((uv / 1023) * 11, 2),               # 0–11
        "Solar Radiation": round((solar / 1023) * 1200, 2),   # W/m²
        "Air Quality": round((aq / 1023) * 500, 2),           # AQI
        "GSR": round((solar / 1023) * 100, 2),                # same solar sensor
        "Atmospheric Pressure": round((pres / 1023) * 1100, 2) # hPa
    }

# =========================
# MQTT CLIENT
# =========================

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.connected = False
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        logging.info("MQTT connected" if self.connected else f"MQTT failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logging.warning("MQTT disconnected")

    def start(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 30)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"MQTT connection error: {e}")

    def publish(self, topic, payload):
        if self.connected:
            self.client.publish(topic, payload)
        else:
            logging.warning("MQTT not connected, skipping publish")


mqtt_client = MQTTClient()
data_queue = queue.Queue()


# =========================
# SERIAL READER
# =========================
def serial_reader():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        logging.info(f"Connected to Arduino on {SERIAL_PORT}")
    except Exception as e:
        logging.error(f"Serial error: {e}")
        return

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue

            if not line.startswith("{") or not line.endswith("}"):
                logging.warning(f"Bad JSON: {line}")
                continue

            data = json.loads(line)
            data_queue.put(data)

        except Exception as e:
            logging.error(f"Serial read error: {e}")

        time.sleep(0.1)


# =========================
# DATA PROCESSOR
# =========================
def data_processor():
    ensure_csv()

    while True:
        if data_queue.empty():
            time.sleep(0.05)
            continue

        raw = data_queue.get()
        calibrated = convert_values(raw)

        logging.info("CALIBRATED → " + str(calibrated))

        # Write to CSV
        write_csv(calibrated)

        # Publish to MQTT
        mqtt_client.publish(TOPIC, json.dumps(calibrated))

        # Heartbeat
        hb = json.dumps({"ts": time.time(), "status": "ok"})
        mqtt_client.publish(STATUS_TOPIC + "/hb", hb)

        time.sleep(PROCESS_INTERVAL)


# =========================
# CSV HANDLING
# =========================

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "Temperature", "Humidity", "CO2", "Oxygen",
                "UV Index", "Solar Radiation", "Air Quality", "GSR",
                "Atmospheric Pressure"
            ])

def write_csv(data):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            data["Temperature"],
            data["Humidity"],
            data["CO2"],
            data["Oxygen"],
            data["UV Index"],
            data["Solar Radiation"],
            data["Air Quality"],
            data["GSR"],
            data["Atmospheric Pressure"]
        ])


# =========================
# SHUTDOWN HANDLER
# =========================
def shutdown(sig, frame):
    logging.info("Shutting down backend…")
    mqtt_client.client.loop_stop()
    os._exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    logging.info("Weather backend starting…")

    mqtt_client.start()

    threading.Thread(target=serial_reader, daemon=True).start()
    threading.Thread(target=data_processor, daemon=True).start()

    while True:
        time.sleep(1)
