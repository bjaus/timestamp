import re
from datetime import tzinfo as dtzinfo
from dateutil import tz as dtz


class TzInfo:
    _TZINFO_RE = re.compile(r"^([\+\-])?(\d{2})(?:\:?(\d{2}))?$")

    @staticmethod
    def get(tzinfo):
        if isinstance(tzinfo, str):
            return dtz.gettz(tzinfo)
        return tzinfo

    @classmethod
    def parse(cls, tzo, **kwargs):
        tzinfo = None
        safe = kwargs.get('safetz', False)

        if isinstance(tzo, (dtz.tzutc, dtz.tzlocal, dtz.tzfile, dtz.tzoffset)):
            return tzo

        elif all([
            isinstance(tzo, dtzinfo),
            hasattr(tzinfo, 'localize'),
            getattr(tzinfo, 'zone', None)
        ]):
            return cls.parse(tzinfo.zone, **kwargs)

        elif tzo is None or tzo in ('utc', 'UTC', 'z', 'Z'):
            return dtz.tzutc()

        elif tzo == 'local':
            return dtz.tzlocal()

        else:
            iso_match = cls._TZINFO_RE.match(tzo)
            if iso_match:
                sign, hours, minutes = iso_match.groups()
                if minutes is None:
                    minutes = 0
                seconds = (int(hours) * 3600) + (int(minutes) * 60)
                if sign == '-':
                    seconds *= -1
                return dtz.tzoffset(None, seconds)

            tzinfo = cls.get(tzo)
            if tzinfo is None:
                if safe:
                    return dtz.tzutc()
                else:
                    raise ValueError(f'Invalid time zone: {tzo!r}')
            return tzinfo

    @classmethod
    def extract(cls, tzinfo):
        if isinstance(tzinfo, dtz.tzutc):
            return 'UTC'
        elif isinstance(tzinfo, dtz.tzlocal):
            return 'local'
        elif isinstance(tzinfo, dtz.tzoffset):
            return str(tzinfo._offset.total_seconds())
        try:
            return '/'.join(
                [
                    i for i in re.search(r"'(.*?)'", str(tzinfo)).group().replace("'", "").split("/")
                    if any([j.isupper() for j in i])
                ]
            )
        except Exception:
            return 'unknown'
