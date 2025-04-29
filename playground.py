# A fun place to try some things out!


from services.spotify import SpotifyAPI
import asyncio
import time
from services.path_finder import PathFinder


async def get_artist_async(spotify: SpotifyAPI, name: str):
    """Wrapper to show timing for each request"""
    print(f"Starting request for {name}")
    start_time = time.time()
    artist = await spotify.get_artist_by_name_async(name)
    duration = time.time() - start_time
    print(f"Found {artist.name if artist else 'No artist'} in {duration:.2f} seconds")
    return artist


async def get_multiple_artists_async(artists: list[str]):
    """Get multiple artists concurrently"""
    spotify = SpotifyAPI()

    print("\nStarting async requests...")
    start_time = time.time()

    # Create tasks for all artists
    tasks = [get_artist_async(spotify, name) for name in artists]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time
    print(f"\nAll async requests completed in {total_time:.2f} seconds")

    return results


def get_multiple_artists_sync(artists: list[str]):
    """Get multiple artists synchronously for comparison"""
    spotify = SpotifyAPI()

    print("\nStarting sync requests...")
    start_time = time.time()

    results = []
    for name in artists:
        print(f"Starting request for {name}")
        request_start = time.time()
        artist = spotify.get_artist_by_name(name)
        duration = time.time() - request_start
        print(
            f"Found {artist.name if artist else 'No artist'} in {duration:.2f} seconds"
        )
        results.append(artist)

    total_time = time.time() - start_time
    print(f"\nAll sync requests completed in {total_time:.2f} seconds")

    return results


def sync_vs_async_test_searching_for_artists():
    artists = [
        "Taylor Swift",
        "Drake",
        "Ed Sheeran",
        "The Weeknd",
        "Eminem",
        "Rihanna",
        "Justin Bieber",
        "Ariana Grande",
        "Post Malone",
        "Bad Bunny",
        "Glass Animals",
        "Nicki Minaj",
        "Lil Wayne",
        "Travis Scott",
        "Nicki Minaj",
        "Katy Perry",
        "Sabrina Carpenter",
        "Dua Lipa",
        "Billie Eilish",
        "Ariana Grande",
        "Bad Bunny",
    ]
    # Run both sync and async versions to compare

    print("\n" + "=" * 50 + "\n")

    print("Running asynchronous version...")
    async_results = asyncio.run(get_multiple_artists_async(artists))  # ~.49 seconds!

    print("Running synchronous version...")
    sync_results = get_multiple_artists_sync(artists)  # ~ 108s :(


def sync_vs_async_test_path_finding():
    print("Starting async path finding...")
    spotify = SpotifyAPI()

    # Simple test (Direct Collaboration)
    # Sync version
    # artist1 = "MGK"
    # artist2 = "Trippie Redd"
    # path_finder = PathFinder(spotify)
    # path = path_finder.find_path(artist1, artist2)
    # print(path)

    # # Async version
    artist1 = "MGK"
    artist2 = "Trippie Redd"
    path_finder = PathFinder(spotify)
    path = asyncio.run(path_finder.find_path_async(artist1, artist2))
    print(path)

    # # Test (Indirect Collaboration)
    # # Sync version
    # artist1 = "MGK"
    # artist2 = "Travis Scott"
    # path_finder = PathFinder(spotify)
    # path = path_finder.find_path(artist1, artist2)
    # print(path)

    # Async version
    # artist1 = "MGK"
    # artist2 = "Eminem"
    # path_finder = PathFinder(spotify)
    # path = asyncio.run(path_finder.find_path_async(artist1, artist2))
    # print(path)


if __name__ == "__main__":
    sync_vs_async_test_path_finding()
