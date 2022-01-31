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
    input_opts = {"check": config.validate_ip}
)
addr = config.validate_ip(addr)
if config.manually_entered:
    config.save(True)

# Establish socket
socket = Socket(console, username)
tm = socket.gettimeout()
socket.settimeout(2)

console.print("[yellow]Connecting...[reset]\r", end = "")
socket.connect_wrap(addr)
socket.settimeout(tm)  # Reset timeout

# Handle SSL
try:
    console.print("[yellow]Establishing SSL connection...[reset]\r", end = "")
    socket.handshake()
    if not config.debug:
        console.clear()

except socket.HandshakeError:
    console.exit(-1, "[red]Failed to handshake with the server.[lblack]\nTry again at a later time.")

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
