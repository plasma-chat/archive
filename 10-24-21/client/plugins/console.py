# Copyright 2021 iiPython
# Console control plugin

# Embeds class
class Console(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "con"

        self.cmap = {
            "help": lambda a: self.loader.print(", ".join([cmd for cmd in self.cmap])),
            "clear": self.clear,
            "rainbow": self.rainbow
        }

        # Metadata
        self.name = "Console Manager"
        self.author = "iiPython"

    def clear(self, args: list) -> None:
        """Clears the console and redraws the chat prompt"""
        return self.loader.clear()

    def rainbow(self, args: list) -> None:
        """Creates rainbow text given an argument"""
        if not args:
            return self.loader.print("[red]No text specified (make sure you use quotes).")

        text, new, idx = args[0], "", 0
        colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
        for char in text:
            if idx > (len(colors) - 1):
                idx = 0

            new += f"[{colors[idx]}]{char}[reset]"
            idx += 1

        return new

    def on_fire(self, args: list) -> None:
        """Handle commands for the plugin"""
        if not args:
            return self.loader.print("[red]No command specified.[reset]")

        command, args = args[0], args[1:]
        if command in self.cmap:
            return self.cmap[command](args)

        else:
            return self.loader.print(f"[red]Unknown command: '{command}'.[reset]")
