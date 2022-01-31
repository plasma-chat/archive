# Copyright 2021 iiPython

# Modules
import os
import shutil
import string
import random
import inspect
import importlib.util

from .config import Config
from .net.struct.user import User

# Built-in plugins
from .defaults.def_plugins import (
    FileManager, PluginManager_
)

# Exceptions
class PluginError(Exception):
    pass

# Plugin manager
config = Config()
class PluginManager(object):
    def __init__(self) -> None:
        self.sock = None
        self.last = None
        self.plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")

    def def_plugins(self) -> None:
        self.plugins = {"plugins": PluginManager_(self), "file": FileManager(self)}

    def on_recv(self, ctx) -> str:
        self.last = ctx

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

    def get_name_prefix(self, user: User) -> str:
        prefix = None
        for plugin in self.plugins:
            plugin = self.plugins[plugin]
            if hasattr(plugin, "get_name_prefix"):
                prefix = plugin.get_name_prefix(user)
                if prefix is not None:
                    break

        return prefix or ""

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

        plugin.name = getattr(plugin, "name", plugin.plugin_id)
        plugin.author = getattr(plugin, "author", "Unknown")

        self.plugins[plugin_id] = plugin
        if config.debug:
            self.print(f"[yellow][PLUGINS]: Loaded {plugin_id} from [green]{plugin}[reset]")

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
