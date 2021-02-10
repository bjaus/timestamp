import re
from . import Timestamp


class TSXlate:
    _rexlate = re.compile(r'^(?P<num>[\d]*)[-]?(?P<frame>[minute|hour|day|week|month|year]*[s]?)$')
    _redatetime = re.compile(
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
