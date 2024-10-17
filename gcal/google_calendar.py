#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is where we retrieve events from the Google Calendar. Before doing so, make sure you have both the
credentials.json and token.pickle in the same folder as this file. If not, run quickstart.py first.
"""

from __future__ import print_function
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List
from typings_google_calendar_api.calendars import Calendar
from typings_google_calendar_api.events import Event as GoogleEvent
from pytz.tzinfo import DstTzInfo


import datetime as dt
import logging
import os.path
import pathlib
import pickle

from gcal.event import InkalEvent


class GoogleCalendar:

    def __init__(self):
        self.logger = logging.getLogger("maginkcal")
        # Initialise the Google Calendar using the provided credentials and token
        SCOPES = ["https/www.googleapis.com/auth/calendar.readonly"]
        self.currPath = str(pathlib.Path(__file__).parent.absolute())

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.currPath + "/token.pickle"):
            with open(self.currPath + "/token.pickle", "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.currPath + "/credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.currPath + "/token.pickle", "wb") as token:
                pickle.dump(creds, token)

        self.googleApi = build(
            "calendar", "v3", credentials=creds, cache_discovery=False
        )

    def list_calendars(self) -> List[Calendar]:
        """
        Lists all the calendars that the user has access to.
        """

        self.logger.info("Getting list of calendars")
        calendars_result = self.googleApi.calendarList().list().execute()
        calendars: List[Calendar] = calendars_result.get("items", [])
        if not calendars:
            self.logger.info("No calendars found.")
        for calendar in calendars:
            summary = calendar["summary"]
            cal_id = calendar["id"]
            self.logger.info("%s\t%s" % (summary, cal_id))

        return calendars

    
    def retrieve_events(
        self,
        calendars: List[Calendar],
        startDatetime: dt.datetime,
        endDatetime: dt.datetime,
        localTZ: DstTzInfo,
        thresholdHours: int,
    ) -> List[InkalEvent]:
        """
        Call the Google Calendar API and return a list of events that fall within the specified dates
        """
        eventList: List[InkalEvent] = []

        minTimeStr: str = startDatetime.isoformat()
        maxTimeStr: str = endDatetime.isoformat()

        self.logger.info(
            "Retrieving events between " + minTimeStr + " and " + maxTimeStr + "..."
        )

        # Call the Calendar API
        google_events: List[GoogleEvent] = []
        for cal in calendars:
            event_list: List[GoogleEvent] = self.googleApi.events().list(
                calendarId=cal,
                timeMin=minTimeStr,
                timeMax=maxTimeStr,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            item_list = event_list.get("items", [])
            google_events.extend(item_list)


        if not google_events:
            self.logger.info("No upcoming events found.")
        for google_event in google_events:
            inkal_event = self.to_inkal_event(google_event, localTZ, thresholdHours)

            eventList.append(inkal_event)

        # We need to sort eventList because the event will be sorted in "calendar order" instead of hours order
        # TODO: improve because of double cycle for now is not much cost
        eventList = sorted(eventList, key=lambda k: k["startDatetime"])
        return eventList
    
    def to_inkal_event(self, google_event: GoogleEvent, localTZ, thresholdHours) -> InkalEvent:
        """
        Convert a Google Event to an InkalEvent
        """
        inkal_event: InkalEvent = {}
        inkal_event["summary"] = google_event["summary"]

        if google_event["start"].get("dateTime") is None:
            inkal_event["allday"] = True
            inkal_event["startDatetime"] = self.to_datetime(
                google_event["start"].get("date"), localTZ
            )
        else:
            inkal_event["allday"] = False
            inkal_event["startDatetime"] = self.to_datetime(
                google_event["start"].get("dateTime"), localTZ
            )

        if google_event["end"].get("dateTime") is None:
            inkal_event["endDatetime"] = self.adjust_end_time(
                self.to_datetime(google_event["end"].get("date"), localTZ), localTZ
            )
        else:
            inkal_event["endDatetime"] = self.adjust_end_time(
                endTime=self.to_datetime(
                    isoDatetime=google_event["end"].get("dateTime"), localTZ=localTZ
                ),
                localTZ=localTZ,
            )

        inkal_event["updatedDatetime"] = self.to_datetime(google_event["updated"], localTZ)
        inkal_event["isUpdated"] = self.is_recently_updated(
            updatedTime=inkal_event["updatedDatetime"], thresholdHours=thresholdHours
        )
        inkal_event["isMultiday"] = self.is_multiday(
            inkal_event["startDatetime"], inkal_event["endDatetime"]
        )

        return inkal_event


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

    def adjust_end_time(self, endTime: dt.datetime, localTZ: DstTzInfo) -> dt.datetime:
        """
        check if end time is at 00:00 of next day, if so set to max time for day before
        """
        if endTime.hour == 0 and endTime.minute == 0 and endTime.second == 0:
            newEndtime: dt.datetime = localTZ.localize(
                dt.datetime.combine(
                    endTime.date() - dt.timedelta(days=1), dt.datetime.max.time()
                )
            )
            return newEndtime
        else:
            return endTime

    def is_multiday(self, start, end) -> bool:
        """
        check if event stretches across multiple days
        """
        return start.date() != end.date()
