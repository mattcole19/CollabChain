import asyncio
import base64
import os
import time
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Set
from urllib.parse import urlencode

import aiohttp
import requests
from dotenv import load_dotenv

from models.artist import Artist, Collaboration
from utils.cache import Cache
from utils.util import parse_spotify_date


class SpotifyAPI:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing Spotify credentials in .env file")

        self.token = None
        self._get_token()
        self.cache = Cache(cache_dir=".cache/spotify")
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

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

    async def get_artist_by_name_async(self, name: str) -> Optional[Artist]:
        """Async version of get_artist_by_name"""
        cache_key = f"artist_search_{name}"
        cached = self.cache.get(cache_key)
        if cached:
            return Artist.from_spotify_data(cached)

        data = await self._make_request_async(
            "search", params={"q": name, "type": "artist", "limit": 1}
        )
        if data["artists"]["items"]:
            artist_data = data["artists"]["items"][0]
            self.cache.set(cache_key, artist_data)
            return Artist.from_spotify_data(artist_data)
        return None

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

    async def get_artist_collaborators_async(
        self, artist: Artist
    ) -> Set[Collaboration]:
        """Async version of get_artist_collaborators"""
        cache_key = f"collaborators_{artist.id}"
        cached = self.cache.get(cache_key)
        if cached:
            return {Collaboration.from_dict(data) for data in cached}

        collaborations = set()

        # Get all albums
        albums = await self._get_all_artist_albums_async(artist.id)

        # Process albums in smaller batches to avoid rate limiting
        batch_size = 5  # Process 5 albums at a time
        for i in range(0, len(albums), batch_size):
            album_batch = albums[i : i + batch_size]
            track_tasks = [
                self._get_album_tracks_async(album["id"]) for album in album_batch
            ]
            batch_tracks = await asyncio.gather(*track_tasks)

            # Process tracks from this batch
            for tracks in batch_tracks:
                for track in tracks:
                    for track_artist in track["artists"]:
                        if track_artist["id"] != artist.id:
                            artist_data = await self._get_artist_data_async(
                                track_artist["id"]
                            )
                            if artist_data:
                                release_date = parse_spotify_date(
                                    track["album"]["release_date"]
                                )

                                collaboration = Collaboration(
                                    artist=Artist.from_spotify_data(artist_data),
                                    track_name=track["name"],
                                    album_name=track["album"]["name"],
                                    release_date=release_date,
                                    track_uri=track["uri"],
                                )
                                collaborations.add(collaboration)

        # Cache the results
        self.cache.set(cache_key, [collab.to_dict() for collab in collaborations])
        return collaborations

    async def _get_all_artist_albums_async(self, artist_id: str) -> List[Dict]:
        """Get all albums for an artist, handling pagination"""
        print(f"Getting all albums for {artist_id} asynchronously...")
        all_albums = []
        offset = 0
        limit = 50  # Spotify's maximum limit

        while True:
            try:
                data = await self._make_request_async(
                    f"artists/{artist_id}/albums",
                    params={
                        "offset": offset,
                        "limit": limit,
                        "include_groups": "album,single",
                    },
                )

                albums = data["items"]
                all_albums.extend(albums)

                if len(albums) < limit:
                    break

                offset += limit
            except Exception as e:
                print(f"Error fetching albums at offset {offset}: {str(e)}")
                break

        print(f"Found {len(all_albums)} albums for {artist_id}")
        return all_albums

    async def _get_album_tracks_async(self, album_id: str) -> List[Dict]:
        """Get all tracks from an album, handling pagination"""
        all_tracks = []
        offset = 0
        limit = 50

        while True:
            try:
                data = await self._make_request_async(
                    f"albums/{album_id}/tracks",
                    params={"offset": offset, "limit": limit},
                )

                tracks = data["items"]

                # Get full track details in batches
                track_ids = [track["id"] for track in tracks]
                if track_ids:
                    full_tracks_data = await self._make_request_async(
                        "tracks", params={"ids": ",".join(track_ids)}
                    )
                    all_tracks.extend(full_tracks_data["tracks"])

                if len(tracks) < limit:
                    break

                offset += limit
            except Exception as e:
                print(f"Error fetching tracks at offset {offset}: {str(e)}")
                break

        return all_tracks

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

    async def _get_artist_data_async(self, artist_id: str) -> Optional[dict]:
        """"""
        cache_key = f"artist_data_{artist_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        artist_data = await self._make_request_async(f"artists/{artist_id}")
        self.cache.set(cache_key, artist_data)

    def _make_request(
        self, endpoint: str, method: str = "GET", params: Optional[dict] = None
    ) -> dict:
        """Make a request to the Spotify API with rate limiting and caching"""
        if not self.token:
            self._get_token()

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

    async def _make_request_async(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make an async request to the Spotify API with rate limit handling
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method
            params: Query parameters
            data: Request body for POST/PUT requests
            max_retries: Maximum number of retry attempts for rate limiting
        """
        base_url = "https://api.spotify.com/v1"
        headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{base_url}/{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"

        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method, url=url, headers=headers, json=data
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            # Get retry-after time from headers (in seconds)
                            retry_after = int(response.headers.get("Retry-After", "2"))
                            if attempt < max_retries:
                                print(
                                    f"Rate limited on {endpoint}. Waiting {retry_after} seconds..."
                                )
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                raise Exception(f"Max retries exceeded for {endpoint}")
                        elif response.status == 401:
                            raise Exception("Token expired")
                        else:
                            raise Exception(
                                f"Request failed with status {response.status}"
                            )
            except aiohttp.ClientError as e:
                if attempt < max_retries:
                    # Add exponential backoff for network errors
                    wait_time = 2**attempt
                    print(
                        f"Request error for {endpoint}. Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"Request failed after {max_retries} retries: {str(e)}")

        raise Exception(f"Request to {endpoint} failed after all retries")

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
            print(f"Found cached collaborators for {artist_id}")
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
