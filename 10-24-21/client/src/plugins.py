# Copyright 2021 iiPython

# Modules
import os
import shutil
import string
import random
import inspect
import importlib.util
from .config import Config

# Exceptions
class PluginError(Exception):
    pass

# Built-in plugins
class PluginManager_(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "plugins"

        self.print = loader.print
        self.plugin_dir = loader.plugin_dir
        self.cmap = {
            "help": lambda a: self.loader.print(", ".join([cmd for cmd in self.cmap])),
            "reload": self.reload,
            "list": self.list
        }

        # Metadata
        self.name = "Plasma Plugin Manager"
        self.author = "iiPython"

    def reload(self, args: list) -> None:
        if not args:
            self.loader.load_plugins()
            return self.print(f"[green]Reloaded {len(self.loader.plugins) - 2} plugin(s)")

        failed = 0
        for plugin in args:
            path = os.path.join(self.plugin_dir, plugin + (".py" if not plugin.endswith(".py") else ""))
            if os.path.isfile(path):
                self.loader.load_module(path)

            else:
                failed += 1

        if failed:
            return self.print(f"[red]Failed to reload {failed} plugin(s), [green]{len(args) - failed} were reloaded.[reset]")

        return self.print(f"[green]Reloaded {len(args) - failed} plugin(s)")

    def list(self, args: list) -> None:
        for plugin in self.loader.plugins:
            plugin = self.loader.plugins[plugin]
            name = plugin.name if hasattr(plugin, "name") else plugin.plugin_id
            author = plugin.author if hasattr(plugin, "author") else "Unknown"
            self.print(f"- {name} (by {author})")

    def on_fire(self, args: list) -> None:
        if not args:
            return self.loader.print("[red]No command specified.[reset]")

        command, args = args[0], args[1:]
        if command in self.cmap:
            return self.cmap[command](args)

        else:
            return self.loader.print(f"[red]Unknown command: '{command}'.[reset]")

class FileMananger(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "file"

        self.print = loader.print
        self.cmap = {"help": self.help, "up": self.upload, "down": self.download, "workdir": self.workdir}

        # Storage
        self.packsize = None
        self.awaiting = False
        self.filemeta = {}
        self.workdir  = os.path.abspath("./")

        # Metadata
        self.name = "Plasma File Manager"
        self.author = "iiPython"

    def scale(self, num: int, suffix: str = "B") -> str:
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"

            num /= 1024.0

        return f"{num:.1f}Yi{suffix}"

    def workdir(self, args: list) -> None:
        if not args:
            return self.print(f"[yellow]Current working directory:\n{self.workdir}")

        path = args[0]
        if not os.path.isdir(path):
            return self.print("[red]Invalid directory specified.")

        self.workdir = path
        return self.print("[green]Working dir changed.")

    def upload(self, args: list) -> None:
        if not args:
            return self.print("[red]No filename specified to upload.")

        elif self.packsize is None:
            return self.print("[red]No packet size is known, wait until a message is received.")

        fn = os.path.join(self.workdir, args[0])
        if not os.path.isfile(fn):
            return self.print("[red]No such file exists.")

        size = os.path.getsize(fn)
        if size + 60 > self.packsize:
            return self.print(f"[red]File too large, packet limit: {self.scale(self.packsize)}")

        fn = fn.replace("\\", "/")
        with open(fn, "rb") as file:
            data = file.read()

        packet = {"type": "m.bin", "data": {"content": data.hex(), "name": fn.split("/")[-1]}}
        if len(packet) > self.packsize:

            # Failsafe incase hex is larger than bytes
            return self.print(f"[red]File too large, packet limit: {self.scale(self.packsize)}")

        # Send packet
        self.loader.sock.send_json(packet)

    def download(self, args: list) -> None:
        if not args:
            return self.print("[red]No file ID provided to download.")

        elif len(args[0]) != 8:
            return self.print("[red]Invalid file ID.")

        elif args[0] in self.filemeta and os.path.isfile(self.filemeta[args[0]]):
            return self.print(f"[red]'{self.filemeta[args[0]]}' already exists locally.")

        self.loader.sock.send_json({"type": "d.down", "data": {"id": args[0]}})
        self.awaiting = True

    def help(self, args: list) -> None:
        cmds = ["up <file>", "down <id>", "workdir [dir]"]
        self.print("[yellow]Plasma File Manager[reset]\nCommands:\n" + "\n".join(["  " + f for f in cmds]))

    def handle_resp(self, data) -> None:
        if not self.awaiting:
            return

        elif data.type == "d.invalid_id":
            self.print("[red]No file has that ID.")

        elif data.type == "d.content":
            fn, data = data.content["name"], data.content["data"]
            if os.path.isfile(os.path.join(self.workdir, fn)):
                self.print(f"[red]'{fn}' already exists locally.")

            else:
                with open(os.path.join(self.workdir, fn), "wb") as file:
                    file.write(bytes.fromhex(data))

                self.print(f"[green]'{fn}' downloaded successfully!")

        self.awaiting = False

    def on_recv(self, ctx) -> None:
        self.packsize = ctx.guild.packet_limit

    def on_fire(self, args: list) -> None:
        if not args:
            return self.loader.print("[red]No command specified.[reset]")

        command, args = args[0], args[1:]
        if command in self.cmap:
            return self.cmap[command](args)

        else:
            return self.loader.print(f"[red]Unknown command: '{command}'.[reset]")

# Plugin manager
config = Config()
class PluginManager(object):
    def __init__(self) -> None:
        self.sock = None
        self.plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")

    def def_plugins(self) -> None:
        self.plugins = {"plugins": PluginManager_(self), "file": FileMananger(self)}

    def on_recv(self, ctx) -> str:
        new = ctx.content
        for plugin in self.plugins:
            plugin = self.plugins[plugin]
            if hasattr(plugin, "on_recv"):
                res = plugin.on_recv(ctx)
                if res is not None:
                    new = res

        return new

    def on_send(self, message: str) -> str:
        if message[0] == "/":
            pid = message[1:].split(" ")[0]
            if pid not in self.plugins:
                return message

            plugin = self.plugins[pid]
            if hasattr(plugin, "on_fire"):
                return plugin.on_fire(self.format_args(" ".join(message.split(" ")[1:])))

            return message

        new = message
        for plugin in self.plugins:
            plugin = self.plugins[plugin]
            if hasattr(plugin, "on_send"):
                res = plugin.on_send(new)
                if res is not None:
                    new = res

        return new

    def generate_uid(self) -> str:
        return "".join(random.choice(string.ascii_letters) for _ in range(12))

    def format_args(self, message: str) -> list:
        args, data = [], {"quote": False, "temp": ""}
        for char in message:
            if char == "\"" and data["quote"]:
                args.append(data["temp"])
                data["temp"] = ""
                data["quote"] = False

            elif char == "\"" and not data["quote"]:
                data["quote"] = True

            elif not data["quote"] and char == " ":
                args.append(data["temp"])
                data["temp"] = ""

            else:
                data["temp"] += char

        return [a for a in args + [data["temp"]] if a.strip()]

    def load_plugin(self, plugin) -> None:
        plugin_id = plugin.plugin_id
        if plugin_id in self.plugins:
            raise PluginError(f"plugin {plugin_id} is already registered")

        self.plugins[plugin_id] = plugin
        if config.debug:
            self.print(f"[yellow]Loaded {plugin_id} from [green]{plugin}[reset]")

    def load_module(self, path: str) -> None:
        uid = self.generate_uid()
        temp_path = os.path.join(self.plugin_dir, uid + ".py")
        shutil.copyfile(path, temp_path)

        # Load module
        spec = importlib.util.spec_from_file_location(f"plugins.{uid}", temp_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        os.remove(temp_path)  # Deletes the copied module

        # Load plugin class
        plugin = None
        for _, class_ in inspect.getmembers(mod, inspect.isclass):
            try:
                plugin = class_(loader = self)
                break

            except Exception:
                pass

        if plugin is not None:
            self.load_plugin(plugin)

    def load_plugins(self) -> None:
        self.def_plugins()
        for file in os.listdir(self.plugin_dir):
            path = os.path.join(self.plugin_dir, file)
            if file[0] == "_" or not file.endswith(".py"):
                continue

            # Load module
            self.load_module(path)
