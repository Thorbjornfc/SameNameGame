"""
Extract tracks from a Spotify playlist into a CSV with:
song name, artist name, embed link, artist image URL.

Usage:
    pip install spotipy
    export SPOTIPY_CLIENT_ID="your_client_id"
    export SPOTIPY_CLIENT_SECRET="your_client_secret"
    python spotify_playlist_to_csv.py "https://open.spotify.com/playlist/..." [output.csv]

Get free credentials at https://developer.spotify.com/dashboard
"""

import csv
import sys
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


# loading variables from .env file
load_dotenv() 
def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python spotify_playlist_to_csv.py <playlist_url_or_id> [output.csv]")

    playlist_ref = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "playlist_tracks.csv"

    # Accept full URL or bare playlist ID
    playlist_id = playlist_ref.rstrip("/").split("/")[-1].split("?")[0]

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    rows = []
    offset = 0
    limit = 100

    while True:
        page = sp.playlist_items(
            playlist_id,
            offset=offset,
            limit=limit,
            fields="items(track(name,id,artists(id,name))),total,next",
        )
        items = page.get("items", [])
        if not items:
            break

        for item in items:
            track = item.get("track")
            if not track or not track.get("id"):
                continue  # skip unavailable/local tracks

            artists = track.get("artists") or []
            artist_name = artists[0]["name"] if artists else ""
            artist_id = artists[0]["id"] if artists else None

            # First artist's image (largest available)
            artist_image = ""
            if artist_id:
                artist = sp.artist(artist_id)
                images = artist.get("images") or []
                if images:
                    artist_image = images[0]["url"]

            rows.append({
                "song_name": track.get("name", ""),
                "artist_name": artist_name,
                "embed_link": f"https://open.spotify.com/embed/track/{track['id']}",
                "artist_image_url": artist_image,
            })

        offset += limit
        if offset >= page.get("total", 0):
            break

    fieldnames = ["song_name", "artist_name", "embed_link", "artist_image_url"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} tracks to {output_path}")


if __name__ == "__main__":
    main()