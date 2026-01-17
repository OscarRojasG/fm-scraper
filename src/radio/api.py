from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from .radio import METADATA_FILE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/metadata")
def get_metadata():
    if not METADATA_FILE.exists():
        return {
            "title": "",
            "artist": ""
        }

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)