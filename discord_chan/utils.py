from collections import OrderedDict
from datetime import datetime as python_datetime

from loguru import logger
from pendulum.datetime import DateTime

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False,
}


# from: https://urlregex.com/
link_regex = (
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


class LRU(OrderedDict):
    def __init__(self, maxsize=100, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            self.popitem(last=False)


def detailed_human_time(input_seconds: float | int):
    # drop rest
    input_seconds = int(input_seconds)
    minutes, seconds = divmod(input_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365)

    msgs = []
    if years:
        msgs.append(f"{years} year(s)")
    if minutes:
        msgs.append(f"{minutes} minute(s)")
    if days:
        msgs.append(f"{days} day(s)")
    if hours:
        msgs.append(f"{hours} hour(s)")
    if seconds:
        msgs.append(f"{seconds} second(s)")

    if not msgs:
        msgs.append("0 second(s)")

    return ", ".join(msgs)


def to_discord_timestamp(
    datetime: DateTime | python_datetime,
    *,
    relative: bool = True,
    both: bool = False,
) -> str:
    timestamp: float = datetime.timestamp()

    if both:
        full_time = f"<t:{int(timestamp)}>"
        relative_time = f"<t:{int(timestamp)}:R>"

        return f"{full_time} ({relative_time})"
    else:
        return f"<t:{int(timestamp)}{':R' if relative else ''}>"
