from typing import TypedDict
import datetime as dt


class InkalEvent(TypedDict):
    """
    Subset of Google Calendar event
    """

    summary: str
    allday: bool
    isMultiday: bool
    isUpdated: bool
    updatedDatetime: dt.datetime
    startDatetime: dt.datetime
    endDatetime: dt.datetime
             

