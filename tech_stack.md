# Technology Stack - LifeLine SOS System

This document outlines the technologies used across the different layers of the Antigravity SOS (LifeLine) project.

## 🎨 Frontend (Dashboard & Monitoring)
- **Framework:** [React 19](https://react.dev/)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **State Management:** React Hooks (`useState`, `useEffect`)
- **Real-time Communication:** [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- **Maps:** 
  - [React-Leaflet](https://react-leaflet.js.org/) (OpenStreetMap)
  - [@vis.gl/react-google-maps](https://visgl.github.io/react-google-maps/) (Google Maps integration)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Styling:** Vanilla CSS (Modern CSS variables and animations)

## ⚙️ Backend (API & Processing)
- **Language:** Python 3.x
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High-performance ASGI framework)
- **Database:** [PostgreSQL](https://www.postgresql.org/) (Structured data storage)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Real-time Core:** [Redis](https://redis.io/) (Used for WebSocket message broadcasting and Pub/Sub)
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/)
- **Web Server:** [Uvicorn](https://www.uvicorn.org/)

## 🔌 Hardware (Nodes & Midway Gateway)
- **Microcontrollers:** ESP32 (WROOM/DevKit)
- **Programming Environment:** Arduino IDE / C++
- **Communication:**
  - **Off-Grid:** LoRa (Long Range 433MHz) using the `LoRa.h` library.
  - **Internet-Facing:** Wi-Fi (`WiFi.h`)
- **Sensors & Peripherals:**
  - **Displays:** OLED SSD1306 (128x64) via I2C (`Adafruit_SSD1306`).
  - **Scanning:** RFID MFRC522 (`MFRC522.h`).
  - **Vitals:** Digital Heart Rate Pulse Sensor.
- **Protocol:** HTTP POST (JSON payloads) for telemetry ingestion.

## 🔄 Integrations
- **Automation:** [n8n](https://n8n.io/) (External webhooks for emergency workflows)
