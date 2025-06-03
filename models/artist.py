from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Artist:
    id: str
    name: str
    genres: tuple[str, ...]
    popularity: int
    uri: str
    collaborators: frozenset[str] = field(default_factory=frozenset)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Artist):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def from_spotify_data(cls, data: dict) -> "Artist":
        return cls(
            id=data["id"],
            name=data["name"],
            genres=tuple(data["genres"]),
            popularity=data["popularity"],
            uri=data["uri"],
            collaborators=frozenset(),
        )


@dataclass(frozen=True)
class Collaboration:
    artist: Artist
    track_name: str
    album_name: str
    release_date: Optional[datetime]
    track_uri: str

    def __hash__(self) -> int:
        return hash((self.artist.id, self.track_uri))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Collaboration):
            return NotImplemented
        return self.artist.id == other.artist.id and self.track_uri == other.track_uri

    def to_dict(self) -> dict:
        return {
            "artist": {
                "id": self.artist.id,
                "name": self.artist.name,
                "genres": list(self.artist.genres),
                "popularity": self.artist.popularity,
                "uri": self.artist.uri,
            },
            "track_name": self.track_name,
            "album_name": self.album_name,
            "release_date": self.release_date.isoformat()
            if self.release_date
            else None,
            "track_uri": self.track_uri,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Collaboration":
        return cls(
            artist=Artist(
                id=data["artist"]["id"],
                name=data["artist"]["name"],
                genres=tuple(data["artist"]["genres"]),
                popularity=data["artist"]["popularity"],
                uri=data["artist"]["uri"],
                collaborators=frozenset(),
            ),
            track_name=data["track_name"],
            album_name=data["album_name"],
            release_date=datetime.fromisoformat(data["release_date"])
            if data["release_date"]
            else None,
            track_uri=data["track_uri"],
        )
