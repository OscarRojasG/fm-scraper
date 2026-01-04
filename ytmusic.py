from ytmusicapi import YTMusic, OAuthCredentials
import ytmusicapi
from dotenv import load_dotenv
import os
import csv
import json
from settings import SONGS_PATH, PLAYLISTS_FILE


def read_csv(filename):
    with open(os.path.join(SONGS_PATH, filename), newline="", encoding="utf-8") as file:
        csv_file = csv.reader(file)
        header = next(csv_file)
        return list(csv_file)
    

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
    songs = read_csv(filename)
    playlist_name = os.path.splitext(filename)[0]

    start = 335
    end = None
    
    add_songs_to_playlist(ytmusic, playlist_name, songs, start, end)


if __name__ == "__main__":
    main()