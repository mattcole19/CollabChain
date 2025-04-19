from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict


class Cache:
    def __init__(self, cache_dir: str, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get(self, key: str) -> Optional[Any]:
        cache_path = self.cache_dir / f"{key}.json"
        if not cache_path.exists():
            return None

        try:
            with cache_path.open("r") as f:
                cached_data = json.load(f)
                cached_time = datetime.fromtimestamp(cached_data["timestamp"])

                if datetime.now() - cached_time > self.ttl:
                    print(f"Cache expired for {key}")
                    return None
                # print(f"Cache hit for {key}")
                return cached_data["data"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, data: Any) -> None:
        cache_path = self.cache_dir / f"{key}.json"
        cache_data = {"timestamp": datetime.now().timestamp(), "data": data}

        try:
            with cache_path.open("w") as f:
                json.dump(cache_data, f)
        except OSError as e:
            print(f"Failed to write cache: {e}")
