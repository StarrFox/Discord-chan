import logging
from datetime import datetime as python_datetime
from collections import OrderedDict

from pendulum.datetime import DateTime
from loguru import logger

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


class LRU[K, V](OrderedDict[K, V]):
    # TODO: find out how to actually type args and kwargs here
    def __init__(self, maxsize: int = 100, *args: tuple[object], **kwargs: dict[object, object]):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: K, value: V):
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            self.popitem(last=False)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        if not frame.f_code:
            return  # Don't care

        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back

            if frame is None:
                return

            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def detailed_human_time(input_seconds: float | int):
    # drop rest
    input_seconds = int(input_seconds)
    minutes, seconds = divmod(input_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365)

    msgs: list[str] = []
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
    timestamp: float = datetime.timestamp() # type: ignore (the unknown case is false)

    if both:
        full_time = f"<t:{int(timestamp)}>" # type: ignore
        relative_time = f"<t:{int(timestamp)}:R>" # type: ignore

        return f"{full_time} ({relative_time})"
    else:
        return f"<t:{int(timestamp)}{':R' if relative else ''}>" # type: ignore
