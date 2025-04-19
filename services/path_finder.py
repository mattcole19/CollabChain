from typing import List, Optional, Dict, Set, Tuple
from collections import deque
from dataclasses import dataclass

from models.artist import Artist, Collaboration
from services.spotify import SpotifyAPI


@dataclass
class ArtistPath:
    """Represents a path between two artists through collaborations"""

    path: List[Tuple[Artist, Optional[str]]]  # List of (artist, connecting_song) pairs

    def __str__(self) -> str:
        result = []
        for i, (artist, song) in enumerate(self.path):
            if i == 0:
                result.append(f"{artist.name}")
            else:
                result.append(f"→ {artist.name} (via '{song}')")
        return " ".join(result)


class PathFinder:
    def __init__(self, spotify: SpotifyAPI):
        self.spotify = spotify

    def _get_cached_collaborators(self, artist_id: str) -> Optional[Set[Collaboration]]:
        """Check if collaborators for an artist are already cached"""
        return self.spotify.get_cached_collaborators(artist_id)

    def _split_collaborators_by_cache(
        self, collaborations: Set[Collaboration]
    ) -> Tuple[List[Artist], List[Artist]]:
        """Split collaborator artists into cached and uncached groups"""
        cached = []
        uncached = []

        for collab in collaborations:
            if self._get_cached_collaborators(collab.artist.id) is not None:
                cached.append(collab.artist)
            else:
                uncached.append(collab.artist)

        return cached, uncached

    def find_path(
        self, start_artist_name: str, end_artist_name: str, max_depth: int = 3
    ) -> Optional[ArtistPath]:
        """
        Find a path between two artists through collaborations.
        Prioritizes checking cached collaborators first.
        """
        # First get both artists
        start_artist = self.spotify.get_artist_by_name(start_artist_name)
        end_artist = self.spotify.get_artist_by_name(end_artist_name)

        if not start_artist or not end_artist:
            return None

        print(f"Searching for path from {start_artist.name} to {end_artist.name}...")

        # Track visited artists and their paths
        visited = {start_artist.id}
        paths = {start_artist.id: [(start_artist, None)]}

        # Queue for artists to check (will contain tuples of (artist, is_cached))
        queue = deque([(start_artist, True)])  # Start artist is effectively cached

        while queue and len(visited) <= max_depth * 100:  # Limit total artists checked
            current_artist, is_cached = queue.popleft()
            current_path = paths[current_artist.id]

            # Get collaborations for current artist
            collaborations = self.spotify.get_artist_collaborators(current_artist)

            # Split collaborators into cached and uncached
            cached_artists, uncached_artists = self._split_collaborators_by_cache(
                collaborations
            )

            # Create a mapping of artist to their collaboration info
            collab_info = {
                collab.artist.id: collab.track_name for collab in collaborations
            }

            # First check cached artists
            for next_artist in cached_artists:
                if next_artist.id not in visited:
                    new_path = current_path + [
                        (next_artist, collab_info[next_artist.id])
                    ]

                    if next_artist.id == end_artist.id:
                        return ArtistPath(new_path)

                    visited.add(next_artist.id)
                    paths[next_artist.id] = new_path
                    queue.append((next_artist, True))

            # Then add uncached artists to the queue
            for next_artist in uncached_artists:
                if next_artist.id not in visited:
                    new_path = current_path + [
                        (next_artist, collab_info[next_artist.id])
                    ]

                    if next_artist.id == end_artist.id:
                        return ArtistPath(new_path)

                    visited.add(next_artist.id)
                    paths[next_artist.id] = new_path
                    queue.append((next_artist, False))

            # Print progress with cache info
            print(
                f"Checked {len(visited)} artists... ({len(cached_artists)} cached, {len(uncached_artists)} uncached)"
            )

        return None
