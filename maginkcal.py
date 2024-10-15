#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This project is designed for the WaveShare 12.48" eInk display. Modifications will be needed for other displays,
especially the display drivers and how the image is being rendered on the display. Also, this is the first project that
I posted on GitHub so please go easy on me. There are still many parts of the code (especially with timezone
conversions) that are not tested comprehensively, since my calendar/events are largely based on the timezone I'm in.
There will also be work needed to adjust the calendar rendering for different screen sizes, such as modifying of the
CSS stylesheets in the "render" folder.
"""


from config import Config
from gcal.google_calendar import GoogleCalendar
from power.pi_sugar import PiSugar
from pytz import timezone
from display_data import DisplayData
from render.render import ChromeRenderer
from typing import List
from typings_google_calendar_api.events import Event

import datetime as dt
import json
import logging
import sys


def main():
    # Basic configuration settings (user replaceable)
    configFile = open("config.json")
    config: Config = json.load(configFile)

    displayTZ: timezone = timezone(
        config["displayTZ"]
    )  # list of timezones - print(pytz.all_timezones)
    thresholdHours = config[
        "thresholdHours"
    ]  # considers events updated within last 12 hours as recently updated
    maxEventsPerDay = config[
        "maxEventsPerDay"
    ]  # limits number of events to display (remainder displayed as '+X more')
    isDisplayToScreen = config[
        "isDisplayToScreen"
    ]  # set to true when debugging rendering without displaying to screen
    isShutdownOnComplete = config[
        "isShutdownOnComplete"
    ]  # set to true to conserve power, false if in debugging mode
    batteryDisplayMode = config[
        "batteryDisplayMode"
    ]  # 0: do not show / 1: always show / 2: show when battery is low
    weekStartDay = config["weekStartDay"]  # Monday = 0, Sunday = 6
    dayOfWeekText = config["dayOfWeekText"]  # Monday as first item in list
    screenWidth = config[
        "screenWidth"
    ]  # Width of E-Ink display. Default is landscape. Need to rotate image to fit.
    screenHeight = config[
        "screenHeight"
    ]  # Height of E-Ink display. Default is landscape. Need to rotate image to fit.
    imageWidth = config[
        "imageWidth"
    ]  # Width of image to be generated for display.
    imageHeight = config[
        "imageHeight"
    ]  # Height of image to be generated for display.
    rotateAngle = config[
        "rotateAngle"
    ]  # If image is rendered in portrait orientation, angle to rotate to fit screen
    calendars: List[str] = config["calendars"]  # Google calendar ids
    is24hour: bool = config["is24h"]  # set 24 hour time

    # Create and configure logger
    logging.basicConfig(
        filename="logfile.log",
        format="%(asctime)s %(levelname)s - %(message)s",
        filemode="a",
    )
    logger = logging.getLogger("maginkcal")
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)
    logger.info("Starting daily calendar update")

    try:
        # Establish current date and time information
        # Note: For Python datetime.weekday() - Monday = 0, Sunday = 6
        # For this implementation, each week starts on a Sunday and the calendar begins on the nearest elapsed Sunday
        # The calendar will also display 5 weeks of events to cover the upcoming month, ending on a Saturday
        pi_sugar = PiSugar()
        # powerService.sync_time()
        battery_level = pi_sugar.get_battery()
        logger.info("Battery level at start: {:.3f}".format(battery_level))

        currDatetime = dt.datetime.now(displayTZ)
        logger.info("Time synchronised to {}".format(currDatetime))
        currDate = currDatetime.date()
        calStartDate = currDate - dt.timedelta(
            days=((currDate.weekday() + (7 - weekStartDay)) % 7)
        )
        calEndDate = calStartDate + dt.timedelta(days=(5 * 7 - 1))
        calStartDatetime = displayTZ.localize(
            dt.datetime.combine(calStartDate, dt.datetime.min.time())
        )
        calEndDatetime = displayTZ.localize(
            dt.datetime.combine(calEndDate, dt.datetime.max.time())
        )

        # Using Google Calendar to retrieve all events within start and end date (inclusive)
        start: dt.datetime = dt.datetime.now()
        googleCalendar = GoogleCalendar()
        googleCalendar.list_calendars()
        events: List[Event] = googleCalendar.retrieve_events(
            calendars=calendars,
            startDatetime=calStartDatetime,
            endDatetime=calEndDatetime,
            localTZ=displayTZ,
            thresholdHours=thresholdHours,
        )
        logger.info("Calendar events retrieved in " + str(dt.datetime.now() - start))

        render_data: DisplayData = {
            "batteryDisplayMode": batteryDisplayMode,
            "batteryLevel": battery_level,
            "calStartDate": calStartDate,
            "dayOfWeekText": dayOfWeekText,
            "events": events,
            "is24hour": is24hour,
            "lastRefresh": currDatetime,
            "maxEventsPerDay": maxEventsPerDay,
            "today": currDate,
            "weekStartDay": weekStartDay,
        } 

        renderer = ChromeRenderer(imageWidth, imageHeight, rotateAngle)
        black_image, red_image = renderer.render(render_data, events)

        if isDisplayToScreen:
            from display.display import EInkDisplay

            eInkDisplay = EInkDisplay(screenWidth, screenHeight)
            if currDate.weekday() == weekStartDay:
                # calibrate display once a week to prevent ghosting
                eInkDisplay.calibrate(cycles=0)  # to calibrate in production
            eInkDisplay.update(black_image, red_image)
            eInkDisplay.sleep()

        battery_level = pi_sugar.get_battery()
        logger.info("Battery level at end: {:.3f}".format(battery_level))

    except Exception as e:
        logger.error(e)

    logger.info("Completed daily calendar update")

    logger.info(
        "Checking if configured to shutdown safely - Current hour: {}".format(
            currDatetime.hour
        )
    )
    if isShutdownOnComplete:
        # implementing a failsafe so that we don't shutdown when debugging
        # checking if it's 6am in the morning, which is the time I've set PiSugar to wake and refresh the calendar
        # if it is 6am, shutdown the RPi. if not 6am, assume I'm debugging the code, so do not shutdown
        if currDatetime.hour == 6:
            logger.info("Shutting down safely.")
            import os

            os.system("sudo shutdown -h now")


if __name__ == "__main__":
    main()
