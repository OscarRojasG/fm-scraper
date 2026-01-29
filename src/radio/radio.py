import os
import random
import json
import subprocess
from pathlib import Path
from ..settings import (
    RADIO_PATH,
    RADIO_SONGS_PATH,
    RADIO_PLAYLIST_FILE,
    RADIO_STATE_FILE,
    RADIO_METADATA_FILE
)
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
import uvicorn

# ================= CONFIG =================

load_dotenv()
os.makedirs(RADIO_PATH, exist_ok=True)

FFMPEG_PATH = os.getenv("FFMPEG_PATH")
ICECAST_URL = os.getenv("ICECAST_URL")

SONGS_PATH = Path(RADIO_SONGS_PATH)
STATE_FILE = Path(os.path.join(RADIO_PATH, RADIO_STATE_FILE))
PLAYLIST_FILE = Path(os.path.join(RADIO_PATH, RADIO_PLAYLIST_FILE))
METADATA_FILE = Path(os.path.join(RADIO_PATH, RADIO_METADATA_FILE))

HISTORY_SIZE = 500

# =========================================


def start_ffmpeg():
    cmd = [
        FFMPEG_PATH,
        "-re",
        "-f", "wav",
        "-i", "pipe:0",
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-f", "mp3",
        ICECAST_URL,
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def play_track(track_path, ffmpeg_process, stop_event):
    cmd = [
        FFMPEG_PATH,
        "-i", track_path,
        "-f", "wav",
        "-ac", "2",
        "-ar", "44100",
        "pipe:1",
    ]

    decoder = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    finished = False

    try:
        while not stop_event.is_set():
            data = decoder.stdout.read(4096)
            if not data:
                finished = True
                break
            ffmpeg_process.stdin.write(data)
    finally:
        decoder.stdout.close()
        decoder.wait()

    return finished

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "current": None,
        "history": []
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def pick_next_track(all_tracks, history):
    available = [t for t in all_tracks if t not in history]

    if not available:
        history.clear()
        available = all_tracks.copy()

    return random.choice(available)


def get_all_tracks():
    return [str(p.resolve()) for p in SONGS_PATH.glob("*.mp3")]


def update_metadata(track):
    artist = "Unknown"
    title = ""

    try:
        audio = MP3(track)
        artist = audio.get("TPE1").text[0]
        title = audio.get("TIT2").text[0]
    except ID3NoHeaderError:
        pass
    except Exception as e:
        print(f"Error metadata: {e}")

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"title": title, "artist": artist},
            f,
            indent=2,
            ensure_ascii=False
        )

def radio_loop(stop_event):
    all_tracks = get_all_tracks()
    if not all_tracks:
        print("No hay canciones")
        return

    ffmpeg_process = start_ffmpeg()
    state = load_state()

    try:
        while not stop_event.is_set():
            track = pick_next_track(all_tracks, state["history"])

            state["current"] = track
            save_state(state)

            print(f"Reproduciendo: {Path(track).name}")
            update_metadata(track)

            finished = play_track(track, ffmpeg_process, stop_event)

            if finished:
                state["history"].append(track)
                state["history"] = state["history"][-HISTORY_SIZE:]

            state["current"] = None
            save_state(state)


    finally:
        print("Apagando radio")
        try:
            ffmpeg_process.stdin.close()
            ffmpeg_process.terminate()
        except Exception:
            pass


def start_api():
    from .api import app
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")