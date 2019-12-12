from datetime import datetime, timedelta


Duration = timedelta
Time = datetime


def hours(hrs: int) -> Duration:
    return Duration(hours=hrs)
