import datetime, re, pytz
from django.utils.timezone import utc


def utcnow():
    """
    Simply returns a datetime of the current instant in UTC.

    Returns:
        datetime
    """
    return datetime.datetime.utcnow().replace(tzinfo=utc)


def utc_from_string(input=None, tz=None):
    """

    Args:
        input (str): A date string from a user.
        tz (pytz): An instance of pytz from the user.

    Returns:
        datetime in utc.
    """
    if not input:
        raise ValueError("No time string entered!")
    now = utcnow()
    cur_year = now.strftime('%Y')
    split_time = input.split(' ')
    if len(split_time) == 3:
        input = "{0} {1} {2} {3}".format(split_time[0], split_time[1], split_time[2], cur_year)
    elif len(split_time) == 4:
        pass
    else:
        raise ValueError("Time must be entered in a 24-hour format such as: %s" % now.strftime('%b %d %H:%H'))
    try:
        local = datetime.datetime.strptime(input, '%b %d %H:%M %Y')
    except ValueError:
        raise ValueError("Time must be entered in a 24-hour format such as: %s" % now.strftime('%b %d %H:%H'))
    local_tz = tz.localize(local)
    return local_tz.astimezone(utc)


def duration_from_string(time_string):
    """
    Take a string and derive a datetime timedelta from it.

    Args:
        time_string (string): This is a string from user-input. The intended format is, for example: "5d 2w 90s" for
                            'five days, two weeks, and ninety seconds.' Invalid sections are ignored.

    Returns:
        timedelta

    """
    time_string = time_string.split(" ")
    seconds = 0
    minutes = 0
    hours = 0
    days = 0
    weeks = 0

    for interval in time_string:
        if re.match(r'^[\d]+s$', interval.lower()):
            seconds =+ int(interval.lower().rstrip("s"))
        elif re.match(r'^[\d]+m$', interval):
            minutes =+ int(interval.lower().rstrip("m"))
        elif re.match(r'^[\d]+h$', interval):
            hours =+ int(interval.lower().rstrip("h"))
        elif re.match(r'^[\d]+d$', interval):
            days =+ int(interval.lower().rstrip("d"))
        elif re.match(r'^[\d]+w$', interval):
            weeks =+ int(interval.lower().rstrip("w"))
        elif re.match(r'^[\d]+y$', interval):
            days =+ int(interval.lower().rstrip("y")) * 365
        else:
            raise ValueError("Could not convert section '%s' to a time duration." % interval)

    return datetime.timedelta(days, seconds, 0, 0, minutes, hours, weeks)


def from_unixtimestring(secs):
    try:
        convert = datetime.datetime.fromtimestamp(int(secs)).replace(tzinfo=pytz.utc)
    except ValueError:
        return None
    return convert