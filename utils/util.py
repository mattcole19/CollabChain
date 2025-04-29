from datetime import datetime
from typing import Optional


def parse_spotify_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string from Spotify API into datetime.

    Spotify can return dates in different formats:
    - YYYY (e.g., "2024")
    - YYYY-MM (e.g., "2024-03")
    - YYYY-MM-DD (e.g., "2024-03-15")

    Args:
        date_str: Date string from Spotify API

    Returns:
        datetime object if parsing succeeds, None otherwise

    Examples:
        >>> parse_spotify_date("2024")
        datetime(2024, 1, 1, 0, 0)
        >>> parse_spotify_date("2024-03")
        datetime(2024, 3, 1, 0, 0)
        >>> parse_spotify_date("2024-03-15")
        datetime(2024, 3, 15, 0, 0)
        >>> parse_spotify_date("invalid") is None
        True
    """
    try:
        if len(date_str) == 4:  # YYYY
            return datetime.strptime(date_str, "%Y")
        elif len(date_str) == 7:  # YYYY-MM
            return datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) == 10:  # YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d")
        return None
    except ValueError:
        return None
