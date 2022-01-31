# Copyright 2021 iiPython

# User class
class User(object):
    def __init__(self, data: dict) -> None:
        self.uid = data["uid"]
        self.name = data["name"]
