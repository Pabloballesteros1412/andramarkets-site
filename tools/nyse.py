"""NYSE trading calendar, from the exchange's published holiday schedule.

Kept as a table so the site needs no third-party calendar package. Years not
listed here are unknown: the importer holds any note dated in them for review
instead of guessing. Add the next year's dates from
https://www.nyse.com/markets/hours-calendars each December.
"""
import datetime as dt

HOLIDAYS = {
    2025: ["01-01", "01-09", "01-20", "02-17", "04-18", "05-26", "06-19", "07-04",
           "09-01", "11-27", "12-25"],
    2026: ["01-01", "01-19", "02-16", "04-03", "05-25", "06-19", "07-03", "09-07",
           "11-26", "12-25"],
    2027: ["01-01", "01-18", "02-15", "03-26", "05-31", "06-18", "07-05", "09-06",
           "11-25", "12-24"],
}

# Sessions that close at 1:00 pm ET instead of 4:00 pm ET.
EARLY_CLOSES = {
    2025: ["07-03", "11-28", "12-24"],
    2026: ["11-27", "12-24"],
    2027: ["11-26"],
}


def _dates(table, year):
    return {dt.date.fromisoformat(f"{year}-{md}") for md in table.get(year, [])}


def is_trading_day(day: dt.date):
    """True or False, or None when the year is not in the table."""
    if day.year not in HOLIDAYS:
        return None
    return day.weekday() < 5 and day not in _dates(HOLIDAYS, day.year)


def close_time(day: dt.date) -> str:
    return "1:00 pm" if day in _dates(EARLY_CLOSES, day.year) else "4:00 pm"
