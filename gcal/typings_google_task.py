from enum import Enum
from typing import Any, TypedDict, List, Optional


class Link(TypedDict):
    type: str
    description: str
    link: str

class AssignmentInfo(TypedDict):
    linkToTask: str
    surfaceType: Any
    driveResourceInfo: Optional[Any]
    spaceInfo: Optional[Any]

class TaskStatus(Enum):
    NEEDS_ACTION = "needsAction"
    COMPLETED = "completed"

class GoogleTask(TypedDict):
    assignmentInfo: AssignmentInfo
    completed: Optional[str]
    deleted: bool
    due: Optional[str]
    etag: str
    hidden: bool
    id: str
    kind: str
    links: List[Link]
    notes: Optional[str]
    parent: Optional[str]
    position: str
    selfLink: str
    status: TaskStatus
    title: str
    updated: str
    webViewLink: str