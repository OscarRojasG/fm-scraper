import os
import random
import json
import subprocess
from pathlib import Path
from ..settings import RADIO_PATH, RADIO_SONGS_PATH, RADIO_PLAYLIST_FILE, RADIO_STATE_FILE, RADIO_METADATA_FILE
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
import threading
import uvicorn


# ================= CONFIG =================

load_dotenv()
os.makedirs(RADIO_PATH, exist_ok=True)

FFMPEG_PATH  = os.getenv('FFMPEG_PATH')
ICECAST_URL  = os.getenv('ICECAST_URL')
SONGS_PATH = Path(RADIO_SONGS_PATH)
STATE_FILE = Path(os.path.join(RADIO_PATH, RADIO_STATE_FILE))
PLAYLIST_FILE = Path(os.path.join(RADIO_PATH, RADIO_PLAYLIST_FILE))
METADATA_FILE = Path(os.path.join(RADIO_PATH, RADIO_METADATA_FILE))
FIFO_PATH = Path(os.path.join(RADIO_PATH, r"\\.\pipe\radio_fifo"))

HISTORY_SIZE = 300

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
        ICECAST_URL
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )


import time

def wait_for_pipe(timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with open(FIFO_PATH, "rb"):
                return
        except FileNotFoundError:
            time.sleep(0.1)

    raise RuntimeError("El pipe no fue creado por FFmpeg")


def play_track(track_path, ffmpeg_process):
    cmd = [
        FFMPEG_PATH,
        "-i", track_path,
        "-f", "wav",
        "-ac", "2",
        "-ar", "44100",
        "pipe:1"
    ]

    decoder = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    while True:
        data = decoder.stdout.read(4096)
        if not data:
            break
        ffmpeg_process.stdin.write(data)

    decoder.wait()


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "current": None,
        "history": []
    }


def pick_next_track(all_tracks, history):
    available = [t for t in all_tracks if t not in history]

    if not available:
        history.clear()
        available = all_tracks.copy()

    return random.choice(available)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_all_tracks():
    return [str(p.resolve()) for p in Path(SONGS_PATH).glob("*.mp3")]


def update_metadata(track):
    artist = "Unknown"
    title = ""

    try:
        audio = MP3(track)
        artist = audio.get('TPE1').text[0]
        title = audio.get('TIT2').text[0]
    except ID3NoHeaderError:
        pass
    except Exception as e:
        print(f"⚠ Error leyendo metadata: {e}")

    metadata = {
        "title": title,
        "artist": artist
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def start_api():
    from .api import app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="warning"
    )

def main():
    all_tracks = get_all_tracks()
    if not all_tracks:
        raise RuntimeError("No se encontraron MP3 en la carpeta music")

    ffmpeg_process = start_ffmpeg()
    state = load_state()

    while True:
        track = pick_next_track(all_tracks, state["history"])

        state["current"] = track
        save_state(state)

        print(f"▶ Reproduciendo: {Path(track).name}")
        update_metadata(track)
        play_track(track, ffmpeg_process)

        state["history"].append(track)
        state["current"] = None
        state["history"] = state["history"][-HISTORY_SIZE:]

        save_state(state)


if __name__ == "__main__":
    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )
    api_thread.start()

    main()