import requests
from bs4 import BeautifulSoup

URL = "https://www.fmtiempo.cl"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_current_song():
    response = requests.get(URL, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    air = soup.find("div", id="air")
    if not air:
        return None, None

    artist = air.find("h3").get_text(strip=True)
    song = air.find("h4").get_text(strip=True)

    return artist, song