# Copyright 2021 iiPython

# Modules
import json
import socket
from iipython import Hellman

from ..config import Config
from ..console import Console

# Initialization
FAILED_MSG = "[red]Plasma - Connection Error\n\n" +\
    "[yellow]Check the server you're connecting to.\nIs it online? Is it public?\n\n" +\
    "[lblack]Keep experiencing this? Check your network, or submit a bug report.[reset]"

# Socket class
config = Config()
class Socket(socket.socket):
    def __init__(self, console: Console, username: str, is_bot: bool = False) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.console = console

        # Attributes
        self.username = username
        self.is_bot = is_bot

        # Hellman (SSL)
        self.hellman = None

    def handshake(self) -> None:
        try:
            data = self.recv_json()[0]["data"]
            self.hellman = Hellman(data["base"], data["modu"])
            self.send_json({"type": "s.handshake", "data": {"pub": self.hellman.pub_key}}, encrypt = False)
            self.hellman.generate_shared(data["pub"])
            if config.debug:
                self.console.print("[yellow][SSL]: DO NOT SHARE THE KEYS BELOW THIS MESSAGE!")
                self.console.print(f"[yellow][SSL]: pub_key: {self.hellman.pub_key}; mod: {self.hellman.modu}; base: {self.hellman.base}")
                self.console.print(f"[yellow][SSL]: shared_key: {self.hellman.shared_key}; priv_key: {self.hellman.priv_key}")

        except Exception:
            raise self.HandshakeError

    def connect_wrap(self, *args, **kwargs) -> None:
        try:
            self.connect(*args, **kwargs)

        except OSError:
            return self.console.exit(1, FAILED_MSG)

    def identify(self) -> None:
        self.send_json({
            "type": "u.connect",
            "data": {
                "id": f"{self.username.lower()}:plasma",
                "name": self.username
            }
        })

    def send_json(self, data: dict, encrypt: bool = True) -> None:
        try:
            data = json.dumps(data)
            if self.hellman is not None and encrypt:
                data = self.hellman.encrypt(data)

            else:
                data = data.encode("utf8")

            self.sendall(data)

        except OSError:
            return self.console.exit(1, FAILED_MSG)

    def recv_json(self) -> list:
        data = b""
        while True:
            try:
                data += self.recv(2048)
                try:
                    if self.hellman is not None:
                        data = [json.loads(self.hellman.decrypt(_)) for _ in data.split(b"\0x55") if _.strip()]
                        break

                    data = [json.loads(_) for _ in data.decode("utf8").split("\0x55") if _.strip()]
                    break

                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            except OSError:
                self.console.exit(1, self._FAILED_MSG)

        return data

    # Handshaking Error
    class HandshakeError(Exception):
        pass
