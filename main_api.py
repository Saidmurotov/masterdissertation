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


# --- Universal IDE Endpoints ---

from pio_manager import PlatformIOManager
from daq_config import BOARD_CATALOG, SENSOR_CATALOG

pio_manager = PlatformIOManager()

@app.get("/boards")
def list_boards():
    """Returns the universal board catalog."""
    return BOARD_CATALOG

@app.get("/ports")
def list_ports():
    """Lists available COM ports."""
    return pio_manager.list_ports()

@app.get("/drivers")
def list_drivers():
    """Returns list of supported drivers."""
    # This could be dynamic, but fixed list is fine for now
    return ["CH340", "CP210x", "Arduino"]

class DriverInstallRequest(BaseModel):
    driver: str

@app.post("/install-driver")
def install_driver(req: DriverInstallRequest):
    """Launches driver installer."""
    success, msg = pio_manager.install_driver(req.driver)
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"message": msg}

@app.websocket("/ws/flash")
async def websocket_flash(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_json()
        code = data.get("code")
        board_name = data.get("board")
        port = data.get("port")
        sensor_types = data.get("sensors", []) # List of strings e.g. ["DHT22"]

        if not code or not board_name or not port:
            await ws.send_json({"type": "error", "message": "Missing code, board, or port"})
            return

        board_config = BOARD_CATALOG.get(board_name)
        if not board_config:
            await ws.send_json({"type": "error", "message": f"Unknown board: {board_name}"})
            return

        # Resolve strict library dependencies from SENSOR_CATALOG
        # We need the folder names that PIO will look for in vendor/libraries.
        # daq_config.py's SENSOR_CATALOG['lib_deps'] has strings like "adafruit/DHT sensor library"
        # Since we installed them using those names, PIO usually stores them as "DHT sensor library" (basename)
        # or we can rely on how PIO resolves deps.
        # But for offline mode with `lib_extra_dirs`, we must specific the folder name if it differs,
        # OR just list the deps and let PIO find them in the extra dir.
        libs = []
        for s_type in sensor_types:
            s_meta = SENSOR_CATALOG.get(s_type)
            if s_meta and "lib_deps" in s_meta:
                 libs.extend(s_meta["lib_deps"])
        
        # Deduplicate
        libs = list(set(libs))

        async def send_log(msg):
            await ws.send_json(msg)

        await pio_manager.build_and_upload(code, board_config, port, libs, send_log)

    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
    finally:
        await ws.close()

