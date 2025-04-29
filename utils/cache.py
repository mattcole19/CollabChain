from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Optional, Any
import hashlib


class Cache:
    def __init__(self, cache_dir: str, ttl_hours: Optional[int] = None):
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours) if ttl_hours else None
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get(self, key: str) -> Optional[Any]:
        cache_path = self.get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with cache_path.open("r") as f:
                cached_data = json.load(f)

                if self.ttl:
                    cached_time = datetime.fromtimestamp(cached_data["timestamp"])

                    if datetime.now() - cached_time > self.ttl:
                        print(f"Cache expired for {key}")
                        return None

                return cached_data["data"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, data: Any) -> None:
        cache_path = self.get_cache_path(key)
        cache_data = {"timestamp": datetime.now().timestamp(), "data": data}

        try:
            with cache_path.open("w") as f:
                json.dump(cache_data, f)
        except OSError as e:
            print(f"Failed to write cache: {e}")

    def generate_cache_key(self, key: str) -> str:
        return hashlib.md5(key.encode("utf-8")).hexdigest() + ".json"

    def get_cache_path(self, key: str) -> Path:
        return self.cache_dir / self.generate_cache_key(key)
