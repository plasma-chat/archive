# Copyright 2021 iiPython

# Modules
import os
import re
import shutil

# Console class
class Console(object):
    def __init__(self) -> None:
        self._clear_cmd = "clear" if os.name != "nt" else "cls"

        # Color map
        self._color_map = {

            # Regular colors
            "black": 30, "red": 31, "green": 32,
            "yellow": 33, "blue": 34, "magenta": 35,
            "cyan": 36, "white": 37,

            # Text styles
            "bright": 1, "dim": 2, "norm": 22,
            "reset": 39
        }
        self._new_clmap = {}
        for color in self._color_map:

            # Normal
            _cl = self._color_map[color]
            self._new_clmap[color] = self._to_ansi(_cl)

            # Light colors / Background / Light Background
            if color not in ["bright", "dim", "norm"]:
                self._new_clmap["l" + color] = self._to_ansi(_cl + 60)
                self._new_clmap["bg" + color] = self._to_ansi(_cl + 10)
                self._new_clmap["bgl" + color] = self._to_ansi(_cl + 70)

        self._color_map = self._new_clmap
        for _rs in [self._color_map["norm"], self._color_map["bgreset"]]:
            self._color_map["reset"] += _rs

    def _to_ansi(self, code: int) -> str:
        return f"\033[{code}m"

    def _strip_tags(self, text: str) -> str:
        for tag in re.findall(r"\[\/*[a-zA-Z]{1,}\]", text):
            text = text.replace(tag, "")

        return text

    def ts(self) -> str:
        return " " * shutil.get_terminal_size().columns

    def clear(self) -> None:
        os.system(self._clear_cmd)

    def print(self, text: str, color: bool = True, print_out: bool = True, **kwargs) -> str:
        if not color:
            return self._strip_tags(text)

        # Process tags | TODO: Make a much better, recursive system
        text += ("[reset]" if not text.endswith("[reset]") else "")
        for tag in self._color_map:
            text = text.replace(f"[{tag}]", self._color_map[tag]).replace(f"[/{tag}]", self._color_map["reset"])

        if not print_out:
            return text

        return print(text, **kwargs)
