# Copyright 2021 iiPython

# Modules
import os
import sys
import json
import socket
from typing import Any, Union
from src.console import Console

# Configuration class
class Config(object):
    def __init__(self) -> None:
        self.con = Console()
        self.config = {}

        self.debug = "--debug" in sys.argv

        # Load configuration
        self.config_file = os.path.join(
            os.path.dirname(__file__),
            "../config.json"
        )
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file, "r") as config:
                    self.config = json.loads(config.read())

            except Exception:
                pass

        # Check for changes
        self.manually_entered = False

    def get(self, key: str, ask: str = None, input_opts: dict = {}) -> Any:
        if key in self.config:
            return self.config[key]

        # Key isn't found
        if ask is None:
            return None

        self.manually_entered = True

        self.con.clear()
        self.con.print(ask)

        value = self.con.input(**input_opts)
        self.config[key] = value

        return value

    def save(self, ask: bool = False) -> None:
        if ask:
            self.con.clear()
            self.con.print("[cyan]Would you like to save these config options?")
            self.con.print("[yellow]  [E] - YES\n  [Q] - NO")

            # Handle keypresses
            if self.con.get_keys(["q", "e"]) == "q":
                return self.con.clear()

            self.con.clear()

        # Save JSON
        with open(self.config_file, "w") as config:
            config.write(json.dumps(self.config, indent = 4))

    def validate_ip(self, ip: str) -> Union[bool, tuple]:
        port = 2075
        if ip == ":":
            return ("localhost", 2075 if not ip[1:] else int(ip[1:]))

        elif ":" in ip:
            if ip.count(":") > 1:
                return False

            port_ = ip.split(":")[1].strip()
            if not port_:
                return False

            try:
                port = int(port_)
                if port > 65535 or port < 1:
                    raise ValueError

            except ValueError:
                return False

        return (socket.gethostbyname(ip.split(":")[0]), port)
