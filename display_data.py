from typing import Any, List, Literal, TypedDict
from datetime import datetime

from gcal.inkal_event import InkalEvent
from gcal.inkal_task import InkalTask


class DisplayData(TypedDict):
    """
    Data to be rendered on the E-Ink display.
    """
    batteryDisplayMode: Literal[0, 1, 2]
    batteryLevel: int
    calStartDate: datetime
    events: List[InkalEvent]
    lastRefresh: datetime
    maxEventsPerDay: int
    today: datetime
    tasks: List[InkalTask]
