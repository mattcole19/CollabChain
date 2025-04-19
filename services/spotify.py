from typing import Optional, Dict, List, Set, Iterator
import requests
import time
from datetime import datetime
from urllib.parse import urlencode
import base64
import os
from dotenv import load_dotenv

from models.artist import Artist, Collaboration
from models.track import Track
from utils.cache import Cache


class SpotifyAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing Spotify credentials in .env file")

        self.token = None
        self.cache = Cache(cache_dir=".cache/spotify")
        # self._setup_rate_limiter()

    def _setup_rate_limiter(self, requests_per_second: int = 5):
        self.last_request: Optional[datetime] = None
        self.minimum_interval = 1.0 / requests_per_second

    def get_artist_by_name(self, name: str) -> Optional[Artist]:
        """Search for an artist by name and return the best match"""
        cache_key = f"artist_search_{name}"
        cached = self.cache.get(cache_key)
        if cached:
            return Artist.from_spotify_data(cached)

        results = self._make_request(
            "search", params={"q": name, "type": "artist", "limit": 1}
        )

        if not results["artists"]["items"]:
            return None

        artist_data = results["artists"]["items"][0]
        self.cache.set(cache_key, artist_data)
        return Artist.from_spotify_data(artist_data)

    def get_artist_collaborators(self, artist: Artist) -> Set[Collaboration]:
        """
        Get all artists that have collaborated with the given artist,
        including information about their collaborations
        """
        print(f"Getting collaborators for {artist.name}")
        cache_key = f"collaborations_{artist.id}"
        cached = self.cache.get(cache_key)
        if cached:
            print(f"Have collaborations cached for {artist.name}")
            return {
                Collaboration(
                    artist=Artist.from_spotify_data(collab_data["artist"]),
                    track_name=collab_data["track_name"],
                    album_name=collab_data["album_name"],
                    release_date=datetime.fromisoformat(collab_data["release_date"]),
                    track_uri=collab_data["track_uri"],
                )
                for collab_data in cached
            }
        print(f"No collaborations cached for {artist.name}. Gathering...")
        collaborations: Set[Collaboration] = set()

        # Get all albums (including singles)
        for album in self._get_all_artist_albums(artist.id):
            # Get tracks for each album
            print(f"\nGetting tracks for {album['name']}")
            for track in self._get_album_tracks(album["id"]):
                # Look for collaborators in this track
                for track_artist in track["artists"]:
                    if track_artist["id"] != artist.id:
                        # Get full artist data
                        collab_artist_data = self._get_artist_data(track_artist["id"])
                        if collab_artist_data:
                            collaboration = Collaboration(
                                artist=Artist.from_spotify_data(collab_artist_data),
                                track_name=track["name"],
                                album_name=album["name"],
                                release_date=datetime.strptime(
                                    track.get(
                                        "release_date",
                                        album.get("release_date", "1970-01-01"),
                                    ),
                                    "%Y-%m-%d",
                                ),
                                track_uri=track["uri"],
                            )
                            collaborations.add(collaboration)
            print(f"Done getting tracks for {album['name']}\n")

        # Cache the collaboration data
        cache_data = [
            {
                "artist": self._get_artist_data(collab.artist.id),
                "track_name": collab.track_name,
                "album_name": collab.album_name,
                "release_date": collab.release_date.isoformat(),
                "track_uri": collab.track_uri,
            }
            for collab in collaborations
        ]
        self.cache.set(cache_key, cache_data)

        return collaborations

    def _get_all_artist_albums(self, artist_id: str) -> Iterator[dict]:
        """Get all albums for an artist, handling pagination"""
        offset = 0
        limit = 50  # Maximum allowed by Spotify

        while True:
            cache_key = f"artist_albums_{artist_id}_{offset}"
            cached = self.cache.get(cache_key)

            if cached:
                albums = cached
            else:
                response = self._make_request(
                    f"artists/{artist_id}/albums",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "include_groups": "album,single",
                    },
                )
                albums = response["items"]
                self.cache.set(cache_key, albums)

            yield from albums

            if len(albums) < limit:
                break
            offset += limit

    def _get_album_tracks(self, album_id: str) -> Iterator[dict]:
        """Get all tracks from an album, handling pagination"""
        cache_key = f"album_tracks_{album_id}"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        tracks = []
        offset = 0
        limit = 50

        while True:
            response = self._make_request(
                f"albums/{album_id}/tracks", params={"limit": limit, "offset": offset}
            )

            tracks.extend(response["items"])

            if len(response["items"]) < limit:
                break
            offset += limit

        # Get full track details in batches of 50
        full_tracks = []
        for i in range(0, len(tracks), 50):
            track_batch = tracks[i : i + 50]
            track_ids = [track["id"] for track in track_batch]
            full_tracks_response = self._make_request(
                "tracks", params={"ids": ",".join(track_ids)}
            )
            full_tracks.extend(full_tracks_response["tracks"])

        self.cache.set(cache_key, full_tracks)
        return full_tracks

    def _get_artist_data(self, artist_id: str) -> Optional[dict]:
        """Get full artist data"""
        cache_key = f"artist_data_{artist_id}"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        try:
            artist_data = self._make_request(f"artists/{artist_id}")
            self.cache.set(cache_key, artist_data)
            return artist_data
        except requests.exceptions.RequestException:
            return None

    def _make_request(
        self, endpoint: str, method: str = "GET", params: Optional[dict] = None
    ) -> dict:
        """Make a request to the Spotify API with rate limiting and caching"""
        if not self.token:
            self._get_token()

        # # Rate limiting
        # if self.last_request:
        #     elapsed = (datetime.now() - self.last_request).total_seconds()
        #     if elapsed < self.minimum_interval:
        #         time.sleep(self.minimum_interval - elapsed)

        base_url = "https://api.spotify.com/v1"
        headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{base_url}/{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"
        start_time = time.time()
        response = requests.request(method, url, headers=headers)
        end_time = time.time()
        # print(f"Time taken for '{endpoint}': {end_time - start_time} seconds")
        # self.last_request = datetime.now()

        if response.status_code == 429:
            print(f"Rate limit exceeded: {response.text}")
            # retry_after = int(response.headers.get("Retry-After", 1))
            # time.sleep(retry_after)
            # return self._make_request(endpoint, method, params)

        response.raise_for_status()
        return response.json()

    def _get_token(self) -> None:
        """Get Spotify access token using client credentials flow"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth_base64}"},
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def get_cached_collaborators(self, artist_id: str) -> Optional[Set[Collaboration]]:
        """Check if collaborators for an artist are in cache"""
        cache_key = f"collaborations_{artist_id}"
        cached = self.cache.get(cache_key)

        if cached:
            return {
                Collaboration(
                    artist=Artist.from_spotify_data(collab_data["artist"]),
                    track_name=collab_data["track_name"],
                    album_name=collab_data["album_name"],
                    release_date=datetime.fromisoformat(collab_data["release_date"]),
                    track_uri=collab_data["track_uri"],
                )
                for collab_data in cached
            }
        return None
