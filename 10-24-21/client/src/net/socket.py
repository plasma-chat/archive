# Copyright 2021 iiPython

# Modules
import json
import socket
from ..console import Console

# Socket class
class Socket(socket.socket):
    def __init__(self, console: Console, username: str, is_bot: bool = False) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self._FAILED_MSG = "[red]Failed to send packet to server.\n" +\
            "[yellow]Please check that the server is online, and that your internet is stable.\n\n" +\
            "[lblack]Try reconnecting later.[reset]"

        # Attributes
        self.username = username
        self.is_bot = is_bot

        self.console = console

    def identify(self) -> None:
        self.send_json({
            "type": "u.connect",
            "data": {
                "id": f"{self.username.lower()}:plasma",
                "name": self.username
            }
        })

    def send_json(self, data: dict) -> None:
        data = json.dumps(data).encode("utf8")
        try:
            self.sendall(data)

        except OSError:

            # Disconnected
            self.console.exit(1, self._FAILED_MSG)

    def recv_json(self) -> list:
        data = b""
        while True:
            try:
                data += self.recv(2048)
                if not data:
                    return []

                try:
                    data = [json.loads(_) for _ in data.decode("utf8").split("\0x55") if _.strip()]
                    break

                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            except OSError:
                self.console.exit(1, self._FAILED_MSG)

        return data
