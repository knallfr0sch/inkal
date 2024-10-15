from typing import List
from typings_google_calendar_api.calendars import Calendar

from gcal.google_calendar import GoogleCalendar


def test_get_calendars() -> None:
    """
    Tests Google Authentication
    """

    googleCalendar = GoogleCalendar()
    calendars: List[Calendar] = googleCalendar.list_calendars()
    assert len(calendars) > 0

