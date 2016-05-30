from datetime import datetime, timedelta

import pytz
import random


def random_datetime():
    return datetime(2016, 5, 11, tzinfo=pytz.utc) + timedelta(hours=random.randint(0, 500))