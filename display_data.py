from typing import List, Literal, TypedDict
from datetime import datetime


class DisplayData(TypedDict):
    """
    Data to be rendered on the E-Ink display.
    """
    batteryDisplayMode: Literal[0, 1, 2]
    batteryLevel: int
    calStartDate: datetime
    dayOfWeekText: str
    events: List[str]
    is24hour: bool
    lastRefresh: datetime
    maxEventsPerDay: int
    today: datetime
    weekStartDay: str