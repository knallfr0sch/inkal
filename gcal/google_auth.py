from __future__ import print_function
from typing import Any, Tuple
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import logging
import os.path
import pathlib
import pickle


class GoogleAuth:
    """Authenticate the user with the Google Calendar API."""

    def __init__(self):
        self.logger = logging.getLogger("maginkcal")
        self.currPath = str(pathlib.Path(__file__).parent.absolute())


    def authenticate(self, account: str) -> Tuple[Any, Any]:
        """-> [Calendar, Task]"""

        SCOPES: list[str] = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/tasks.readonly"
            ]
        file_path = self.currPath + '/' + account + ".token.pickle"

        creds = None

        # Load token
        if os.path.exists(file_path):
            with open(file_path, "rb") as token:
                creds = pickle.load(token)

        # Authenticate if no token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.currPath + "/credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(file_path, "wb") as token:
                pickle.dump(creds, token)

        calendar_service = build(
            "calendar", "v3", credentials=creds, cache_discovery=False
        )
        task_service = build("tasks", "v1", credentials=creds)
        return calendar_service, task_service
