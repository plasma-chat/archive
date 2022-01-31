# Copyright 2021 iiPython

# Modules
import os
import re
import sys
import shutil
import traceback
from typing import Union
from types import FunctionType
from iikp import readchar, keys

# Initialization
if os.name == "nt":
    try:
        from colorama import init
        init()

    except ImportError:
        pass

    # Windows libraries (for cursor management)
    import ctypes

    # Cursor data class
    class _CursorInfo(ctypes.Structure):
        _fields_ = [
            ("size", ctypes.c_int),
            ("visible", ctypes.c_byte)
        ]

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

        self._regen_ts()
        self.hcursor()

    def _to_ansi(self, code: int) -> str:
        return f"\033[{code}m"

    def _regen_ts(self) -> None:
        self._size = shutil.get_terminal_size()
        self._ts = " " * self._size.columns

    def _strip_tags(self, text: str) -> str:
        for tag in re.findall(r"\[\/*[a-zA-Z]{1,}\]", text):
            text = text.replace(tag, "")

        return text

    def clear(self) -> None:
        self._regen_ts()
        os.system(self._clear_cmd)

    def print(self, text: str, color: bool = True, print_out: bool = True, **kwargs) -> str:
        self._regen_ts()
        if not color:
            return self._strip_tags(text)

        # Process tags | TODO: Make a much better, recursive system
        text += ("[reset]" if not text.endswith("[reset]") else "")
        for tag in self._color_map:
            text = text.replace(f"[{tag}]", self._color_map[tag]).replace(f"[/{tag}]", self._color_map["reset"])

        if not print_out:
            return text

        return print(text, **kwargs)

    def input(self, prompt: str = "[yellow]> ", limit: int = None, whitelist: str = None, check: FunctionType = None) -> str:
        self._regen_ts()
        limit = limit or self._size.columns

        # Main loop
        prompt += ("[reset]" if not prompt.endswith("[reset]") else "")
        message = ""
        while True:

            # Print prompt
            print(f"\r{self._ts}\r{self.print(prompt, print_out = False)}{message}{self.print('[yellow]_[reset]', print_out = False)}", end = "")

            # Handle keypresses
            key = readchar()
            if key == keys.ENTER and message.strip():
                if not check or (check and check(message)):
                    return message

            elif key == keys.BACKSPACE and message:
                message = message[:-1]

            elif key == keys.CTRL_C:
                return self.exit(0, "[red]^C [yellow]| Come back another time.")

            elif (isinstance(key, str) or key == keys.SPACE) and (len(message) != limit) and ((key in whitelist) if whitelist else True):
                if key == keys.SPACE:
                    message += " "

                else:
                    message += key

    def get_keys(self, allowed_keys: list) -> Union[None, str, int]:
        while True:
            key = readchar()
            if key in allowed_keys:
                return key

    def hcursor(self) -> None:
        if os.name == "nt":
            if not hasattr(self, "_ci"):
                self._ci = _CursorInfo()

            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(self._ci))
            self._ci.visible = False
            ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(self._ci))

        else:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()

    def scursor(self) -> None:
        if os.name == "nt":
            if not hasattr(self, "_ci"):
                self._ci = _CursorInfo()

            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(self._ci))
            self._ci.visible = True
            ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(self._ci))

        else:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

    def exit(self, code: int, message: str = None, sockets: list = [], clear: bool = True) -> None:
        if "--debug" not in sys.argv and clear:
            self.clear()

        if message is not None:
            self.print(message.replace("\n", "\r\n"))

        # Close sockets
        if sockets:
            for socket in sockets:
                socket.close()

        # Show cursor
        self.scursor()

        # Close script
        # Currently this uses _exit, which kills threads by
        # bypassing garbage collection. HOWEVER, I think
        # that might be a bad idea, so I want to figure out
        # a killable thread solution from threading.Thread
        # until then, ¯\_(ツ)_/¯
        return os._exit(code)

    def error(self, error: Exception, path: str = None) -> None:
        self._regen_ts()
        self.print(f"\r{self._ts}\r", end = "")
        self.print(f"[red]An internal exception occured{f' ({path})' if path else ''}:\n\t{error}")

    def traceback(self, error: Exception) -> None:
        if "--debug" not in sys.argv:
            self.clear()

        self.print("[red]Plasma has experienced an internal error, below are the details.")
        print(f"{type(error).__name__}: {error}")
        tb = traceback.extract_tb(error.__traceback__)
        for item in traceback.StackSummary.from_list(tb).format():
            print(item, end = "")

        return self.exit(
            1,
            "\n[lblack]Keep experiencing this? Contact [yellow]iiPython (github.com/ii-Python)",
            clear = False
        )
