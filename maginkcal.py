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


from typings_google_calendar_api.calendars import Calendar
from config import Config
from gcal.google_auth import GoogleAuth
from gcal.google_calendar import GoogleCalendar
from gcal.google_tasks import GoogleTasks
from gcal.inkal_event import InkalEvent
from gcal.inkal_task import InkalTask
from power.pi_sugar import PiSugar
from pytz import timezone
from pytz.tzinfo import DstTzInfo
from display_data import DisplayData
from render.render import ChromeRenderer
from typing import Any, List
from typings_google_calendar_api.events import Event

import datetime as dt
import json
import logging
import sys
import os


from PIL import Image

image_dir = '/home/pi/inkal/render'


def main():
    # Basic configuration settings (user replaceable)
    configFile = open("config.json")
    config: Config = json.load(configFile)


    #  READ CONFIGURATION

    displayTZ: DstTzInfo = timezone(
        config["displayTZ"]
    )  # list of timezones - print(pytz.all_timezones)
    thresholdHours = config[
        "thresholdHours"
    ]  # considers events updated within last 12 hours as recently updated
    maxEventsPerDay = config[
        "maxEventsPerDay"
    ]  # limits number of events to display (remainder displayed as '+X more')
    isShutdownOnComplete = config[
        "isShutdownOnComplete"
    ]  # set to true to conserve power, false if in debugging mode
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
    # calendars: List[str] = config["calendars"]  # Google calendar ids
    accounts: List[Any] = config["accounts"]  # Google accounts to authenticate

    is_client = config["is_client"]
    is_server = not is_client

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
        if (is_client):
            sync_time(logger)

    except Exception as e:
        logger.error(e)

    if is_server:
        try:
            currDatetime = dt.datetime.now(displayTZ)

            currDate = currDatetime.date()
            calStartDate = currDate - dt.timedelta(
                days=(currDate.weekday() % 7)
            )
            calEndDate = calStartDate + dt.timedelta(days=(4 * 7 - 1))
            calStartDatetime = displayTZ.localize(
                dt.datetime.combine(calStartDate, dt.datetime.min.time())
            )
            calEndDatetime = displayTZ.localize(
                dt.datetime.combine(calEndDate, dt.datetime.max.time())
            )

            start: dt.datetime = dt.datetime.now()

            tasks: List[InkalTask] = []
            events: List[InkalEvent] = []
            for account in accounts:
                calendars: List[Calendar] = config["accounts"][account]["calendars"]
                google_auth = GoogleAuth()
                calendar_service, task_service = google_auth.authenticate(account)
                google_calendar = GoogleCalendar(calendar_service)
                google_tasks = GoogleTasks(task_service)

                account_tasks: List[InkalTask] = google_tasks.retrieve_tasks(
                    calStartDatetime - dt.timedelta(weeks=3),
                    calEndDatetime,
                    displayTZ,
                    thresholdHours,
                )

                account_events: List[Event] = google_calendar.retrieve_events(
                    calendars=calendars,
                    startDatetime=calStartDatetime,
                    endDatetime=calEndDatetime,
                    localTZ=displayTZ,
                    thresholdHours=thresholdHours,
                )
                logger.info("Calendar events retrieved in " + str(dt.datetime.now() - start))

                tasks.extend(account_tasks)
                events.extend(account_events)

            render_data: DisplayData = {
                "calStartDate": calStartDate,
                "events": events,
                "lastRefresh": currDatetime,
                "maxEventsPerDay": maxEventsPerDay,
                "today": currDate,
                "tasks": tasks
            } 

            renderer = ChromeRenderer(imageWidth, imageHeight, rotateAngle)
            black_image, red_image = renderer.render(render_data)
        except Exception as e:
            logger.error(e)

    if is_client:
        copy_image()

        from display.display import EInkDisplay

        eInkDisplay = EInkDisplay(screenWidth, screenHeight)

        red_image_path = os.path.join(image_dir, 'red_image.png')
        black_image_path = os.path.join(image_dir, 'black_image.png')
        red_image = Image.open(red_image_path)
        black_image = Image.open(black_image_path)
        # if currDate.weekday() == 0:
        #     # calibrate display once a week to prevent ghosting
        #     eInkDisplay.calibrate(cycles=0)  # to calibrate in production
        eInkDisplay.display(black_image, red_image)
        # eInkDisplay.sleep()

        pi_sugar = PiSugar()
        battery_level = pi_sugar.get_battery()
        logger.info("Battery level at end: {:.3f}".format(battery_level))


    logger.info("Completed daily calendar update")
    
    if is_client:
        logger.info(
            "Checking if configured to shutdown safely - Current hour: {}".format(
                dt.datetime.now(displayTZ).hour
            )
        )
        logger.info("Shutting down safely.")
        os.system("sudo shutdown -h now")

def copy_image():
    black_image_path = os.path.join(image_dir, 'black_image.png')
    red_image_path = os.path.join(image_dir, 'red_image.png')
    os.system(f"scp zero1:{black_image_path} {black_image_path}")
    os.system(f"scp zero1:{red_image_path} {red_image_path}")

def sync_time(logger: logging.Logger, displayTZ: DstTzInfo) -> None:
    pi_sugar = PiSugar()
    pi_sugar.sync_time()
    battery_level: float = pi_sugar.get_battery()
    logger.info("Battery level at start: {:.3f}".format(battery_level))
    currDatetime = dt.datetime.now(displayTZ)
    logger.info("Time synchronised to {}".format(currDatetime))

if __name__ == "__main__":
    main()
