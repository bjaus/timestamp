from calendar import monthrange
from datetime import datetime

MIN_TIMESTAMP = datetime(1, 1, 2).timestamp()

MAX_TIMESTAMP = datetime.max.timestamp()
MAX_TIMESTAMP_MS = MAX_TIMESTAMP * 1e3
MAX_TIMESTAMP_US = MAX_TIMESTAMP * 1e6

MAX_YEAR = datetime.max.year
MIN_YEAR = datetime.min.year

MAX_ORDINAL = datetime.max.toordinal()
MIN_ORDINAL = 1


def safe_date(year, month, day, hour, minute, second, microsecond):
    MAX_DAY = monthrange(year, month)[-1]

    return {
        'year': MIN_YEAR if year < MIN_YEAR else (MAX_YEAR if year > MAX_YEAR else year),
        'month': 1 if month < 1 else (12 if month > 12 else month),
        'day': 1 if day < 1 else (MAX_DAY if day > MAX_DAY else day),
        'hour': 0 if hour < 0 else (23 if hour > 23 else hour),
        'minute': 0 if minute < 0 else (59 if minute > 59 else minute),
        'second': 0 if second < 0 else (59 if second > 59 else second),
        'microsecond': 0 if microsecond < 0 else (999_999 if microsecond > 999_999 else microsecond),
    }


def validate_bounds(bounds):
    if bounds not in ('()', '(]', '[)', '[]'):
        raise ValueError(f"invalid bounds: {bounds!r} not in ('()', '(]', '[)', '[]')")


def validate_ordinal(ordinal):
    if isinstance(ordinal, bool) or not isinstance(ordinal, int):
        raise TypeError(f'ordinal must be integer: {type(ordinal)}')
    if not (MIN_ORDINAL <= ordinal <= MAX_ORDINAL):
        raise ValueError(f'ordinal out of range: {ordinal!r}')


def validate_timestamp(timestamp):
    if timestamp < MIN_TIMESTAMP:
        raise ValueError(f'timestamp too small: {timestamp!r}')
    if timestamp > MAX_TIMESTAMP:
        if timestamp < MAX_TIMESTAMP_MS:
            timestamp /= 1e3
        elif timestamp < MAX_TIMESTAMP_US:
            timestamp /= 1e6
        else:
            raise ValueError(f'timestamp too large: {timestamp!r}')
    return timestamp
