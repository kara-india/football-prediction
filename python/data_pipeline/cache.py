import time
import json
import os
from typing import Any, Optional

class DataCache:
    def __init__(self, disk_path: str = None):
        self._memory_cache = {}
        self._disk_path = disk_path
        if self._disk_path and os.path.exists(self._disk_path):
            try:
                with open(self._disk_path, 'r') as f:
                    self._memory_cache = json.load(f)
            except Exception:
                pass
                
    def _save_to_disk(self):
        if self._disk_path:
            with open(self._disk_path, 'w') as f:
                json.dump(self._memory_cache, f)

    def get(self, key: str) -> Optional[Any]:
        if key in self._memory_cache:
            item = self._memory_cache[key]
            if item['expiry'] > time.time():
                return item['value']
            else:
                del self._memory_cache[key]
                self._save_to_disk()
        return None

    def set(self, key: str, value: Any, ttl_seconds: int):
        self._memory_cache[key] = {
            'value': value,
            'expiry': time.time() + ttl_seconds
        }
        self._save_to_disk()

    def invalidate(self, key: str):
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._save_to_disk()

    def invalidate_prefix(self, prefix: str):
        keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._memory_cache[k]
        if keys_to_delete:
            self._save_to_disk()
