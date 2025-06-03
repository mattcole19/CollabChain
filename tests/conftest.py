"""
Test Data Relationships:

Artists: Alpha, Beta, Gamma, Delta, Epsilon

Collaboration Graph:
    Alpha ─────("Song One")────► Beta
       │                          │
       └─("Song Two")─► Gamma ◄──("Song Three")
                          │
                    ("Song Four")
                          │
                          ▼
                        Delta ─("Song Five")─► Epsilon

Expected Paths:
- Alpha -> Beta: direct collaboration via "Song One"
- Alpha -> Gamma: direct collaboration via "Song Two"
- Alpha -> Delta: through Gamma via "Song Two" -> "Song Four"
- Beta -> Delta: through Gamma via "Song Three" -> "Song Four"
- Alpha -> Epsilon: through Gamma, Beta, and Delta via "Song Two" -> "Song Four" -> "Song Five"
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from models.artist import Artist, Collaboration
from services.spotify import SpotifyAPI


@pytest.fixture
def mock_spotify():
    """Create a mock SpotifyAPI with controlled responses"""
    spotify = Mock(spec=SpotifyAPI)

    # Mock artist data
    alpha = Artist(
        id="alpha_id",
        name="Alpha",
        genres=tuple(["pop", "rock"]),
        popularity=82,
        uri="spotify:artist:alpha_id",
        collaborators=frozenset(),
    )

    beta = Artist(
        id="beta_id",
        name="Beta",
        genres=tuple(["rock"]),
        popularity=85,
        uri="spotify:artist:beta_id",
        collaborators=frozenset(),
    )

    gamma = Artist(
        id="gamma_id",
        name="Gamma",
        genres=tuple(["indie"]),
        popularity=78,
        uri="spotify:artist:gamma_id",
        collaborators=frozenset(),
    )

    delta = Artist(
        id="delta_id",
        name="Delta",
        genres=tuple(["pop"]),
        popularity=90,
        uri="spotify:artist:delta_id",
        collaborators=frozenset(),
    )

    epsilon = Artist(
        id="epsilon_id",
        name="Epsilon",
        genres=tuple(["electronic"]),
        popularity=75,
        uri="spotify:artist:epsilon_id",
        collaborators=frozenset(),
    )

    # Mock collaboration data
    alpha_collabs = {
        Collaboration(
            artist=beta,
            track_name="Song One",
            album_name="First Album",
            release_date=datetime(2023, 1, 1),
            track_uri="spotify:track:song_one",
        ),
        Collaboration(
            artist=gamma,
            track_name="Song Two",
            album_name="First Album",
            release_date=datetime(2023, 1, 1),
            track_uri="spotify:track:song_two",
        ),
    }

    beta_collabs = {
        Collaboration(
            artist=gamma,
            track_name="Song Three",
            album_name="Second Album",
            release_date=datetime(2023, 2, 1),
            track_uri="spotify:track:song_three",
        )
    }

    gamma_collabs = {
        Collaboration(
            artist=delta,
            track_name="Song Four",
            album_name="Third Album",
            release_date=datetime(2023, 3, 1),
            track_uri="spotify:track:song_four",
        )
    }

    delta_collabs = {
        Collaboration(
            artist=epsilon,
            track_name="Song Five",
            album_name="Fourth Album",
            release_date=datetime(2023, 4, 1),
            track_uri="spotify:track:song_five",
        )
    }

    # Configure mock responses
    def get_artist_by_name(name: str) -> Artist:
        return {
            "Alpha": alpha,
            "Beta": beta,
            "Gamma": gamma,
            "Delta": delta,
            "Epsilon": epsilon,
        }.get(name)

    def get_artist_collaborators(artist: Artist) -> set[Collaboration]:
        return {
            "alpha_id": alpha_collabs,
            "beta_id": beta_collabs,
            "gamma_id": gamma_collabs,
            "delta_id": delta_collabs,
            "epsilon_id": set(),
        }.get(artist.id, set())

    spotify.get_artist_by_name.side_effect = get_artist_by_name
    spotify.get_artist_collaborators.side_effect = get_artist_collaborators

    # Add async versions of the methods
    async def get_artist_by_name_async(name: str) -> Artist:
        return get_artist_by_name(name)

    async def get_artist_collaborators_async(artist: Artist) -> set[Collaboration]:
        return get_artist_collaborators(artist)

    spotify.get_artist_by_name_async.side_effect = get_artist_by_name_async
    spotify.get_artist_collaborators_async.side_effect = get_artist_collaborators_async

    return spotify
