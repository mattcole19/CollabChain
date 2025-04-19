from dataclasses import dataclass, field
from typing import Set, List, Optional
from datetime import datetime


@dataclass(frozen=True)  # Make the dataclass immutable
class Artist:
    id: str
    name: str
    genres: tuple[str, ...]  # Change from List to tuple since lists aren't hashable
    popularity: int
    uri: str
    collaborators: frozenset[str] = field(
        default_factory=frozenset
    )  # Change from Set to frozenset

    def __hash__(self) -> int:
        return hash(self.id)  # Use the Spotify ID as the hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Artist):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def from_spotify_data(cls, data: dict) -> "Artist":
        return cls(
            id=data["id"],
            name=data["name"],
            genres=tuple(data["genres"]),  # Convert list to tuple
            popularity=data["popularity"],
            uri=data["uri"],
            collaborators=frozenset(),  # Empty frozenset instead of set
        )


@dataclass(frozen=True)
class Collaboration:
    artist: "Artist"
    track_name: str
    album_name: str
    release_date: datetime
    track_uri: str

    def __hash__(self) -> int:
        return hash((self.artist.id, self.track_uri))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Collaboration):
            return NotImplemented
        return self.artist.id == other.artist.id and self.track_uri == other.track_uri
