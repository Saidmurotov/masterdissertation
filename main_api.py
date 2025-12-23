"""Lightweight FastAPI wrapper around esp_mqtt_generator."""

import asyncio
import json
import random
from typing import List, Optional

from fastapi import HTTPException, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import esp_mqtt_generator as gen
from semantic_analyzer import analyze


class SensorSelection(BaseModel):
    type: str = Field(..., description="Sensor type, e.g., DHT22")
    pin: Optional[int] = Field(None, description="Optional pin number")


class GenerateRequest(BaseModel):
    mcu: str = Field("ESP32", description="Target MCU")
    board: str = Field("ESP32", description="Target board")
    sensors: List[SensorSelection]
    mqtt_enabled: bool = True
    wifi_ssid: str | None = None
    wifi_password: str | None = None
    mqtt_broker: str | None = None


class GenerateResponse(BaseModel):
    code: str


app = FastAPI(title="ESP MQTT Generator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/sensors")
def list_sensors():
    return gen.available_sensors()


@app.post("/generate-code", response_model=GenerateResponse)
def generate_code(req: GenerateRequest):
    if not req.sensors:
        raise HTTPException(status_code=400, detail="At least one sensor is required.")

    semantic_errors = analyze(req.model_dump())
    if semantic_errors:
        raise HTTPException(status_code=400, detail={"semantic_errors": semantic_errors})

    try:
        payload = {
            "mcu": req.mcu,
            "board": req.board,
            "sensors": [s.model_dump() for s in req.sensors],
            "mqtt_enabled": req.mqtt_enabled,
            "wifi_ssid": req.wifi_ssid,
            "wifi_password": req.wifi_password,
            "mqtt_broker": req.mqtt_broker,
        }
        code = gen.generate_code(payload)
        return GenerateResponse(code=code)
    except gen.UnsupportedSensorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except gen.IncompatibleMCUError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.websocket("/ws/data")
async def websocket_data(ws: WebSocket):
    await ws.accept()
    counter = 0
    while True:
        counter += 1
        # Simulate realistic sensor readings
        payload = {
            "temperature": round(random.uniform(20.0, 30.0), 2),
            "humidity": round(random.uniform(40.0, 70.0), 2),
            "pressure": round(random.uniform(990.0, 1020.0), 2),
            "gas": round(random.uniform(200.0, 450.0), 2),
            "light": random.randint(100, 900),
            "ts": counter,
        }
        await ws.send_text(json.dumps(payload))
        await asyncio.sleep(2)

