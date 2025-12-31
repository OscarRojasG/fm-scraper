import csv
import os
import time
from datetime import datetime
from request import get_current_song
from settings import SONGS_PATH

def get_csv_filename():
    os.makedirs(SONGS_PATH, exist_ok=True)
    filename = datetime.now().strftime("%d-%m-%Y") + ".csv"
    return os.path.join(SONGS_PATH, filename)


def get_last_record(csv_file):
    if not os.path.exists(csv_file):
        return None, None

    with open(csv_file, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        if len(rows) <= 1:
            return None, None
        return rows[-1][0], rows[-1][1]


def append_to_csv(csv_file, artist, song):
    file_exists = os.path.exists(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["artista", "cancion", "hora"])

        writer.writerow([
            artist,
            song,
            datetime.now().strftime("%H:%M:%S")
        ])


def main():
    while True:
        try:
            artist, song = get_current_song()
            if not artist or not song:
                print("No se pudo obtener la canción")
                time.sleep(60)
                continue

            csv_file = get_csv_filename()
            last_artist, last_song = get_last_record(csv_file)

            if artist != last_artist or song != last_song:
                append_to_csv(csv_file, artist, song)
                print(f"🎵 Nueva canción: {artist} - {song}")
            else:
                print("⏳ Canción sin cambios")

        except Exception as e:
            print("Error:", e)

        time.sleep(60)


if __name__ == "__main__":
    main()