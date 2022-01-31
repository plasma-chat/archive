# Copyright 2021 iiPython

# Modules
import os
import json
from threading import Thread
from datetime import datetime

from .console import Console
from .core.emoji.core import em
from .core.config import config
from .struct.client import Client
from .core.socket import Socket, SocketWrapper

# Server class
class Server(object):
    def __init__(self) -> None:
        self.sock = Socket()
        self.wrap = SocketWrapper(self.sock)

        self.clients = []
        self.console = Console()

    def to_dict(self) -> dict:
        return {
            "name": config.get("name"),
            "users": [client.to_dict() for client in self.clients if client.authed]
        }

    def close(self) -> None:

        # Shutdown clients
        for client in self.clients:
            client.shutdown()

        # Exit server
        self.console.print("\r[red]^C | Server shutdown successfully.")
        os._exit(0)  # Kills off our threads

    def start(self, addr: tuple, name: str) -> None:
        self.name = name
        self.addr = addr

        # Connect socket
        self.sock.bind(("0.0.0.0", 2075))
        self.sock.listen(5)

        # Start text
        self.console.clear()
        self.console.print("[blue]Server running on [yellow]0.0.0.0:2075[blue]..")

        # Client handler
        while True:
            try:
                conn, addr = self.sock.accept()
                client = Client(self, (conn, addr))

                # Handle thread
                self.clients.append(client)
                Thread(target = client.handle).start()

            except KeyboardInterrupt:
                return self.close()

    def broadcast(self, data: dict) -> None:
        data = json.loads(em(json.dumps(data)))
        for client in self.clients:
            try:
                client.sock.send_json(data)

            except OSError:
                self.clients.remove(client)

        # Print to server
        ts = datetime.now().strftime("%H:%M")
        if data["type"] in ["m.msg", "u.join", "u.leave"]:
            internal_dt = data["data"]
            lines = internal_dt["content"].split("\n")
            def generate_prefix() -> str:  # noqa
                return f"[cyan]{ts} [lgreen]{internal_dt['author']['name']}[reset] "

            self.console.print(f"{generate_prefix()}[lblack]| [reset]{lines[0]}[reset]")
            for line in lines[1:]:
                self.console.print(f"{' ' * len(self.console.print(generate_prefix(), color = False))}[lblack]| [reset]{line}[reset]")

# Initialization
server = Server()
