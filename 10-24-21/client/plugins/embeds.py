# Copyright 2021 iiPython
# Embed creation plugin

# Modules
from datetime import datetime

# Embeds class
class Embeds(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "em"

        dt = datetime.now()
        self.timezone = dt.astimezone().tzinfo.tzname(dt)

        # Metadata
        self.name = "Plasma Embed Creator"
        self.author = "iiPython"

    def now(self) -> str:
        return datetime.now().strftime("%I:%M %P").lstrip("0")

    def add_line(self, text: str, color: str = None) -> str:
        text = f" {text} "
        if len(text) > self.embed_size:
            text = text[:-((len(text) - self.embed_size) + 4)] + "..."
            dist = " " * (self.embed_size - len(text))

        elif len(text) < self.embed_size:
            dist = " " * (self.embed_size - len(text))

        else:
            dist = ""

        if color is None:
            color = self.fgcolor

        return f"[{self.bgcolor}][{color}]{text}{dist}[reset]\n"

    def spacer(self, length: int) ->  str:
        return " " * (round(self.embed_size / 2) - round((length + 2) / 2))

    def on_fire(self, args: list) -> str:
        try:
            title, body, config = args[0], args[1], {}
            for arg in args[2:]:
                if "=" not in arg:
                    continue

                dt = arg.split("=")
                if (not dt[0] or not dt[1]) or (len(dt) > 2):
                    continue

                config[dt[0]] = dt[1]

        except IndexError:
            title, body, config = "Title", "Body", {}

        # Configuration
        self.bgcolor = "bg" + (config.get("bg") or "lblack")
        self.fgcolor = config.get("fg") or "white"

        self.embed_size = 45

        # Construct fields
        title_spacer = self.spacer(len(title))
        title = f"{title_spacer}{title}{title_spacer}"

        footer = f"Today · {self.now()} {self.timezone}"
        footer_spacer = self.spacer(len(footer))

        footer = f"{footer_spacer}{footer}{footer_spacer}"

        body = [body[i:i + (self.embed_size - 5)] for i in range(0, len(body), (self.embed_size - 5))]
        body = "".join([self.add_line(f"{self.spacer(len(line))}{line}{self.spacer(len(line))}") for line in body])

        # Handle embed
        embed = "".join([line for line in [
            self.add_line(title, color = "yellow"),
            body,
            self.add_line(""),
            self.add_line(footer, color = "cyan")
        ]])
        return embed
