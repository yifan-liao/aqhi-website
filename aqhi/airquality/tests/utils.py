from datetime import datetime, timedelta

import pytz
import random


def random_datetime(hour_delta=None):
    if hour_delta is None:
        hour_delta = random.randint(0, 500)
    return datetime(2016, 5, 11, tzinfo=pytz.utc) + timedelta(hours=hour_delta)