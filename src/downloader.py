from __future__ import unicode_literals
from yt_dlp import YoutubeDL
import yt_dlp.utils
from .settings import DOWNLOADS_PATH
import os
import glob
from dotenv import load_dotenv
from mutagen.id3 import ID3, TXXX, TIT2, TPE1


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class Downloader:
    def __init__(self):
        load_dotenv()
        self.ffmpeg_path = os.getenv('FFMPEG_PATH')
        self.current_downloads = CurrentDownloads()
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)

    def yt_download(self, id, artist, title):
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': self.ffmpeg_path,
            'outtmpl': os.path.join(DOWNLOADS_PATH, '%(artist)s - %(title)s.%(ext)s'),
            'cookiefile': 'cookies.txt',

            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {'key': 'FFmpegMetadata'}
            ],

            'addmetadata': True,
            'logger': MyLogger(),
            'restrictfilenames': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f'https://www.youtube.com/watch?v={id}',
                download=True
            )
        mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3'
        self.write_metadata(mp3_path, id, artist, title)

    def write_metadata(self, mp3_path, video_id, artist, title):
        audio = ID3(mp3_path)

        audio.add(
            TXXX(
                encoding=3,
                desc='VIDEO_ID',
                text=video_id
            )
        )
        audio.add(TIT2(encoding=3, text=title))
        audio.add(TPE1(encoding=3, text=artist))

        audio.save(v2_version=3)
    
    def download(self, id, artist, title):
        if self.current_downloads.exists(artist, title):
            if self.current_downloads.same_id(artist, title, id):
                print(f"⚠️ Canción sin cambios: {artist} - {title}")
                return
            self.current_downloads.remove(artist, title)
            print(f"🔄 Actualizando: {artist} - {title}")
        else:
            print(f"✅ Nueva descarga: {artist} - {title}")

        self.yt_download(id, artist, title)
        self.current_downloads.update()


class CurrentDownloads:
    def __init__(self):
        self.update()
    
    def exists(self, artist, title):
        return (artist, title) in self.current_downloads
    
    def same_id(self, artist, title, id):
        return self.current_downloads[(artist, title)]['id'] == id
    
    def remove(self, artist, title):
        os.remove(self.current_downloads[(artist, title)]['filename'])
        self.update()

    def update(self):
        self.current_downloads = dict()
        for filename in glob.glob(os.path.join(DOWNLOADS_PATH, '**', '*.mp3'), recursive=True):    
            audio = ID3(filename)
            artist = audio.get('TPE1').text[0]
            title = audio.get('TIT2').text[0]
            video_id = audio.getall('TXXX:VIDEO_ID')[0].text[0]
            self.current_downloads[(artist, title)] = {
                'id': video_id,
                'filename': filename
            }
    
    def summary(self):
        # Cabecera
        print(f"{'Índice':<6} {'Artista':<30} {'Título':<40} {'Archivo':<40}")
        print("-" * 90)  # línea separadora
        
        for i, (artist, title) in enumerate(self.current_downloads):
            filename = self.current_downloads[(artist, title)]['filename']
            filename = os.path.basename(filename)
            print(f"{i:<6} {artist:<30} {title:<40} {filename:<40}")

    
def clean_downloads(data):
    current_downloads = CurrentDownloads()
    songs_map = dict()
    for song in data:
        artist, title, id = song
        songs_map[(artist, title)] = id

    for (artist, title) in current_downloads.current_downloads:
        if not (artist, title) in songs_map:
            current_downloads.remove(artist, title)
            print(f"❌ Eliminando: {artist} - {title}")

def print_downloaded_songs():
    CurrentDownloads().summary()