import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "target_account": "沈理电协",
    "output_dir": "articles",
    "download_videos": True,
    "max_articles": 0,
    "headless": False,
    "login_timeout_ms": 180000,
}


class Config:
    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._data.update(json.load(f))

    def get(self, key, default=None):
        return self._data.get(key, default)

    @property
    def target_account(self):
        return self._data["target_account"]

    @property
    def output_dir(self):
        return self._data["output_dir"]

    @property
    def download_videos(self):
        return self._data["download_videos"]

    @property
    def max_articles(self):
        return self._data["max_articles"]

    @property
    def headless(self):
        return self._data["headless"]

    @property
    def login_timeout_ms(self):
        return self._data["login_timeout_ms"]
