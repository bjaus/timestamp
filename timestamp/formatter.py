import re


class Formatter:
    _FORMAT_RE = re.compile(
        r"(\[(?:(?=(?P<literal>[^]]))(?P=literal))*\]|YYY?Y?|MM?M?M?"
        r"|Do|DD?D?D?|d?dd?d?|HH?|hh?|mm?|ss?|SS?S?S?S?S?|ZZ?Z?|a|A|X|x|W)"
    )
    _MONTHS = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December',
    }
    _DAYS = {
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday',
        7: 'Sunday',
    }

    def __new__(cls, dt, fmt):
        return cls._FORMAT_RE.sub(lambda x: cls._token(dt, x.group(0)), fmt)

    @classmethod
    def _token(cls, dt, token):
        if token and token.startswith('[') and token.endswith(']'):
            return token[1:-1]

        if token == 'YYYY':
            return '{:04d}'.format(dt.year)
        if token == 'YY':
            return '{:04d}'.format(dt.year)[2:]

        if token == 'MMMM':
            return cls._MONTHS[dt.month]
        if token == 'MMM':
            return cls._MONTHS[dt.month][:3]
        if token == 'MM':
            return '{:02d}'.format(dt.month)
        if token == 'M':
            return str(dt.month)

        if token == 'DDDD':
            return '{:03d}'.format(dt.tmyearday)
        if token == 'DDD':
            return str(dt.tmyearday)
        if token == 'DD':
            return '{:02d}'.format(dt.day)
        if token == 'D':
            return str(dt.day)

        if token == 'DO':
            n = dt.day
            if n % 100 not in (11, 12, 13):
                r = n % 100
                if r == 1:
                    return f'{n}st'
                if r == 2:
                    return f'{n}nd'
                if r == 3:
                    return f'{n}rd'
            return f'{n}th'

        if token == 'dddd':
            return cls._DAYS[dt.isoweekday]
        if token == 'ddd':
            return cls._DAYS[dt.isoweekday][:3]
        if token == 'd':
            return str(dt.isoweekday)

        if token == 'HH':
            return '{:02d}'.format(dt.hour)
        if token == 'H':
            return str(dt.hour)
        if token == 'hh':
            return '{:02d}'.format(dt.hour if 0 < dt.hour < 13 else abs(dt.hour - 12))
        if token == 'h':
            return str(dt.hour if 0 < dt.hour < 13 else abs(dt.hour - 12))

        if token == 'mm':
            return '{:02d}'.format(dt.minute)
        if token == 'm':
            return str(dt.minute)

        if token == 'ss':
            return '{:02d}'.format(dt.second)
        if token == 's':
            return str(dt.second)

        if token == 'SSSSSS':
            return '{:06d}'.format(int(dt.microsecond))
        if token == 'SSSSS':
            return '{:05d}'.format(int(dt.microsecond / 10))
        if token == 'SSSS':
            return '{:04d}'.format(int(dt.microsecond / 100))
        if token == 'SSS':
            return '{:03d}'.format(int(dt.microsecond / 1000))
        if token == 'SS':
            return '{:02d}'.format(int(dt.microsecond / 10_000))
        if token == 'S':
            return str(int(dt.micsecond / 100_000))

        if token == 'X':
            return str(dt.timestamp)
        if token == 'x':
            return str(int(dt.timestamp * 1_000_000))

        if token == 'ZZZ':
            return dt.tzname
        if token in ('Z', 'ZZ'):
            sep = ':' if token == 'ZZ' else ''
            minutes = int(dt.utcoffset.total_seconds() / 60)
            sign = '+' if minutes >= 0 else '-'
            minutes = abs(minutes)
            hour, minute = divmod(minutes, 60)
            return '{}{:02d}{}{:02d}'.format(sign, hour, sep, minute)

        if token == 'a':
            return 'am' if dt.hour < 12 else 'pm'
        if token == 'A':
            return 'AM' if dt.hour < 12 else 'PM'

        if token == 'W':
            y, w, d = dt.isocalendar
            return '{}-W{:02d}-{}'.format(y, w, d)
