# Copyright 2021 iiPython

# Modules
from src import server, config

# Launch server
server.start(
    addr = (
        config.get("host") or "0.0.0.0",
        config.get("port") or 2075
    ),
    name = config.get("name") or "Server"
)
