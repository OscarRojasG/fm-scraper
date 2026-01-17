from ytmusicapi import YTMusic, OAuthCredentials
import ytmusicapi
from dotenv import load_dotenv
import os
import csv
import json
import glob
from .settings import SONGS_PATH, PLAYLISTS_FILE, DATA_FOLDER, DEFAULT_DATA_FILE


def read_songs():
    songs = []
    for filename in glob.glob(os.path.join(SONGS_PATH, "*.csv")):
        with open(filename, newline="", encoding="utf-8") as file:
            csv_file = csv.reader(file)
            header = next(csv_file)
            songs += list(csv_file)
    return songs
    

def read_data(filename=DEFAULT_DATA_FILE):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    path = os.path.join(DATA_FOLDER, filename)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # Saltar encabezados
            return [tuple(row) for row in reader]
    return []
    

def create_playlist(ytmusic: YTMusic, name: str):
    playlist_id = ytmusic.create_playlist(name, "FMTiempo " + name)

    # Si el archivo existe, lo cargamos
    if os.path.exists(PLAYLISTS_FILE):
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            playlists = json.load(f)
    else:
        playlists = {}

    # Guardamos / actualizamos la playlist
    playlists[name] = playlist_id

    # Escribimos el JSON completo
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4, ensure_ascii=False)

    return playlist_id


def get_playlist_id(ytmusic: YTMusic, name):
    if os.path.exists(PLAYLISTS_FILE):
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            playlists = json.load(f)

            if name in playlists:
                playlist_id = playlists[name]
            else:
                return None

    try:
        ytmusic.get_playlist(playlist_id)
        return playlist_id
    except:
        return None    


def add_songs_to_playlist(ytmusic: YTMusic, playlist_name, songs, start=None, end=None):
    playlist_id = get_playlist_id(ytmusic, playlist_name)
    if playlist_id is None:
        playlist_id = create_playlist(ytmusic, playlist_name)

    if start is None:
        start = 0

    if end is None:
        end = len(songs)
    else:
        end = min(end, len(songs))

    for i in range(start, end):
        song = songs[i]
        query = song[0] + " " + song[1]

        results = ytmusic.search(query, limit=5)
        for result in results:
            if result['resultType'] == 'song' or result['resultType'] == 'video':
                song_id = result['videoId']
                print(result['title'])
                break

        ytmusic.add_playlist_items(playlist_id, [song_id])
        print(f"✅ Canción añadida: {song[1]} - {song[0]} ({i})")


def get_unique(songs: list):
    unique = set()
    for song in songs:
        unique.add((song[0], song[1]))
    return unique


def get_pending(songs: list):
    songs = get_unique(songs)
    data = read_data()

    entries = set((entry[0], entry[1]) for entry in data)
    return songs - entries


def populate_data(ytmusic: YTMusic, populate_limit=None, filename=DEFAULT_DATA_FILE):
    songs = read_songs()
    songs = get_pending(songs)

    if populate_limit is None:
        populate_limit = len(songs)

    entries = []

    for i, song in enumerate(songs):
        if i == populate_limit:
            break

        query = f"{song[0]} {song[1]}"
        result = ytmusic.search(query, filter='songs', limit=1)[0]
        song_id = result['videoId']
        entries.append((song[0], song[1], song_id))

    # Leer datos antiguos y combinarlos
    data = read_data()
    data += entries

    # Guardar en CSV
    with open(os.path.join(DATA_FOLDER, filename), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["artist", "name", "id"])
        writer.writerows(data)


def auth():
    AUTHORIZATION = os.getenv('AUTHORIZATION')
    COOKIE = os.getenv('COOKIE')

    headers = {
        "Accept": "*/*",
        "Authorization": AUTHORIZATION,
        "Content-Type": "application/json",
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
        "Cookie": COOKIE
    }
    headers_raw = "\n".join(f"{k}: {v}" for k, v in headers.items())

    ytmusicapi.setup(filepath="browser.json", headers_raw=headers_raw)
    return YTMusic('browser.json')


def main():
    load_dotenv()
    """
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))
    """

    AUTHORIZATION = os.getenv('AUTHORIZATION')
    COOKIE = os.getenv('COOKIE')

    headers = {
        "Accept": "*/*",
        "Authorization": AUTHORIZATION,
        "Content-Type": "application/json",
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
        "Cookie": COOKIE
    }
    headers_raw = "\n".join(f"{k}: {v}" for k, v in headers.items())

    ytmusicapi.setup(filepath="browser.json", headers_raw=headers_raw)
    ytmusic = YTMusic('browser.json')

    filename = "31-12-2025.csv"
    songs = read_songs(filename)
    playlist_name = os.path.splitext(filename)[0]

    start = 335
    end = None
    
    add_songs_to_playlist(ytmusic, playlist_name, songs, start, end)


if __name__ == "__main__":
    main()