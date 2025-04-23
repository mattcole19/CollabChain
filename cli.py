import argparse
from services.spotify import SpotifyAPI
from services.path_finder import PathFinder
from collections import defaultdict


def find_path_command():
    """Interactive command to find path between two artists"""
    spotify = SpotifyAPI()
    path_finder = PathFinder(spotify)

    start_name = input("Enter first artist name: ")
    end_name = input("Enter second artist name: ")

    print(f"\nSearching for connection between {start_name} and {end_name}...")
    path = path_finder.find_path(start_name, end_name)

    if path:
        print("\nFound path!")
        print(path)
    else:
        print("\nNo path found between these artists.")


def show_collaborations_command(artist_name: str):
    """Show all collaborations for a given artist"""
    spotify = SpotifyAPI()

    artist = spotify.get_artist_by_name(artist_name)
    if not artist:
        print(f"Could not find artist: {artist_name}")
        return

    print(f"\nFinding collaborators for {artist.name}...")
    collaborations = spotify.get_artist_collaborators(artist)

    # Group collaborations by artist
    artist_collabs = defaultdict(list)
    for collab in collaborations:
        artist_collabs[collab.artist.name].append(collab)

    # Print results
    print(f"\nFound {len(artist_collabs)} collaborators:")
    for collab_artist_name, collabs in sorted(artist_collabs.items()):
        print(f"\n{collab_artist_name}:")
        for collab in sorted(collabs, key=lambda x: x.release_date, reverse=True):
            print(
                f"  - {collab.track_name} (from {collab.album_name}, {collab.release_date.year})"
            )


def main():
    parser = argparse.ArgumentParser(description="Artist Connections CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Path command
    path_parser = subparsers.add_parser("path", help="Find path between two artists")

    # Collaborations command
    collab_parser = subparsers.add_parser(
        "collabs", help="Show all collaborations for an artist"
    )
    collab_parser.add_argument("artist", help="Name of the artist")

    args = parser.parse_args()

    if args.command == "path":
        find_path_command()
    elif args.command == "collabs":
        show_collaborations_command(args.artist)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
