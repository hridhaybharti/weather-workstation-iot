# 🌤️ Weather Workstation (IoT)

> A full-stack IoT-based real-time environmental monitoring system using Python, MQTT, and a live web dashboard.

---

## 🔍 Overview

**Weather Workstation** is a real-time IoT monitoring system designed to collect, process, and visualize environmental and air-quality data.  
It integrates sensor hardware, a Python backend, MQTT messaging, and a responsive web dashboard to deliver low-latency and reliable monitoring.

---

## ✨ Key Features

- 🌡️ Real-time monitoring of environmental parameters  
- 🔄 Multithreaded Python backend  
- 📡 MQTT publish/subscribe communication  
- 📊 Live dashboard with charts & alerts  
- 🧾 CSV-based data logging  
- ⚠️ Threshold-based alert detection  
- 🔁 Auto-reconnect & fault tolerance  

---

## 🌡️ Sensors Monitored

- Temperature (°C)
- Humidity (%)
- CO₂ (ppm)
- Oxygen (%)
- UV Index
- Solar Radiation (W/m²)
- Air Quality Index (AQI)
- Atmospheric Pressure (hPa)

---

## 🧠 System Architecture

Sensors → Arduino → Raspberry Pi (Backend)
→ MQTT Broker
→ Web Dashboard


---

## 🛠️ Tech Stack

**Backend**
- Python 3
- Multithreading
- Paho MQTT
- CSV & JSON

**Frontend**
- HTML, CSS, JavaScript
- Chart.js
- MQTT.js (WebSockets)

**Hardware (Optional)**
- Scientech 6205
- Arduino Mega
- Raspberry Pi 4

---

Use Cases

Smart cities

Environmental research

Smart agriculture

Disaster monitoring

Academic IoT labs

🔮 Future Scope

Cloud integration (AWS / Firebase)

Mobile app

Database storage

AI-based forecasting

Multi-node sensor network

👨‍🎓 Author

Hridhay Bharti
B.Tech CSE (Cyber Security)
Rashtriya Raksha University
