# Copyright 2021 iiPython

# Modules
from dateutil import tz
from datetime import datetime

from ..config import Config

from .struct.user import User
from .struct.guild import Guild

# Load config
config = Config()

# Timestamp handler
formats = {
    "12": lambda t: t.strftime("%I:%M %p"),
    "24": lambda t: t.strftime("%H:%M"),
    "utc12": lambda t: t.astimezone(tz.tzutc()).strftime("%I:%M %p"),
    "utc24": lambda t: t.astimezone(tz.tzutc()).strftime("%H:%M")
}

def format_timestamp(ts: datetime) -> str:
    timefrmt = config.get("timeformat")
    if timefrmt not in formats:
        return formats["24"](ts)

    return formats[timefrmt.rstrip("h")](ts)

# Result class
class ParseResult(object):
    def __init__(self, data: dict = None) -> None:

        # Basic structure
        self.type = data.get("type")
        self.data = data.get("data")
        self.guild = Guild(data.get("guild"))

        # Additional fields
        self.author = User(self.data.get("author"))
        self.content = self.data.get("content")
        self.timestamp_raw = datetime.utcfromtimestamp(self.data.get("timestamp")).replace(tzinfo = tz.tzutc()).astimezone(tz.tzlocal())
        self.timestamp = format_timestamp(self.timestamp_raw)

# Parser
def parse(data: dict) -> ParseResult:
    return ParseResult(data)
