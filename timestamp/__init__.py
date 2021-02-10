import re
import sys
import calendar
from datetime import (
    date,
    datetime,
    timedelta,
)

from dateutil import tz as dtz
from dateutil.parser import ParserError, parse as dtp
from dateutil.relativedelta import relativedelta

from . import formatter, parser, util

try:
    import bson
except ImportError:
    has_bson = False
else:
    has_bson = True


class Timestamp:
    _ATTRS = ["year", "month", "day", "hour", "minute", "second", "microsecond"]
    _ATTRS_PLURAL = [f"{attr}s" for attr in _ATTRS]
    _ATTR_MAP = {k: v for k, v in zip(_ATTRS_PLURAL, _ATTRS)}

    _REXLATE = re.compile(r'^(?P<num>[-]?[\d]*)(?P<frame>[minute|hour|day|week|month|quarter|year]*[s]?)$')
    _RESTAMP = re.compile(
        r'^(?P<year>[\d]{2,4})[-/]?'
        r'(?P<month>[\d]{1,2})[-/]?'
        r'(?P<day>[\d]{1,2})[\sT]?'
        r'(?P<hour>[\d]{0,2})[:]?'
        r'(?P<minute>[\d]{0,2})[:]?'
        r'(?P<second>[\d]{0,2})[\s\.]?'
        r'(?P<microsecond>[\d]{0,6})[\s]?'
        r'(?P<tzoffset>[+-]?[\d]{0,2}[:]?[\d]{0,2})[\s]?'
        r'(?P<tzname>[\w]*[/]?[\w]*)$'
    )

    def __init__(
        self,
        year,
        month,
        day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        safedt=False,
        safetz=False,
        **kwargs,
    ):
        self._safetz = safetz
        self._safedt = safedt
        try:
            year = int(year)
            month = int(month)
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            second = int(second)
            microsecond = int(microsecond)
        except (TypeError, ValueError) as e:
            raise e

        tzinfo = self.tzparser(tzinfo, safetz=safetz)
        try:
            self._dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo)
        except ValueError as e:
            if not safedt:
                raise e

            self._dt = datetime(
                **util.safe_date(year, month, day, hour, minute, second, microsecond),
                tzinfo=tzinfo
            )

    def __add__(self, other):
        if isinstance(other, (timedelta, relativedelta)):
            return self.fromdatetime(self._dt + other, tzinfo=self.tzinfo)
        return NotImplementedError(f'not supported: {other!r}')

    def __eq__(self, other):
        return self.__eval__(other, '==')

    def __eval__(self, other, sign):
        if sign not in ['==', '!=', '<', '<=', '>', '>=']:
            raise NotImplementedError(f'not supported: {sign!r}')
        elif other is None:
            return False
        elif isinstance(other, str):
            other = self.__class__.get(other)
        elif has_bson and isinstance(other, bson.ObjectId):
            other = self.fromdatetime(other.generation_time.replace(tzinfo=None))

        if self.isdate(other):
            return eval(f'self.date {sign} other')
        elif self.isdatetime(other):
            if not other.tzinfo:
                return eval(f'self.naive {sign} other')
            return eval(f'self.datetime {sign} other')
        elif self.isself(other):
            return eval(f'self.datetime {sign} other.datetime')

    def __format__(self, fmt):
        if isinstance(fmt, str):
            return self.format(fmt)
        return str(self)

    def __ge__(self, other):
        return self.__eval__(other, '>=')

    def __gt__(self, other):
        return self.__eval__(other, '>')

    def __hash__(self):
        return self._dt.__hash__()

    def __le__(self, other):
        return self.__eval__(other, '<=')

    def __lt__(self, other):
        return self.__eval__(other, '<')

    def __ne__(self, other):
        return self.__eval__(other, '!=')

    def __radd__(self, other):
        return self.__add__(other)

    def __reduce__(self):
        return (
            self.__class__, (
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.microsecond,
                self.tz,
                self._safedt,
                self._safetz,
            )
        )

    def __repr__(self):
        return '{}({}, tzinfo={})'.format(
            self.__class__.__name__,
            self.format('YYYY, M, D, HH, mm, ss, SSSSSS'),
            repr(self.tz)
        )

    def __rsub__(self, other):
        if self.isself(other):
            return other._dt - self._dt
        elif self.isdate(other):
            return other - self.date
        elif self.isdatetime(other):
            if other.tzinfo:
                return other - self.dateime
            return other - self.naive
        return self.__sub__(other)

    def __str__(self):
        return self.isoformat()

    def __sub__(self, other):
        if isinstance(other, (timedelta, relativedelta)):
            return self.fromdatetime(self._dt - other, tzinfo=self.tzinfo)
        elif self.isself(other):
            return self._dt - other._dt
        elif self.isdate(other):
            return self.date - other
        elif self.isdatetime(other):
            if other.tzinfo:
                return self.dateime - other
            return self.naive - other
        raise NotImplementedError(f'not supported: {other!r}')

    ##############
    # Properties #
    ##############

    @property
    def ambiguous(self):
        return dtz.datetime_ambiguous(self._dt)

    @property
    def ctime(self):
        return self._dt.ctime()

    @property
    def date(self):
        return self._dt.date()

    @property
    def datetime(self):
        return self._dt

    @property
    def day(self):
        return self._dt.day

    @property
    def dst(self):
        return self._dt.dst()

    @property
    def hour(self):
        return self._dt.hour

    @property
    def isdst(self):
        return bool(self.tmisdst)

    @property
    def imaginary(self):
        return not dtz.datetime_exists(self._dt)

    @property
    def isocalendar(self):
        return self._dt.isocalendar()

    @property
    def isoweekday(self):
        return self._dt.isoweekday()

    @property
    def microsecond(self):
        return self._dt.microsecond

    @property
    def minute(self):
        return self._dt.minute

    @property
    def month(self):
        return self._dt.month

    def monthname(self):
        return self.format('MMMM')

    @property
    def naive(self):
        return self._dt.replace(tzinfo=None)

    @property
    def quarter(self):
        return int((self.month - 1) / 3) + 1

    @property
    def second(self):
        return self._dt.second

    @property
    def time(self):
        return self._dt.time()

    @property
    def timegm(self):
        return calendar.timegm(self.timetuple)

    @property
    def timestamp(self):
        return self._dt.timestamp()

    @property
    def timetuple(self):
        return self._dt.timetuple()

    @property
    def timetz(self):
        return self._dt.timetz()

    @property
    def tmday(self):
        return self.timetuple.tm_mday

    @property
    def tmhour(self):
        return self.timetuple.tm_hour

    @property
    def tmisdst(self):
        return self.timetuple.tm_isdst

    @property
    def tmminute(self):
        return self.timetuple.tm_min

    @property
    def tmmonth(self):
        return self.timetuple.tm_mon

    @property
    def tmsecond(self):
        return self.timetuple.tm_sec

    @property
    def tmweekday(self):
        return self.timetuple.tm_wday

    @property
    def tmyear(self):
        return self.timetuple.tm_year

    @property
    def tmyearday(self):
        return self.timetuple.tm_yday

    @property
    def toordinal(self):
        return self._dt.toordinal()

    @property
    def tz(self):
        return self.tzextract(self.tzinfo)

    @property
    def tzinfo(self):
        return self._dt.tzinfo

    @tzinfo.setter
    def tzinfo(self, tz):
        tzinfo = self.tzparser(tz, safetz=self._safetz)
        self._dt = self._dt.replace(tzinfo=tzinfo)

    @property
    def tzname(self):
        return self._dt.tzname()

    @property
    def unixtimestamp(self):
        return self.timestamp * 1000

    @property
    def utcoffset(self):
        return self._dt.utcoffset()

    @property
    def utctimetuple(self):
        return self._dt.utctimetuple()

    @property
    def week(self):
        return self.isocalendar[1]

    @property
    def weekday(self):
        return self._dt.weekday()

    @property
    def year(self):
        return self._dt.year

    ####################
    # Instance Methods #
    ####################

    def astimezone(self, tz):
        tzinfo = self.tzparser(tz)
        return self._dt.astimezone(tzinfo)

    def ceil(self, frame):
        return self.span(frame)[1]

    def copy(self):
        return self.fromdatetime(self._dt, tzinfo=self.tzinfo)

    def fileformat(self, include_time=False):
        if include_time:
            return self.format('YYYYMMDDHHmmss')
        return self.format('YYYYMMDD')

    def floor(self, frame):
        return self.span(frame)[0]

    def format(self, fmt='YYYY-MM-DD HH:mm:ssZZ'):
        return formatter.Formatter(self, fmt)

    def humanize(self):
        def pluralize(f, i):
            return f'{f}' if i == 1 else f'{f}s'

        now = self.now(self.tzinfo)
        if now > self:
            s = int((now - self).total_seconds())
            t = '{} {} ago'
        else:
            s = int((self - now).total_seconds())
            t = 'in {} {}'

        i = int(s / 31_536_000)
        if i >= 1:
            return t.format(i, pluralize('year', i))

        i = int(s / 2_592_000)
        if i >= 1:
            return t.format(i, pluralize('month', i))

        i = int(s / 86_400)
        if i >= 1:
            return t.format(i, pluralize('day', i))

        i = int(s / 3_600)
        if i >= 1:
            return t.format(i, pluralize('hour', i))

        i = int(s / 60)
        if i >= 1:
            return t.format(i, pluralize('minute', i))

        return t.format(s, pluralize('second', s))

    def isbetween(self, start, end, bounds='()'):
        util.validate_bounds(bounds)
        if not self.isconvertable(start):
            raise ValueError(f'not DateTool convertable: {start!r}')
        if not self.isconvertable(end):
            raise ValueError(f'not DateTool convertable: {end!r}')
        start = self.get(start)
        end = self.get(end)

        include_start = bounds[0] == '['
        include_end = bounds[1] == ']'

        return all((
            (start.timestamp <= self.timestamp <= end.timestamp),
            (include_start or start.timestamp < self.timestamp),
            (include_end or self.timestamp < end.timestamp)
        ))

    def isoformat(self, sep="T", timespec="auto"):
        return self._dt.isoformat(sep, timespec)

    def jsonify(self):
        return self.isoformat()

    def replace(self, **kwargs):
        kw = {}
        for k, v in kwargs.items():
            if k in self._ATTRS:
                kw[k] = v
            elif k in self._ATTR_MAP:
                kw[k] = self._ATTR_MAP[k]
            elif k != 'tzinfo' or k in ('week', 'weeks', 'quarter', 'quarters'):
                raise NotImplementedError(f'not supportd: {k!r}')
        kw['tzinfo'] = self.tzparser(kwargs.get('tzinfo', self.tzinfo))
        return self.fromdatetime(self._dt.replace(**kw))

    def shift(self, **kwargs):
        relatives = {}
        addattrs = ['weeks', 'quarters', 'weekday']
        for k, v in kwargs.items():
            if k in self._ATTR_MAP or k in addattrs:
                relatives[k] = v
            elif k in self._ATTRS + ['week', 'quarter']:
                relatives[f'{k}s'] = v
            else:
                supported = ', '.join(self._ATTRS_PLURAL + addattrs)
                raise ValueError(f'timeframe not supported: {k!r} not in {supported}')

        relatives.setdefault('months', 0)
        relatives['months'] += relatives.pop('quarters', 0) * 3

        current = self._dt + relativedelta(**relatives)
        if not dtz.datetime_exists(current):
            current = dtz.resolve_imaginary(current)

        return self.fromdatetime(current, tzinfo=self.tzinfo)

    def smartformat(self, d='-', s=' ', t=':', tz=False, fname=False):
        if fname:
            tz = False
            d = s = t = ''
        tz = 'ZZ' if tz else ''
        fmt = f'YYYY{d}MM{d}DD'
        if not any([self.hour, self.minute, self.second]):
            return self.format(fmt)
        fmt += f'{s}HH{t}mm{t}ss{tz}'
        return self.format(fmt)

    def span(self, frame, count=1, bounds="[)", exact=False):
        util.validate_bounds(bounds)
        absolute, relative, steps = self._get_frames(frame)

        if absolute == 'week':
            attr = 'day'
        elif absolute == 'quarter':
            attr = 'month'
        else:
            attr = absolute

        floor = self
        if not exact:
            index = self._ATTRS.index(attr)
            frames = self._ATTRS[: index + 1]
            values = [getattr(self, f) for f in frames]

            for _ in range(3 - len(values)):
                values.append(1)
            floor = self.__class__(*values, tzinfo=self.tzinfo)

            if absolute == 'week':
                floor = floor.shift(days=-(self.isoweekday - 1))
            elif absolute == 'quarter':
                floor = floor.shift(months=-((self.month - 1) % 3))

        ceil = floor.shift(**{relative: count * steps})

        if bounds[0] == '(':
            floor = floor.shift(microseconds=1)
        if bounds[1] == ')':
            ceil = ceil.shift(microseconds=-1)

        return floor, ceil

    def strftime(self, fmt):
        return self._dt.strftime(fmt)

    def to(self, tz, **kwargs):
        tzinfo = self.tzparser(tz, **kwargs)
        return self.fromdatetime(self.astimezone(tzinfo), **kwargs)

    def toutc(self):
        return self.to('UTC')

    #################
    # Class Methods #
    #################

    @classmethod
    def fromdate(cls, d, tzinfo=None, **kwargs):
        if not cls.isdate(d):
            raise ValueError(f'invalid date: {d!r}')
        return cls(
            d.year,
            d.month,
            d.day,
            tzinfo=tzinfo,
            **kwargs
        )

    @classmethod
    def fromdatetime(cls, dt, tzinfo=None, **kwargs):
        if not cls.isdatetime(dt):
            raise ValueError(f'invalid datetime: {dt!r}')
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=tzinfo or dt.tzinfo,
            **kwargs
        )

    @classmethod
    def fromordinal(cls, value, tzinfo=None, **kwargs):
        util.validate_ordinal(value)
        return cls.fromdatetime(datetime.fromordinal(value), tzinfo=tzinfo, **kwargs)

    @classmethod
    def fromtimestamp(cls, value, tzinfo=None, **kwargs):
        if not cls.istimestamp(value):
            raise ValueError(f'invalid timestamp: {value!r}')
        timestamp = util.validate_timestamp(float(value))
        tzinfo = cls.tzparser(tzinfo, **kwargs)
        return cls.fromdatetime(datetime.fromtimestamp(timestamp, tzinfo), **kwargs)

    @classmethod
    def get(cls, d, tzinfo=None, default=None, **kwargs):
        if cls.isself(d):
            if tzinfo is None:
                tzinfo = d.tzinfo
            else:
                tzinfo = cls.tzparser(tzinfo, **kwargs)
            return cls.fromdatetime(d._dt, tzinfo=tzinfo, **kwargs)

        tzinfo = cls.tzparser(tzinfo, **kwargs)
        if cls.isdate(d):
            return cls.fromdate(d, tzinfo=tzinfo, **kwargs)
        elif cls.isdatetime(d):
            return cls.fromdatetime(d, tzinfo=tzinfo, **kwargs)
        elif cls.istimestamp(d):
            return cls.fromtimestamp(d, tzinfo=tzinfo, **kwargs)
        else:
            if isinstance(d, str):
                if d.isdigit():
                    if len(d) == 6:
                        d = '{}-{}'.format(d[:4], d[4:])
            try:
                dt = dtp(d)
            except (ParserError, ValueError):
                if default == 'now':
                    return cls.now(tzinfo=tzinfo)
                return default
            return cls.fromdatetime(dt, tzinfo=dt.tzinfo or tzinfo)

    @classmethod
    def interval(cls, frame, start, end, interval=1, tz=None, bounds='[)', exact=False):
        interval = int(interval)
        if interval < 1:
            raise ValueError('interval must be a positive intger')
        spanrange = iter(cls.spanrange(frame, start, end, tz, bounds=bounds, exact=exact))
        while True:
            try:
                s, e = next(spanrange)
                for _ in range(interval - 1):
                    try:
                        _, e = next(spanrange)
                    except StopIteration:
                        continue
                yield s, e
            except StopIteration:
                return

    @classmethod
    def isconvertable(cls, d):
        return any([
            cls.isself(d),
            cls.isdateobject(d)
        ])

    @classmethod
    def isself(cls, d):
        return isinstance(d, cls)

    @classmethod
    def now(cls, tzinfo=None, **kwargs):
        tzinfo = cls.tzparser(tzinfo)
        return cls.fromdatetime(datetime.now(tzinfo), **kwargs)

    @classmethod
    def range(cls, frame, start='now', end=None, tz=None, limit=None):  # noqa
        _, relative, steps = cls._get_frames(frame)
        if isinstance(start, str):
            tzinfo = cls.tzparser(tz)
        else:
            tzinfo = cls.tzparser(start.tzinfo if tz is None else tz)

        def getiteration(e, lim):
            if e is None:
                if limit is None:
                    raise ValueError('either `end` or `limit` params required')
                return datetime.max, limit
            elif lim is None:
                return end, sys.maxsize
            return e, lim

        start = cls.get(start, tzinfo=tzinfo)
        end, limit = getiteration(end, limit)
        end = cls.get(end, tzinfo=tzinfo)

        current = start.copy()
        dayclipped = False
        i = 0

        while current <= end and i < limit:
            i += 1
            yield current

            current = current.shift(**{relative: steps})

            if frame in ['month', 'quarter', 'year'] and current.day < start.day:
                dayclipped = True

            if dayclipped and current.day != calendar.monthrange(current.year, current.month)[1]:
                current = current.replace(day=start.day)

    @classmethod
    def spanrange(cls, frame, start, end, tz=None, limit=None, bounds='[)', exact=False):
        if cls.isdatetime(start):
            tzinfo = cls.tzparser(start.tzinfo if tz is None else tz)
        else:
            tzinfo = cls.tzparser(tz)
        start = cls.get(start, tzinfo=tzinfo).span(frame, exact=exact)[0]
        end = cls.get(end, tzinfo=tzinfo)
        for r in cls.range(frame, start, end, tz, limit):
            if not exact:
                yield r.span(frame, bounds=bounds, exact=exact)
            else:
                floor, ceil = r.span(frame, bounds=bounds, exact=exact)
                if ceil > end:
                    ceil = end
                    if bounds[1] == ')':
                        ceil += relativedelta(microseconds=-1)
                if floor == end:
                    break
                elif floor + relativedelta(microseconds=-1) == end:
                    break
                yield floor, ceil

    @classmethod
    def strptime(cls, string, fmt, tzinfo=None):
        dt = datetime.strptime(string, fmt)
        return cls.fromdatetime(dt, tzinfo=tzinfo)

    @classmethod
    def tzparser(cls, tz, **kwargs):
        return parser.TzInfo.parse(tz, **kwargs)

    @classmethod
    def tzget(cls, tzinfo):
        return parser.TzInfo.get(tzinfo)

    @classmethod
    def tzextract(cls, tzinfo):
        return parser.TzInfo.extract(tzinfo)

    @classmethod
    def utcnow(cls):
        return cls.fromdatetime(datetime.utcnow())

    @classmethod
    def xlate(cls, rule, is_from=True, default=None):
        now = cls.now()
        if not default:
            default = now

        if rule == 'default':
            if is_from:
                return now.shift(days=-32)
            return now

        elif rule in ['current', 'now']:
            return now

        elif rule == 'hour':
            if is_from:
                return now.floor('hour')
            return now.ceil('hour')

        elif rule == 'day':
            if is_from:
                return now.floor('day')
            return now.ceil('day')

        elif rule == 'week':
            if is_from:
                return now.floor('week')
            return now.ceil('week')

        elif rule == 'month':
            if is_from:
                return now.floor('month')
            return now.ceil('month')

        elif rule == 'lasthour':
            now = now.shift(hour=-1)
            if is_from:
                return now.floor('hour')
            return now.ceil('hour')

        elif rule in ['yesterday', 'lastday']:
            now = now.shift(days=-1)
            if is_from:
                return now.floor('day')
            return now.ceil('day')

        elif rule == 'lastweek':
            now = now.shift(weeks=-1)
            if is_from:
                return now.floor('week')
            return now.ceil('week')

        elif rule == 'lastmonth':
            now = now.shift(months=-1)
            if is_from:
                return now.floor('month')
            return now.ceil('month')

        elif rule == 'lastquarter':
            now = now.floor('quarter').shift(quarter=-1)
            if is_from:
                return now.floor('quarter')
            return now.ceil('quarter')

        elif rule == 'lastyear':
            now = now.shift(year=-1)
            if is_from:
                return now.floor('year')
            return now.ceil('year')

        elif rule == 'bot':
            return now.replace(year=2008).floor('year')

        match = cls._RESTAMP.match(rule)
        if match:
            result = {}
            m = match.groupdict()
            for k, v in m.items():
                if k in cls._ATTRS:
                    if v:
                        result[k] = int(v)
                    else:
                        result[k] = 0
            result['tzinfo'] = m['tzname'] or m['tzoffset'] or None
            dt = cls(**result)
            return dt.to('UTC') if dt else None

        match = cls._REXLATE.match(rule)
        if match:
            m = match.groupdict()
            return now.shift(**{m['frame']: int(m['num'])})

        raise ValueError(f'not supported: {rule!r}')

    ##################
    # Static Methods #
    ##################

    @staticmethod
    def isdate(obj):
        return isinstance(obj, date) and not isinstance(obj, datetime)

    @staticmethod
    def isdatetime(obj):
        return isinstance(obj, date) and isinstance(obj, datetime)

    @staticmethod
    def isdateobject(obj):
        return isinstance(obj, date)

    @staticmethod
    def istimestamp(obj):
        if obj is None or isinstance(obj, bool) or not isinstance(obj, (int, float, str)):
            return False
        try:
            util.validate_timestamp(float(obj))
        except ValueError:
            return False
        return True

    @staticmethod
    def istz(obj):
        return isinstance(obj, (dtz.tzutc, dtz.tzlocal, dtz.tzfile, dtz.tzoffset))

    @staticmethod
    def timedelta(*args, **kwargs):
        return timedelta(*args, **kwargs)

    ###################
    # Private Methods #
    ###################

    @classmethod
    def _get_frames(cls, attr):
        if attr in cls._ATTRS:
            return attr, f'{attr}s', 1
        elif attr in cls._ATTR_MAP:
            return cls._ATTR_MAP[attr], attr, 1
        elif attr in ['week', 'weeks']:
            return 'week', 'weeks', 1
        elif attr in ['quarter', 'quarters']:
            return 'quarter', 'months', 3
        supported = ', '.join(f'{a}(s)' for a in cls._ATTRS + ['week', 'quarter'])
        raise ValueError(f'timeframe not supported: {attr!r} not in {supported}')
