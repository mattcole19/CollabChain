from typing import List, Optional, Dict, Set, Tuple, Deque
from collections import deque
from dataclasses import dataclass
import asyncio
import aiohttp

from models.artist import Artist, Collaboration
from services.spotify import SpotifyAPI


@dataclass
class PathNode:
    """Represents a node in the path with the artist and the song that led to them"""

    artist: Artist
    connecting_song: Optional[str] = None


@dataclass
class ArtistPath:
    """Represents a complete path between two artists"""

    path: List[PathNode]

    def __str__(self) -> str:
        result = []
        for i, node in enumerate(self.path):
            if i == 0:
                result.append(f"{node.artist.name}")
            else:
                result.append(f"→ {node.artist.name} (via '{node.connecting_song}')")
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

    async def _split_collaborators_by_cache_async(
        self, collaborations: Set[Collaboration]
    ) -> Tuple[List[Artist], List[Artist]]:
        """Async version of splitting collaborators into cached and uncached groups"""
        cached = []
        uncached = []

        for collab in collaborations:
            if (
                await self.spotify.get_cached_collaborators_async(collab.artist.id)
                is not None
            ):
                cached.append(collab.artist)
            else:
                uncached.append(collab.artist)

        return cached, uncached

    async def find_path_async(
        self, start_artist_name: str, end_artist_name: str, max_depth: int = 3
    ) -> Optional[ArtistPath]:
        """
        Find a path between two artists through their collaborations asynchronously.

        Args:
            start_artist_name: Name of the starting artist
            end_artist_name: Name of the target artist
            max_depth: Maximum number of hops between artists (e.g. max_depth=3 means up to 3 artists can be between start and end)

        Returns:
            Optional[ArtistPath]: The path between artists if found, None otherwise
        """
        # Get both artists
        start_artist = await self.spotify.get_artist_by_name_async(start_artist_name)
        end_artist = await self.spotify.get_artist_by_name_async(end_artist_name)

        if not start_artist or not end_artist:
            print(
                f"Could not find one or both artists: {start_artist_name}, {end_artist_name}"
            )
            return None

        print(f"Searching for path from {start_artist.name} to {end_artist.name}...")

        # Track visited artists and their paths
        visited_artists: Set[str] = {start_artist.id}

        # For each artist ID, store the path that led to them
        artist_paths: Dict[str, List[PathNode]] = {
            start_artist.id: [PathNode(artist=start_artist)]
        }

        # Queue will store (artist, is_cached, depth) tuples
        queue: Deque[Tuple[Artist, bool, int]] = deque([(start_artist, True, 0)])

        while queue:
            # Take up to 5 artists to process concurrently
            current_batch: List[Tuple[Artist, bool, int]] = []
            while queue and len(current_batch) < 5:
                current_batch.append(queue.popleft())

            if not current_batch:
                break

            print(f"\nProcessing batch of {len(current_batch)} artists...")

            # Get collaborators for all artists in current batch concurrently
            collab_tasks = [
                self.spotify.get_artist_collaborators_async(artist)
                for artist, _, _ in current_batch
            ]

            try:
                collaborations_list = await asyncio.gather(*collab_tasks)
            except Exception as e:
                print(f"Error getting collaborations: {e}")
                continue

            # Process each artist's collaborations
            for (current_artist, _, current_depth), collaborations in zip(
                current_batch, collaborations_list
            ):
                # Skip if we've exceeded max depth
                if current_depth >= max_depth:
                    print(
                        f"Skipping {current_artist.name} because depth limit reached ({current_depth} >= {max_depth})"
                    )
                    continue

                current_path = artist_paths[current_artist.id]
                print(
                    f"Checking {len(collaborations)} collaborators for {current_artist.name} at depth {current_depth}"
                )

                # Process each collaboration
                for collab in collaborations:
                    collaborator = collab.artist

                    if collaborator.id not in visited_artists:
                        # Create new path by extending current path
                        new_path = current_path + [
                            PathNode(
                                artist=collaborator, connecting_song=collab.track_name
                            )
                        ]

                        # Check if we found the target artist
                        if collaborator.id == end_artist.id:
                            print(
                                f"Found path through {current_artist.name} at depth {current_depth + 1}!"
                            )
                            return ArtistPath(new_path)

                        # Add to visited and queue for processing
                        visited_artists.add(collaborator.id)
                        artist_paths[collaborator.id] = new_path
                        # Add to queue with incremented depth
                        queue.append((collaborator, True, current_depth + 1))

                print(f"Checked {len(visited_artists)} artists so far...")

        print(f"No path found within depth limit of {max_depth}")
        return None

    def find_path(
        self, start_artist_name: str, end_artist_name: str, max_depth: int = 3
    ) -> Optional[ArtistPath]:
        """Synchronous version of path finding"""
        # First get both artists
        start_artist = self.spotify.get_artist_by_name(start_artist_name)
        print(f"Start artist: {start_artist}")
        end_artist = self.spotify.get_artist_by_name(end_artist_name)
        print(f"End artist: {end_artist}")

        if not start_artist or not end_artist:
            print(f"Could not find artist: {start_artist_name} or {end_artist_name}")
            return None

        if end_artist == start_artist:
            print("That's the same artist!")
            return ArtistPath([PathNode(artist=start_artist)])

        print(f"Searching for path from {start_artist.name} to {end_artist.name}...")

        # Track visited artists and their paths
        visited = {start_artist.id}
        paths = {start_artist.id: [PathNode(artist=start_artist)]}

        # Queue for artists to check (will contain tuples of (artist, is_cached))
        queue = deque([(start_artist, True)])  # Start artist is effectively cached

        while queue and len(visited) <= max_depth:  # Limit total artists checked
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
                        PathNode(
                            artist=next_artist,
                            connecting_song=collab_info[next_artist.id],
                        )
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
                        PathNode(
                            artist=next_artist,
                            connecting_song=collab_info[next_artist.id],
                        )
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
