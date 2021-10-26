# Copyright 2021 iiPython
# Mention highlighting plugin

# Configuration
config = {
    "foreground": "white",
    "background": "lblack"
}

# Plugin class
class Mention(object):
    def __init__(self, loader) -> None:
        self.loader = loader
        self.plugin_id = "mention"

        # Metadata
        self.name = "Mention Highlighter"
        self.author = "iiPython"

    def highlight(self, mention: str) -> str:
        return f"[bg{config['background']}][{config.get('foreground')}]{mention}[reset]"

    def on_recv(self, ctx) -> str:
        if "@" not in ctx.content:
            return ctx.content

        for tag in [u.name for u in ctx.guild.users] + [u.uid for u in ctx.guild.users]:
            if f"@{tag}" in ctx.content:
                ctx.content = ctx.content.replace(f"@{tag}", self.highlight(f"@{tag}"))

        return ctx.content
