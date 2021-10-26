# Copyright 2021 iiPython

# Modules
from dateutil import tz
from datetime import datetime

from ..config import Config

from .struct.user import User
from .struct.guild import Guild

# Load config
config = Config()
def format_timestamp(ts: datetime) -> str:
    timefrmt = config.get("timeformat").rstrip("h")
    formats = {
        "12": lambda t: t.strftime("%I:%M %p"),
        "24": lambda t: t.strftime("%H:%M"),
        "utc12": lambda t: t.astimezone(tz.tzutc()).strftime("%I:%M %p"),
        "utc24": lambda t: t.astimezone(tz.tzutc()).strftime("%H:%M")
    }
    if timefrmt in formats:
        return formats[timefrmt](ts)

    return ts

# Result class
class ParseResult(object):
    def __init__(self, data: dict = None) -> None:

        # Basic structure
        self.type = data["type"]
        self.data = data["data"]
        self.guild = Guild(data["guild"])

        # Additional fields
        self.author = User(self.data["author"])
        self.content = self.data["content"]
        self.timestamp_raw = datetime.utcfromtimestamp(self.data["timestamp"]).replace(tzinfo = tz.tzutc()).astimezone(tz.tzlocal())
        self.timestamp = format_timestamp(self.timestamp_raw)

# Parser
def parse(data: dict) -> ParseResult:
    return ParseResult(data)
