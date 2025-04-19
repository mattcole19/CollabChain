from dataclasses import dataclass
from typing import Set, Optional
from datetime import datetime


@dataclass
class Track:
    id: str
    name: str
    artist_ids: Set[str]
    album_name: str
    release_date: datetime
    popularity: int
    uri: str

    @classmethod
    def from_spotify_data(cls, data: dict) -> "Track":
        return cls(
            id=data["id"],
            name=data["name"],
            artist_ids={artist["id"] for artist in data["artists"]},
            album_name=data["album"]["name"],
            release_date=datetime.strptime(data["album"]["release_date"], "%Y-%m-%d"),
            popularity=data["popularity"],
            uri=data["uri"],
        )
