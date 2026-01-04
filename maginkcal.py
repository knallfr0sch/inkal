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



import requests
from pytz import timezone
from pytz.tzinfo import DstTzInfo
from display_data import DisplayData
from render.render import ChromeRenderer
from power.pi_sugar import PiSugar
from PIL import Image
import datetime as dt
import json
import logging
import sys
import os

image_dir = '/home/pi/inkal/render'



def main():
    # Basic configuration settings (user replaceable)
    with open("config.json") as configFile:
        config = json.load(configFile)

    #  READ CONFIGURATION
    displayTZ: DstTzInfo = timezone(config["displayTZ"])
    thresholdHours = config["thresholdHours"]
    maxEventsPerDay = config["maxEventsPerDay"]
    isShutdownOnComplete = config["isShutdownOnComplete"]
    alarm_interval_minutes = config["alarm_interval_minutes"]
    screenWidth = config["screenWidth"]
    screenHeight = config["screenHeight"]
    imageWidth = config["imageWidth"]
    imageHeight = config["imageHeight"]
    rotateAngle = config["rotateAngle"]

    # Create and configure logger
    logging.basicConfig(
        filename="logfile.log",
        format="%(asctime)s %(levelname)s - %(message)s",
        filemode="a",
    )
    logger = logging.getLogger("maginkcal")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    logger.info("Starting daily calendar update")

    logger.info(msg="Time synchronised")

    try:
        currDatetime = dt.datetime.now(displayTZ)
        currDate = currDatetime.date()
        calStartDate = currDate - dt.timedelta(days=(currDate.weekday() % 7))
        calEndDate = calStartDate + dt.timedelta(days=(4 * 7 - 1))

        start: dt.datetime = dt.datetime.now()

        # Fetch events and tasks from HTTP endpoint
        url = "https://script.google.com/macros/s/AKfycbxdEmpN73rq-hAZRyB8GNnwpgbA339C8qdmE53B_27HqSKGc1JHfCbcIay4GPYWk5k/exec"
        params = {"key": "test"}
        logger.info(f"Fetching events and tasks from {url}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        logger.info("Events and tasks fetched successfully")

        events = data.get("calendars", [])
        tasks = data.get("tasks", [])

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

    logger.info(msg="Data rendered in " + str(dt.datetime.now() - start))

    from display.display import EInkDisplay

    eInkDisplay = EInkDisplay(screenWidth, screenHeight)

    red_image_path = os.path.join(image_dir, 'red_image.png')
    black_image_path = os.path.join(image_dir, 'black_image.png')
    red_image = Image.open(red_image_path)
    black_image = Image.open(black_image_path)
    # if currDate.weekday() == 0:
    #     eInkDisplay.calibrate(cycles=0)
    eInkDisplay.display(black_image, red_image)
    # eInkDisplay.sleep()

    pi_sugar = PiSugar()
    battery_level = pi_sugar.get_battery()
    logger.info("Battery level at end: {:.3f}".format(battery_level))

    logger.info("Completed daily calendar update")
    logger.info(
        "Checking if configured to shutdown safely - Current hour: {}".format(
            dt.datetime.now(displayTZ).hour
        )
    )
    # logger.info("Shutting down safely.")
    # os.system("sudo shutdown -h now")


def sync_time(logger: logging.Logger, displayTZ: DstTzInfo) -> None:
    pi_sugar = PiSugar()
    pi_sugar.sync_time()
    battery_level: float = pi_sugar.get_battery()
    logger.info("Battery level at start: {:.3f}".format(battery_level))
    currDatetime = dt.datetime.now(displayTZ)
    logger.info("Time synchronised to {}".format(currDatetime))

if __name__ == "__main__":
    main()
