from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import json

from .radio import METADATA_FILE, radio_loop
from .control import radio_thread, radio_stop_event, radio_lock

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/radio/on")
def radio_on():
    global radio_thread, radio_stop_event

    with radio_lock:
        if radio_thread and radio_thread.is_alive():
            return {"status": "already_on"}

        radio_stop_event = threading.Event()
        radio_thread = threading.Thread(
            target=radio_loop,
            args=(radio_stop_event,),
            daemon=True
        )
        radio_thread.start()

    return {"status": "on"}


@app.post("/radio/off")
def radio_off():
    global radio_thread, radio_stop_event

    with radio_lock:
        if not radio_thread:
            return {"status": "already_off"}

        radio_stop_event.set()
        radio_thread = None
        radio_stop_event = None

    return {"status": "off"}


@app.get("/radio/status")
def radio_status():
    return {
        "running": bool(radio_thread and radio_thread.is_alive())
    }


@app.get("/metadata")
def get_metadata():
    if not METADATA_FILE.exists():
        return {"title": "", "artist": ""}

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
