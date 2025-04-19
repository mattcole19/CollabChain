from services.spotify import SpotifyAPI
from models.artist import Artist
from collections import defaultdict
from services.path_finder import PathFinder


def main():
    spotify = SpotifyAPI()
    path_finder = PathFinder(spotify)

    # path = path_finder.find_path("MGK", "Trippie Redd")
    # print(path)

    artist_name = "Lil Wayne"
    artist = spotify.get_artist_by_name(artist_name)
    collaborators = spotify.get_artist_collaborators(artist)
    print(collaborators)

    path = path_finder.find_path("MGK", "Eminem")
    print(path)

    # artist_name = input("Enter artist name to find collaborators: ")
    # artists = [
    #     "Eminem",
    #     # "Kendrick Lamar",
    #     "Travis Scott",
    #     "Drake",
    #     "Nicki Minaj",
    #     "Lil Wayne",
    #     "Glass Animals",
    #     "Taylor Swift",
    #     "Bryce Vine",
    # ]

    # for artist_name in artists:
    #     artist = spotify.get_artist_by_name(artist_name)
    #     if not artist:
    #         print(f"Could not find artist: {artist_name}")
    #         continue

    #     print(f"\nFinding collaborators for {artist.name}...")
    #     collaborations = spotify.get_artist_collaborators(artist)

    #     # Group collaborations by artist
    #     artist_collabs = defaultdict(list)
    #     for collab in collaborations:
    #         artist_collabs[collab.artist.name].append(collab)

    #     # Print results
    #     print(f"\nFound {len(artist_collabs)} collaborators:")
    #     for artist_name, collabs in sorted(artist_collabs.items()):
    #         print(f"\n{artist_name}:")
    #         for collab in sorted(collabs, key=lambda x: x.release_date, reverse=True):
    #             print(
    #                 f"  - {collab.track_name} (from {collab.album_name}, {collab.release_date.year})"
    #             )


if __name__ == "__main__":
    main()
