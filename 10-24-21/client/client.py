# Copyright 2021 iiPython

# Modules
import string
from threading import Thread
from src.config import Config
from src.net.socket import Socket
from src.loops import SendLoop, ReceiveLoop

# Initialization
config = Config()
console = config.con  # No need for an extra import

# Grab configuration options
username = config.get(
    "username",
    ask = "[yellow]What should everyone call you?",
    input_opts = {"limit": 16, "whitelist": string.ascii_letters + string.digits + string.punctuation}
)
addr = config.get(
    "autoconnect",
    ask = "[yellow]Enter a server address to connect to",
    input_opts = {"limit": 21, "whitelist": string.digits + ":.", "check": config.validate_ip}
)
addr = config.validate_ip(addr)
if config.manually_entered:
    config.save(True)

# Establish socket
try:
    socket = Socket(console, username)
    tm = socket.gettimeout()
    socket.settimeout(2)

    console.print("[yellow]Connecting...[reset]\r", end = "")
    if not config.debug:
        console.clear()

    socket.connect(addr)
    socket.settimeout(tm)  # Reset timeout

except OSError:
    console.exit(-1, socket._FAILED_MSG.replace("send packet", "connect"))

# Spawn event loop
Thread(target = ReceiveLoop(socket).loop).start()

send = Thread(target = SendLoop(socket).loop)
send.start()

# Handle identification
socket.identify()

# Shutdown client
send.join()

socket.send_json({"type": "u.leave"})
console.exit(0, "[red]^C [yellow]| Come back another time.", sockets = [socket])
