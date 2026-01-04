from turtle import update
from typing import TypedDict

class GoogleAppScriptTask(TypedDict, total=False):
	listName: str
	title: str
	notes: str
	due: str
	status: str
	updated: str
