# Copyright 2021 carpedm20
# See the original at https://github.com/carpedm20/emoji
# Taken to reduce dependency count

# Modules
import re
from .emojis import EMOJI_ALIAS_UNICODE_ENGLISH
def em(string: str) -> str:
    pattern = re.compile(u'(%s[\\w\\-&.’”“()!#*+?–,/]+%s)' % (":", ":"), flags = re.UNICODE)
    def replace(match):  # noqa
        mg = match.group(1).replace(":", ":").replace(":", ":")
        emj = EMOJI_ALIAS_UNICODE_ENGLISH.get(mg, mg)
        return emj

    return pattern.sub(replace, string)
