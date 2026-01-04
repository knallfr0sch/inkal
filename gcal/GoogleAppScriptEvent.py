from typing import TypedDict

class GoogleAppScriptEvent(TypedDict, total=False):
	calendarName: str
	id: str
	title: str
	start: str
	end: str
	description: str
	location: str