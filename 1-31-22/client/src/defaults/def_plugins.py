# Copyright 2021 iiPython
# Plasma Built-in Plugins

# Modules
import os
import shutil
import textwrap

# Plugin Manager
class PluginManager_(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "plugins"

        self.print = loader.print
        self.plugin_dir = loader.plugin_dir
        self.cmap = {
            "help": self.help,
            "reload": self.reload,
            "list": self.list
        }

        # Metadata
        self.name = "Plasma Plugin Manager"
        self.author = "iiPython"

    def help(self, args: list) -> None:
        self.print("[yellow]Plasma Plugin Manager v1.1")
        self.print("  [blue]help                  [lblack]| Shows this message")
        self.print("  [blue]list                  [lblack]| Lists all plugins")
        self.print("  [blue]list names            [lblack]| Lists all plugin names")
        self.print("  [blue]list authors          [lblack]| Lists all plugin authors")
        self.print("  [blue]list author <author>  [lblack]| Lists all plugins by an author")
        self.print("  [blue]reload                [lblack]| Reloads all plugins")
        self.print("  [blue]reload <id>           [lblack]| Reloads a plugin by its ID")

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
        if args:
            opt = args[0]
            if opt == "names":
                text = "[blue]" + "\n".join(textwrap.wrap(
                    ", ".join(sorted(p.name for _, p in self.loader.plugins.items())),
                    width = shutil.get_terminal_size().columns - 10
                ))
                self.print("[yellow]Listing plugins ([cyan]by name[yellow]):")
                return self.print(text.replace(",", "[white],[blue]"))

            elif opt == "authors":
                text = "[blue]" + "\n".join(textwrap.wrap(
                    ", ".join(author for author in sorted(list(set([p.author for _, p in self.loader.plugins.items() if p.author != "Unknown"])))),
                    width = shutil.get_terminal_size().columns - 10
                ))
                self.print("[yellow]Listing plugin authors ([cyan]by name[yellow]):")
                return self.print(text.replace(",", "[white],[blue]"))

            elif opt == "author":
                if not args[1:]:
                    return self.print("[red]No author provided to lookup.")

                text = "[blue]" + "\n".join(textwrap.wrap(
                    ", ".join([plugin.name for plugin in [p for _, p in self.loader.plugins.items() if p.author.lower() == args[1].lower()]]),
                    width = shutil.get_terminal_size().columns - 10
                ))
                self.print(f"[yellow]Listing plugins ([cyan]made by {args[1].lower()}[yellow]):")
                return self.print(text.replace(",", "[white],[blue]"))

            else:
                return self.print(f"[red]Plugin List: no known option [yellow]'{opt}'[reset]")

        # Sort plugins by author
        plugindata = {}
        for _, plugin in self.loader.plugins.items():
            plugindata[plugin.author] = [plugin] + plugindata.get(plugin.author, [])

        # Print out plugins
        for author, plugins in plugindata.items():
            self.print(f"[yellow]{author}:")
            for plugin in plugins:
                self.print(f"  [blue]- {plugin.name}")

    def on_fire(self, args: list) -> None:
        if not args:
            return self.loader.print("[red]No command specified.[reset]")

        command, args = args[0], args[1:]
        if command in self.cmap:
            return self.cmap[command](args)

        else:
            return self.loader.print(f"[red]Unknown command: '{command}'.[reset]")

# File manager
class FileManager(object):
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
