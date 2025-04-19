# PLAYGROUND SCRIPT THAT IS NOT USED IN THE PROJECT


import requests
import base64
from urllib.parse import urlencode
import os
import logging
import time
from dotenv import load_dotenv
from typing import Set, List, Dict
from dataclasses import dataclass
from datetime import datetime

load_dotenv()


class SpotifyAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def get_token(self):
        """Get Spotify access token using client credentials flow"""
        print("Getting token")
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print(f"Token received: {self.token}")
            return self.token
        else:
            raise Exception("Failed to get token")

    def make_request(self, endpoint, method="GET", params=None):
        """Make a request to the Spotify API"""
        if not self.token:
            self.get_token()

        base_url = "https://api.spotify.com/v1"
        headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{base_url}/{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"
        start_time = time.time()
        response = requests.request(method, url, headers=headers)
        end_time = time.time()
        print(f"Time taken for {endpoint}: {end_time - start_time} seconds")
        status_code = response.status_code
        if status_code != 200:
            if status_code == 429:
                print(f"Rate limit exceeded {response.text}")
                raise Exception("Rate limit exceeded")
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")
        return response.json()


# Initialize the API
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
spotify = SpotifyAPI(client_id, client_secret)

# # Search for tracks
# results = spotify.make_request(
#     "search", params={"q": "bohemian rhapsody", "type": "track"}
# )


def search_artist(artist_name) -> dict:
    print(f"Searching for artist: {artist_name}")
    results = spotify.make_request(
        "search", params={"q": artist_name, "type": "artist"}
    )
    artist = results["artists"]["items"][0]
    print(f"Artist found: {artist['name']}")
    return artist


# Search for an artist
# eminem = search_artist("Eminem")
# eminem_id = eminem["id"]

# # Get an artist
# eminem_info = spotify.make_request(f"artists/{eminem_id}")
# print(eminem_info)

# mgk = search_artist("MGK")
# mgk_id = mgk["id"]

# mgk_top_tracks = spotify.make_request(f"artists/{mgk_id}/top-tracks?market=US")
# num_tracks = len(mgk_top_tracks["tracks"])
# print(f"Number of top tracks: {num_tracks}")

# for track in mgk_top_tracks["tracks"]:
#     print(track["name"])
#     # print(track["id"])
#     # print(track["album"]["name"])
#     # print(track["album"]["id"])
#     # print(track["album"]["images"][0]["url"])

# mgk_albums = spotify.make_request(f"artists/{mgk_id}/albums?limit=50")
# num_albums = len(mgk_albums["items"])
# print(f"Number of albums: {num_albums}")

# for album in mgk_albums["items"]:
#     print(album["name"])


@dataclass
class CollaborationInfo:
    artist_name: str
    track_name: str
    album_name: str


def get_artist_collaborators(artist_name: str) -> Dict[str, CollaborationInfo]:
    """
    Get all artists that have collaborated with the given artist.
    Returns a dictionary mapping collaborator IDs to CollaborationInfo
    """
    # Step 1: Get artist ID
    artist = search_artist(artist_name)
    artist_id = artist["id"]
    collaborators: Dict[str, CollaborationInfo] = {}

    # Step 2: Get all albums
    albums = spotify.make_request(
        f"artists/{artist_id}/albums",
        params={
            "limit": 50,  # Maximum allowed
            "include_groups": "album,single",  # Include both albums and singles
        },
    )

    # Handle pagination for albums
    all_albums = albums["items"]
    while albums.get("next"):
        albums = spotify.make_request(
            albums["next"].replace("https://api.spotify.com/v1/", "")
        )
        all_albums.extend(albums["items"])

    # Step 3 & 4: Get tracks from albums
    for i in range(0, len(all_albums), 20):  # Process 20 albums at a time (API limit)
        album_batch = all_albums[i : i + 20]
        album_ids = [album["id"] for album in album_batch]

        # Get detailed album info (includes tracks)
        albums_detail = spotify.make_request(
            "albums", params={"ids": ",".join(album_ids)}
        )

        for album in albums_detail["albums"]:
            if not album:  # Skip any null results
                continue

            album_name = album["name"]
            tracks = album["tracks"]["items"]

            # Handle pagination for tracks within album
            while album["tracks"].get("next"):
                more_tracks = spotify.make_request(
                    album["tracks"]["next"].replace("https://api.spotify.com/v1/", "")
                )
                tracks.extend(more_tracks["items"])

            # Get full track details in batches of 50
            track_ids = [track["id"] for track in tracks]
            for j in range(0, len(track_ids), 50):
                track_batch = track_ids[j : j + 50]
                tracks_detail = spotify.make_request(
                    "tracks", params={"ids": ",".join(track_batch)}
                )

                for track in tracks_detail["tracks"]:
                    if not track:  # Skip any null results
                        continue

                    # Find collaborators in this track
                    for track_artist in track["artists"]:
                        # Skip the original artist
                        if track_artist["id"] == artist_id:
                            continue

                        # Add to collaborators if new
                        if track_artist["id"] not in collaborators:
                            collaborators[track_artist["id"]] = CollaborationInfo(
                                artist_name=track_artist["name"],
                                track_name=track["name"],
                                album_name=album_name,
                            )

    print(f"Found {len(collaborators)} collaborators for {artist_name}")
    for collab_id, info in collaborators.items():
        print(
            f"- {info.artist_name} (collaborated on '{info.track_name}' from '{info.album_name}')"
        )

    return collaborators


# Example usage:
if __name__ == "__main__":
    collaborators = get_artist_collaborators("MGK")
