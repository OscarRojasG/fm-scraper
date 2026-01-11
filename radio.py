import os
import random
import json
import subprocess
from pathlib import Path
from settings import RADIO_PATH, RADIO_SONGS_PATH, RADIO_PLAYLIST_FILE, RADIO_STATE_FILE
from dotenv import load_dotenv

# ================= CONFIG =================

load_dotenv()
os.makedirs(RADIO_PATH, exist_ok=True)

FFMPEG_PATH  = os.getenv('FFMPEG_PATH')
ICECAST_URL  = os.getenv('ICECAST_URL')
QUEUE_SIZE = 200
SONGS_PATH = Path(RADIO_SONGS_PATH)
STATE_FILE = Path(os.path.join(RADIO_PATH, RADIO_STATE_FILE))
PLAYLIST_FILE = Path(os.path.join(RADIO_PATH, RADIO_PLAYLIST_FILE))

FFMPEG_CMD = [
    FFMPEG_PATH, "-re",
    "-f", "concat", "-safe", "0",
    "-i", str(PLAYLIST_FILE),
    "-vn",
    "-c:a", "libmp3lame",
    "-b:a", "192k",
    "-f", "mp3",
    ICECAST_URL
]

# =========================================


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"queue": [], "history": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_all_tracks():
    return [str(p.resolve()) for p in Path(SONGS_PATH).glob("*.mp3")]


def refill_queue(state, all_tracks):
    used = set(state["queue"]) | set(state["history"])
    available = [t for t in all_tracks if t not in used]

    random.shuffle(available)

    while len(state["queue"]) < QUEUE_SIZE:
        if not available:
            # si se acabaron, reseteamos historial
            state["history"] = []
            available = [t for t in all_tracks if t not in state["queue"]]
            random.shuffle(available)

        state["queue"].append(available.pop())


def write_playlist(queue):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        for track in queue:
            f.write(f"file '{track.replace('\\', '/')}'\n")


def run_ffmpeg():
    subprocess.run(FFMPEG_CMD)


def main():
    all_tracks = get_all_tracks()
    if not all_tracks:
        raise RuntimeError("No se encontraron MP3 en la carpeta music")

    while True:
        state = load_state()

        refill_queue(state, all_tracks)
        write_playlist(state["queue"])
        save_state(state)

        print(f"▶ Reproduciendo cola de {len(state['queue'])} canciones")
        run_ffmpeg()

        # cuando termina ffmpeg, toda la cola pasa a historial
        state["history"].extend(state["queue"])
        state["queue"] = []

        # limitamos historial para que no crezca infinito
        state["history"] = state["history"][-QUEUE_SIZE:]

        save_state(state)


if __name__ == "__main__":
    main()