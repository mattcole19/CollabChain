import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from services.spotify import SpotifyAPI
from services.path_finder import PathFinder
import asyncio


def init_spotify():
    """Initialize Spotify API client"""
    return SpotifyAPI()


def create_path_visualization(path):
    """Create a visual graph from the path"""
    G = nx.Graph()

    # Add nodes and edges from the path
    for i, (artist, song) in enumerate(path.path):
        G.add_node(artist.id, name=artist.name, popularity=artist.popularity)
        if i > 0:
            prev_artist = path.path[i - 1][0]
            G.add_edge(prev_artist.id, artist.id, song=song)

    # Create the visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(G)

    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color="lightblue",
        node_size=[G.nodes[node]["popularity"] * 30 for node in G.nodes],
        alpha=0.7,
    )

    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color="gray", alpha=0.5)

    # Add artist names as labels
    labels = {node: G.nodes[node]["name"] for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold")

    # Add song names as edge labels
    edge_labels = nx.get_edge_attributes(G, "song")
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

    plt.title("Artist Connection Path")
    plt.axis("off")
    return fig


async def find_path_async(artist1: str, artist2: str):
    """Async path finding for Streamlit"""
    spotify = SpotifyAPI()
    path_finder = PathFinder(spotify)

    async with spotify:
        return await path_finder.find_path_async(artist1, artist2)


def main():
    st.set_page_config(page_title="Artist Connections", page_icon="🎵", layout="wide")

    st.title("🎵 Artist Connections")
    st.write("Discover how artists are connected through their collaborations!")

    # Initialize session state for Spotify client
    if "spotify" not in st.session_state:
        st.session_state.spotify = init_spotify()

    # Create two columns for input
    col1, col2 = st.columns(2)

    with col1:
        artist1 = st.text_input("First Artist", placeholder="e.g., Taylor Swift")
    with col2:
        artist2 = st.text_input("Second Artist", placeholder="e.g., Drake")

    if st.button("Find Connection", type="primary"):
        if artist1 and artist2:
            with st.spinner(f"Finding connection between {artist1} and {artist2}..."):
                try:
                    # Use asyncio to run the async function
                    path = asyncio.run(find_path_async(artist1, artist2))

                    if path:
                        st.success("Found a connection! 🎉")

                        # Show the visualization
                        st.pyplot(create_path_visualization(path))

                        # Show detailed path
                        st.write("### Connection Details:")
                        for i, (artist, song) in enumerate(path.path):
                            if i == 0:
                                st.write(f"**{artist.name}**")
                            else:
                                st.write(f"↓ via '**{song}**'")
                                st.write(f"**{artist.name}**")

                        # Show additional artist info
                        st.write("### Artist Information:")
                        for artist, _ in path.path:
                            with st.expander(f"{artist.name}"):
                                st.write(f"**Genres:** {', '.join(artist.genres)}")
                                st.write(f"**Popularity:** {artist.popularity}/100")
                                st.write(f"**Spotify URI:** {artist.uri}")
                    else:
                        st.error("No connection found between these artists 😕")
                        st.write("Try different artists or check the spelling!")

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter both artist names! 🎤")

    # Add some helpful information at the bottom
    with st.expander("ℹ️ About"):
        st.write("""
        This app finds connections between artists through their collaborations using the Spotify API.
        - Direct collaborations (artists who have worked together)
        - Indirect connections (through other artists)
        - Visualization of the connection path
        """)


if __name__ == "__main__":
    main()
