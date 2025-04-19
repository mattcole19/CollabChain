# Artist Connections

A Python tool to discover connections between music artists through their collaborations using the Spotify API.

## Features

- Find direct collaborations between artists
- Discover paths between artists through mutual collaborations
- Caching system for improved performance
- Detailed collaboration information including tracks and albums

## Setup

1. Clone the repository

```bash
git clone https://github.com/mattcole19/artist-connections.git
cd artist-connections
```

2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install uv
uv pip install -r requirements.txt
```

4. Set up Spotify API credentials
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new application
   - Copy the Client ID and Client Secret
   - Create a `.env` file in the project root with:
     - SPOTIFY_CLIENT_ID=your_client_id
     - SPOTIFY_CLIENT_SECRET=your_client_secret

## CLI Usage

The project provides a command-line interface with the following commands:

### Find Path Between Artists

```bash
python cli.py path
```

This will prompt you to enter two artist names and will find the shortest connection between them through collaborations.

### Show Artist Collaborations

```bash
python cli.py collabs "Artist Name"
```

Shows all collaborations for the specified artist, grouped by collaborator with song and album details.

### Help

```bash
python cli.py --help
```

Shows available commands and their usage.
