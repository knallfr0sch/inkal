import logging
import pathlib

import datetime as dt
from typing import List
from pytz.tzinfo import DstTzInfo

from gcal.inkal_task import InkalTask
from gcal.typings_google_task import GoogleTask


class GoogleTasks:
    """Google Tasks API"""

    def __init__(self, task_service):
        self.logger = logging.getLogger("maginkcal")
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.task_service = task_service

    def retrieve_tasks(
            self,
            startDatetime: dt.datetime,
            endDatetime: dt.datetime,
            localTZ: DstTzInfo,
            thresholdHours: int,
    ) -> List[InkalTask]:
        taskList: List[InkalTask] = []

        minTimeStr: str = startDatetime.isoformat()
        maxTimeStr: str = endDatetime.isoformat()

        # There will only be one task list
        task_lists = self.task_service.tasklists().list(maxResults=10).execute().get('items', [])

        # For each task list, get the tasks
        google_tasks: List[GoogleTask] = []
        for task_list in task_lists:
            tasks = self.task_service.tasks().list(
                tasklist=task_list['id'],
                dueMin=minTimeStr,
                dueMax=maxTimeStr,
                ).execute()
            google_tasks.extend(tasks.get('items', []))

        # Convert Google Tasks to Inkal Tasks
        for google_task in google_tasks:
            inkal_task = self.to_inkal_task(google_task, localTZ, thresholdHours)

            taskList.append(inkal_task)

        return taskList
    
    def to_inkal_task(self, google_task, localTZ: dt.datetime, thresholdHours: dt.datetime) -> InkalTask:
        """
        Convert a Google Task to an InkalTask
        """
        inkal_task: InkalTask = {}

        inkal_task["title"] = google_task["title"]

        inkal_task["kind"] = "tasks#task"

        inkal_task["isCompleted"] = "completed" in google_task
        inkal_task["due"] = self.to_date(google_task.get("due", None))


        inkal_task["updatedDatetime"] = self.to_datetime(google_task["updated"], localTZ)
        inkal_task["isUpdated"] = self.is_recently_updated(
            updatedTime=inkal_task["updatedDatetime"], thresholdHours=thresholdHours
        )

        return inkal_task
    
    def to_date(self, isoDate: str) -> dt.date:
        if isoDate:
            return dt.datetime.fromisoformat(isoDate).date()
        return None
    
    def to_datetime(self, isoDatetime, localTZ) -> dt.datetime:
        # replace Z with +00:00 is a workaround until datetime library decides what to do with the Z notation
        toDatetime = dt.datetime.fromisoformat(isoDatetime.replace("Z", "+00:00"))
        return toDatetime.astimezone(localTZ)
    
    def is_recently_updated(self, updatedTime: dt.datetime, thresholdHours: int) -> bool:
        # consider events updated within the past X hours as recently updated
        utcnow: dt.datetime = dt.datetime.now(dt.timezone.utc)
        diff: float = (
            utcnow - updatedTime
        ).total_seconds() / 3600  # get difference in hours
        return diff < thresholdHours
