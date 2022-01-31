# Copyright 2021 iiPython

# Modules
import time
import socket
from .config import Config
from .net.parse import parse
from .console import Console
from iikp import readchar, keys
from .plugins import PluginManager

# Initalization
con, config, plugins = Console(), Config(), PluginManager()
message_input = ""

# Load custom colors
custom_colors, def_colors = config.get("colors") or {}, {
    "user": "lgreen",
    "time": "cyan",
    "prompt": "yellow"
}
for default in def_colors:
    if default not in custom_colors:
        custom_colors[default] = def_colors[default]

def generate_prompt() -> str:
    return con.print(f"[{custom_colors['prompt']}]> [reset]", print_out = False) +\
        message_input +\
        con.print(f"[{custom_colors['prompt']}]_[reset]", print_out = False)

# Send loop
class SendLoop(object):
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock

    def loop(self) -> None:
        global message_input
        _old_len = 0
        while True:
            try:
                _len = len(message_input)
                if _len >= (len(con._ts) - 2):
                    message_input, _len = message_input[:-1], _len - 1

                if _len > _old_len:
                    print("\r" + generate_prompt(), end = "")

                else:
                    print(f"\r{con._ts}\r{generate_prompt()}\r", end = "")

                _old_len = _len

                # Handle keypresses
                key = readchar()
                if key == keys.ENTER and message_input.strip():
                    message_input = plugins.on_send(message_input)
                    if message_input is None:
                        message_input = ""
                        continue

                    self.sock.send_json({
                        "type": "m.msg",
                        "data": {"content": message_input, "ts": time.time()}
                    })
                    message_input = ""

                elif key == keys.BACKSPACE and message_input:
                    message_input = message_input[:-1]

                elif key == keys.CTRL_C:
                    break

                elif isinstance(key, str) or key == keys.SPACE:
                    message_input += (key if key != keys.SPACE else " ")

            except Exception as error:
                return con.traceback(error)

# Receive loop
class ReceiveLoop(object):
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock

        # Plugin manager needs print
        for attr in ["print", "clear", "sock"]:
            setattr(plugins, attr, getattr(self, attr))

        plugins.load_plugins()

    def clear(self) -> None:
        con.clear()
        con.print(generate_prompt() + "\r", end = "")

    def print(self, *args) -> None:
        con.print(f"\r{con._ts}\r", end = "")
        con.print(" ".join([str(a) for a in args]), end = "")
        con.print(f"\n\r{generate_prompt()}\r", end = "")

    def loop(self) -> None:
        global message_input
        while True:
            try:
                messages = self.sock.recv_json()
                for message in messages:
                    data = parse(message)

                    # Handle data
                    ts = data.timestamp
                    def generate_prefix() -> str:  # noqa
                        return f"[{custom_colors['time']}]{ts} [{custom_colors['user']}]{plugins.get_name_prefix(data.author)}{data.author.name}[reset] "

                    def print_lines(lines: str) -> None:
                        self.print(f"{generate_prefix()}[lblack]| [reset]{lines[0]}[reset]")
                        for line in lines[1:]:
                            self.print(f"{' ' * len(con.print(generate_prefix(), color = False))}[lblack]| [reset]{line}[reset]")

                    if data.type in ["m.msg", "m.bin", "u.join", "u.leave"]:
                        if data.type == "m.bin":
                            plugins.plugins["file"].filemeta[data.content["id"]] = data.content["name"]
                            print_lines([data.content["name"], f"use '/file down {data.content['id']}' to download"])
                            continue

                        print_lines(plugins.on_recv(data).split("\n"))

                    elif data.type in ["d.content", "d.invalid_id"]:
                        plugins.plugins["file"].handle_resp(data)

            except Exception as error:
                return con.traceback(error)
