# Copyright 2021 iiPython

# Modules
from .user import User

# Guild class
class Guild(object):
    def __init__(self, data: dict) -> None:
        self.name = data["name"]
        self.users = [User(user) for user in data["users"]]
        self.packet_limit = data["packet_limit"] or 1048576
