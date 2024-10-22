from typing import Optional, TypedDict
import datetime as dt

class InkalTask(TypedDict):
    """
    Subset of Google Calendar task
    """

    kind: str  # 'tasks#task'

    account: str
    due: Optional[dt.date]
    title: str

    updated: dt.datetime
    isUpdated: bool

    isCompleted: bool