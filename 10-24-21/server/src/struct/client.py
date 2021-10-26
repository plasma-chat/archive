# Copyright 2021 iiPython

# Modules
import os
import time
import random
import string
import socket
from typing import Tuple
from datetime import datetime
from ..core.config import config
from ..core.socket import SocketWrapper

# Configuration
_CONTENT_LIMIT = config.get("limits")["content"]
_PACKET_LIMIT  = int(config.get("limits")["packet"] * 1000) if "packet" in config.get("limits") else None  # in Kilobytes
_FILE_DIR      = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "files")

# Clear up files
for file in os.listdir(_FILE_DIR):
    os.remove(os.path.join(_FILE_DIR, file))

# Client class
class Client(object):
    def __init__(self, server, data: tuple = Tuple[Tuple[str, int], socket.socket]) -> None:
        self.srv = server
        self.conn, self.addr = data
        self.sock = SocketWrapper(self.conn, self.srv)

        # Attributes
        self.authed   =   False
        self.attr     =   {
            "uid": None,  # User ID
            "name": None  # Username
        }

    def shutdown(self) -> None:
        self.attr = {}
        self.authed = False

        self.sock.close()
        try:
            self.srv.clients.remove(self)

        except ValueError:
            pass

    def to_dict(self) -> dict:
        return self.attr

    def pack_json(self, **kwargs) -> dict:
        return {
            "type": kwargs.get("type", "m.msg"),
            "data": {
                "author": kwargs.get("author", {"uid": "system:plasma", "name": "System"}),
                "content": kwargs["content"],
                "timestamp": time.time()
            },
            "guild": self.srv.to_dict() | {"packet_limit": _PACKET_LIMIT}
        }

    def send(self, **kwargs) -> None:
        return self.sock.send_json(self.pack_json(**kwargs))

    def print(self, *args, **kwargs) -> None:
        return self.srv.console.print(*args, **kwargs)

    def handle(self) -> None:
        while True:
            try:
                data = self.sock.recv_json(limit = _PACKET_LIMIT)
                if data is None:
                    return self.shutdown()

            except OverflowError as err:
                self.print(f"[red]Ignored data from {self.attr['uid']} - got {int(float(str(err)))}b; limit is {_PACKET_LIMIT}b")
                self.send(type = "e.overflow", content = f"Packet limit is {_PACKET_LIMIT} bytes!")
                continue

            # Check data
            try:
                dtype, data = data["type"], (data["data"] if "data" in data else {})
                if not isinstance(data, dict):
                    raise ValueError

                elif "." not in dtype:
                    raise ValueError

                elif dtype.count(".") > 1:
                    raise ValueError

                type_base = dtype.split(".")[0]
                if not type_base.strip():
                    raise ValueError

                dtype = dtype.split(".")[1]

            except Exception:
                self.send(type = "e.parse", content = "Invalid type/data or field(s) missing.")
                continue

            # Handle action(s)
            if type_base == "u":
                if dtype == "connect":
                    if self.authed:
                        self.send(type = "e.unexpected", content = "Client is already authenticated.")
                        continue

                    # Check data
                    uid, name = data.get("id", ""), data.get("name", "")
                    if not (
                        uid.strip() and name.strip() and  # Check fields exist
                        uid.count(":") == 1 and uid.split(":")[0].strip() and uid.split(":")[1].strip() and uid.lower() == uid and  # Validate UID
                        " " not in name and " " not in uid and  # Check for illegal spaces
                        uid.split(":")[0] == name.lower()  # Check UID name
                    ) or not (
                        len(name) <= 16 and  # Check name length
                        ":" not in name  # Check illegal : in name
                    ):
                        self.send(type = "e.parse", content = "Invalid UID/name or field(s) missing.")
                        continue

                    # Attributes
                    self.attr = {"uid": uid, "name": name}
                    self.authed = True

                    # Welcome message
                    now = datetime.utcnow().strftime("%H:%M")
                    self.send(content = f"[cyan]Welcome to {config.get('name')}! [lred]{now} UTC[reset]")
                    self.srv.broadcast(self.pack_json(
                        content = f"[lgreen]{self.attr['name']} ({self.attr['uid'].split(':')[1]})[/lgreen] has [green]joined[/green] the server.",
                        type = "u.join"
                    ))

                elif dtype == "leave":
                    self.srv.broadcast(self.pack_json(
                        content = f"[lgreen]{self.attr['name']} ({self.attr['uid'].split(':')[1]})[/lgreen] has [red]left[/red] the server.",
                        type = "u.leave"
                    ))
                    break

            # Authenticated action(s)
            elif self.authed:
                if type_base == "m":
                    if dtype == "msg":
                        try:
                            message = str(data["content"]).strip("\b\r")
                            if not message.strip():
                                raise ValueError

                            elif len(message) > _CONTENT_LIMIT:
                                raise OverflowError

                            self.srv.broadcast(self.pack_json(author = self.to_dict(), content = message))
                            continue

                        except Exception as err:
                            except_map = {
                                ValueError: {"type": "e.missing", "content": "Message missing."},
                                OverflowError: {"type": "e.overflow", "content": f"Message limit is {_CONTENT_LIMIT} char(s)."}
                            }
                            if type(err) in except_map:
                                self.send(**except_map[type(err)])
                                continue

                            self.send(type = "e.server", content = "Server error has occured, try your request again later.")
                            raise err

                    elif dtype == "bin":
                        try:
                            message, fileid = bytes.fromhex(data["content"]), "".join(random.choice(string.ascii_letters) for _ in range(8))
                            if "/" in data["name"] or "\\" in data["name"]:
                                raise ValueError

                            filepath = os.path.join(_FILE_DIR, fileid + "_" + data["name"])
                            with open(filepath, "wb") as file:
                                file.write(message)

                            self.srv.broadcast(self.pack_json(author = self.to_dict(), content = {"name": data["name"], "id": fileid}, type = "m.bin"))
                            continue

                        except Exception as err:
                            except_map = {
                                IndexError: {"type": "e.missing", "content": "Content or filename is missing."},
                                ValueError: {"type": "e.invalid", "content": "Provided filename is invalid."}
                            }
                            if type(err) in except_map:
                                self.send(**except_map[type(err)])
                                continue

                            self.send(type = "e.server", content = "Server error has occured, try your request again later.")
                            raise err

                elif type_base == "d":
                    if dtype == "down":
                        try:
                            fileid = data["id"]
                            try:
                                filename = [_ for _ in os.listdir(_FILE_DIR) if _.split("_")[0] == fileid][0]

                            except IndexError:
                                self.send(type = "d.invalid_id", content = "File ID is invalid.")
                                continue

                            with open(os.path.join(_FILE_DIR, filename), "rb") as file:
                                self.send(type = "d.content", content = {"data": file.read().hex(), "name": "_".join(filename.split("_")[1:])})

                        except IndexError:
                            self.send(type = "e.missing", content = "File ID is missing.")
                            continue

        # Shutdown client
        self.shutdown()
