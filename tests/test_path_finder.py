import pytest

from services.path_finder import PathFinder


def test_direct_path(mock_spotify):
    """Test finding a direct path between two artists who have collaborated"""
    path_finder = PathFinder(mock_spotify)

    path = path_finder.find_path("Alpha", "Beta")
    print(path)

    assert path is not None
    assert len(path.path) == 2
    assert path.path[0].artist.name == "Alpha"
    assert path.path[1].artist.name == "Beta"
    assert path.path[1].connecting_song == "Song One"


def test_two_hop_path(mock_spotify):
    """Test finding a path between two artists through an intermediary"""
    path_finder = PathFinder(mock_spotify)

    path = path_finder.find_path("Alpha", "Delta")

    assert path is not None
    assert len(path.path) == 3
    assert path.path[0].artist.name == "Alpha"
    assert path.path[1].artist.name == "Gamma"
    assert path.path[2].artist.name == "Delta"
    assert path.path[1].connecting_song == "Song Two"
    assert path.path[2].connecting_song == "Song Four"


def test_no_path_found(mock_spotify):
    """Test when no path exists between artists"""
    path_finder = PathFinder(mock_spotify)

    # Try to find path to an artist with no connections
    path = path_finder.find_path("Epsilon", "Alpha")
    assert path is None


def test_artist_not_found(mock_spotify):
    """Test when one or both artists are not found"""
    path_finder = PathFinder(mock_spotify)

    # Mock artist not found
    mock_spotify.get_artist_by_name.return_value = None

    path = path_finder.find_path("Nonexistent Artist", "Alpha")
    assert path is None


def test_max_depth_limit(mock_spotify):
    """Test that the path finder respects the max_depth parameter"""
    path_finder = PathFinder(mock_spotify)

    # Set max_depth to 1 to only allow direct collaborations
    path = path_finder.find_path("Alpha", "Epsilon", max_depth=1)
    assert path is None  # Should not find the 2-hop path


@pytest.mark.parametrize(
    "start,end,expected_length",
    [
        ("Alpha", "Beta", 2),  # Direct collaboration
        ("Alpha", "Delta", 3),  # Two-hop path
        ("Beta", "Delta", 3),  # Different two-hop path
    ],
)
def test_path_lengths(mock_spotify, start, end, expected_length):
    """Test various path lengths between different artists"""
    path_finder = PathFinder(mock_spotify)

    path = path_finder.find_path(start, end)
    assert path is not None
    assert len(path.path) == expected_length


# Add async versions of all tests
@pytest.mark.asyncio
async def test_direct_path_async(mock_spotify):
    """Test finding a direct path between two artists who have collaborated (async)"""
    path_finder = PathFinder(mock_spotify)

    path = await path_finder.find_path_async("Alpha", "Beta")

    assert path is not None
    assert len(path.path) == 2
    assert path.path[0].artist.name == "Alpha"
    assert path.path[1].artist.name == "Beta"
    assert path.path[1].connecting_song == "Song One"


@pytest.mark.asyncio
async def test_two_hop_path_async(mock_spotify):
    """Test finding a path between two artists through an intermediary (async)"""
    path_finder = PathFinder(mock_spotify)

    path = await path_finder.find_path_async("Alpha", "Delta")

    assert path is not None
    assert len(path.path) == 3
    assert path.path[0].artist.name == "Alpha"
    assert path.path[1].artist.name == "Gamma"
    assert path.path[2].artist.name == "Delta"
    assert path.path[1].connecting_song == "Song Two"
    assert path.path[2].connecting_song == "Song Four"


@pytest.mark.asyncio
async def test_no_path_found_async(mock_spotify):
    """Test when no path exists between artists (async)"""
    path_finder = PathFinder(mock_spotify)

    # Try to find path to an artist with no connections
    path = await path_finder.find_path_async("Epsilon", "Alpha")
    assert path is None


@pytest.mark.asyncio
async def test_artist_not_found_async(mock_spotify):
    """Test when one or both artists are not found (async)"""
    path_finder = PathFinder(mock_spotify)

    # Mock artist not found
    mock_spotify.get_artist_by_name_async.return_value = None

    path = await path_finder.find_path_async("Nonexistent Artist", "Alpha")
    assert path is None


@pytest.mark.asyncio
async def test_max_depth_limit_async(mock_spotify):
    """Test that the path finder respects the max_depth parameter (async)"""
    path_finder = PathFinder(mock_spotify)

    # Set max_depth to 1 to only allow direct collaborations
    path = await path_finder.find_path_async("Alpha", "Epsilon", max_depth=1)
    assert path is None  # Should not find the 2-hop path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start,end,expected_length",
    [
        ("Alpha", "Beta", 2),  # Direct collaboration
        ("Alpha", "Delta", 3),  # Two-hop path
        ("Beta", "Delta", 3),  # Different two-hop path
    ],
)
async def test_path_lengths_async(mock_spotify, start, end, expected_length):
    """Test various path lengths between different artists (async)"""
    path_finder = PathFinder(mock_spotify)

    path = await path_finder.find_path_async(start, end)
    assert path is not None
    assert len(path.path) == expected_length
