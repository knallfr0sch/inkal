from typing import TypedDict
import datetime as dt


class InkalEvent(TypedDict):
    """
    Subset of Google Calendar event
    """

    kind: str # 'calendar#event'

    account: str
    allday: bool
    isMultiday: bool
    isUpdated: bool
    summary: str
    updatedDatetime: dt.datetime
    startDatetime: dt.datetime
    endDatetime: dt.datetime
             

