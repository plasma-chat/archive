# Copyright 2021 iiPython

# Modules
import os
import json
from typing import Any

# Configuration
class Configuration(object):
    def __init__(self) -> None:
        self.config_path = os.path.join(
            os.path.dirname(__file__),
            "../../config.json"
        )
        self.config = {}
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r") as config:
                    self.config = json.loads(config.read())

            except Exception:
                pass

    def get(self, key: str) -> Any:
        if key in self.config:
            return self.config[key]

        return None

# Initialization
config = Configuration()
