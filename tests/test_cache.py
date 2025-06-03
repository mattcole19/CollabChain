import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from utils.cache import Cache


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary directory for cache files"""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def cache(temp_cache_dir):
    """Create a cache instance with no TTL"""
    return Cache(temp_cache_dir)


@pytest.fixture
def ttl_cache(temp_cache_dir):
    """Create a cache instance with 1 hour TTL"""
    return Cache(temp_cache_dir, ttl_hours=1)


def test_cache_initialization(temp_cache_dir):
    """Test cache directory is created properly"""
    cache_dir = Path(temp_cache_dir) / "new_dir"
    Cache(str(cache_dir))
    assert cache_dir.exists()
    assert cache_dir.is_dir()


def test_cache_key_generation(cache):
    """Test cache key generation is consistent and correct"""
    test_key = "test_key"
    generated_key = cache.generate_cache_key(test_key)

    # Test key format
    assert generated_key.endswith(".json")

    # Test consistency
    assert cache.generate_cache_key(test_key) == generated_key

    # Test different keys generate different hashes
    assert cache.generate_cache_key("different_key") != generated_key


def test_cache_set_and_get(cache):
    """Test basic set and get operations"""
    test_data = {"test": "data"}
    cache.set("test_key", test_data)

    # Test retrieval
    retrieved_data = cache.get("test_key")
    assert retrieved_data == test_data

    # Test file exists with correct content
    cache_path = cache.get_cache_path("test_key")
    assert cache_path.exists()

    with cache_path.open("r") as f:
        stored_data = json.load(f)
        assert "timestamp" in stored_data
        assert stored_data["data"] == test_data


def test_cache_ttl(ttl_cache):
    """Test TTL functionality"""
    test_data = {"test": "data"}
    ttl_cache.set("test_key", test_data)

    # Should be available immediately
    assert ttl_cache.get("test_key") == test_data

    # Manually modify timestamp to simulate expired cache
    cache_path = ttl_cache.get_cache_path("test_key")
    with cache_path.open("r") as f:
        stored_data = json.load(f)

    # Set timestamp to 2 hours ago
    stored_data["timestamp"] = (datetime.now() - timedelta(hours=2)).timestamp()

    with cache_path.open("w") as f:
        json.dump(stored_data, f)

    # Should return None for expired data
    assert ttl_cache.get("test_key") is None


def test_cache_missing_key(cache):
    """Test behavior with non-existent keys"""
    assert cache.get("nonexistent_key") is None


def test_cache_invalid_json(cache, temp_cache_dir):
    """Test handling of corrupted cache files"""
    # Create invalid JSON file
    cache_path = cache.get_cache_path("test_key")
    with cache_path.open("w") as f:
        f.write("invalid json content")

    assert cache.get("test_key") is None


def test_cache_special_characters(cache):
    """Test handling of keys with special characters"""
    special_key = "test/key:with?special*characters"
    test_data = {"test": "data"}

    cache.set(special_key, test_data)
    assert cache.get(special_key) == test_data


def test_large_data(cache):
    """Test handling of large data structures"""
    large_data = {str(i): "x" * 1000 for i in range(1000)}
    cache.set("large_key", large_data)
    assert cache.get("large_key") == large_data


def test_concurrent_access(cache):
    """Test cache behavior with rapid sequential access"""
    for i in range(100):
        cache.set(f"key_{i}", {"value": i})

    for i in range(100):
        assert cache.get(f"key_{i}") == {"value": i}
