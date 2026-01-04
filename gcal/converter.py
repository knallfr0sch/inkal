from gcal.GoogleAppScriptEvent import GoogleAppScriptEvent
from gcal.inkal_event import InkalEvent

from typing import List, Dict, Any
import datetime as dt

from gcal import GoogleAppScriptTask
from gcal.inkal_task import InkalTask

class Converter:
    """
    Converter for Google Calendar/Tasks API JSON data to InkalEvent and InkalTask objects.
    """

    @staticmethod
    def to_inkal_events(events: List[GoogleAppScriptEvent]) -> List[InkalEvent]:
        """
        Convert a list of calendar event dicts (from test-events.json) to InkalEvent objects.
        """
        inkal_events = []
        for event in events:
            inkal_event: InkalEvent = {
                "kind": "calendar#event",
                "summary": event.get("title", ""),
                # "location": event.get("location", ""),
            }

            # Parse start and end datetimes
            start_str = event.get("start")
            end_str = event.get("end")
            if start_str:
                try:
                    inkal_event["startDatetime"] = dt.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                except Exception:
                    pass
                    # inkal_event["startDatetime"] = start_str
            else:
                inkal_event["startDatetime"] = None
            if end_str:
                try:
                    inkal_event["endDatetime"] = dt.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                except Exception:
                    pass
                    # inkal_event["endDatetime"] = end_str
            else:
                inkal_event["endDatetime"] = None

            # All-day event detection
            inkal_event["allday"] = (
                isinstance(inkal_event["startDatetime"], dt.datetime)
                and inkal_event["startDatetime"].hour == 0
                and inkal_event["startDatetime"].minute == 0
                and inkal_event["startDatetime"].second == 0
                and isinstance(inkal_event["endDatetime"], dt.datetime)
                and inkal_event["endDatetime"].hour == 0
                and inkal_event["endDatetime"].minute == 0
                and inkal_event["endDatetime"].second == 0
            )

            # Multiday event detection
            if (
                isinstance(inkal_event["startDatetime"], dt.datetime)
                and isinstance(inkal_event["endDatetime"], dt.datetime)
            ):
                inkal_event["isMultiday"] = inkal_event["startDatetime"].date() != inkal_event["endDatetime"].date()
            else:
                inkal_event["isMultiday"] = False

            # No updatedDatetime/isUpdated in test-events.json, so set to None/False
            updated_str = event.get("updated", "")
            inkal_event["updatedDatetime"] =  dt.datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            inkal_event["isUpdated"] = False

            inkal_events.append(inkal_event)
        return inkal_events

    @staticmethod
    def to_inkal_tasks(tasks: List[GoogleAppScriptTask.GoogleAppScriptTask]) -> List[InkalTask]:
        """
        Convert a list of task dicts (from test-events.json) to InkalTask objects.
        """
        inkal_tasks = []
        for task in tasks:
            inkal_task: InkalTask = {
                "kind": "tasks#task",
                "title": task.get("title", ""),
            }
            due_str = task.get("due")
            if due_str:
                try:
                    inkal_task["due"] = dt.datetime.fromisoformat(due_str.replace("Z", "+00:00")).date()
                except Exception:
                    pass
                    # inkal_task["due"] = due_str
            else:
                inkal_task["due"] = None

            # Completed status
            inkal_task["isCompleted"] = task.get("status", "") == "completed"

            # No updatedDatetime/isUpdated in test-events.json, so set to None/False
            updated_str = task.get("updated", "")
            
            try:
                inkal_task["updated"] = dt.datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            except Exception:
                pass

            inkal_task["isUpdated"] = False

            inkal_tasks.append(inkal_task)
        return inkal_tasks