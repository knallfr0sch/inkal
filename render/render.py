#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot. This screenshot will then be processed
to extract the grayscale and red portions, which are then sent to the eInk display for updating.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can better delink the generation of the
calendar and refreshing of the eInk display. In the future, I might choose to generate the calendar on a separate
RPi device, while using a ESP32 or PiZero purely to just retrieve the image from a file host and update the screen.
"""

import PIL
from datetime import timedelta
from PIL.Image import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from time import sleep
from typing import Dict, List, Literal, Tuple
from typings_google_calendar_api.events import Event

import datetime as dt
import logging
import pathlib
import calendar

from htmlgenerator import LI, OL, render, DIV

from display_data import DisplayData

BatteryText = Literal[
    'batteryHide',
    'battery0'
    'battery20',
    'battery40',
    'battery60',
    'battery80',
    ]

class ChromeRenderer:

    def __init__(self, width: int, height: int, angle: int):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle

    
    def render(self, data: DisplayData, events: List[Event]) -> Tuple[Image, Image]:
        # first setup list to represent the 4 weeks in our calendar
        cal_list: List[List[Dict]] = []
        for i in range(28):
            cal_list.append([])

        # retrieve calendar configuration
        maxEventsPerDay = data['maxEventsPerDay']

        # for each item in the eventList, add them to the relevant day in our calendar list
        for event in events:
            idx = self.get_day_in_cal(data['calStartDate'], event['startDatetime'].date())
            if idx >= 0 and idx < len(cal_list):
                cal_list[idx].append(event)
            if event['isMultiday']:
                idx = self.get_day_in_cal(data['calStartDate'], event['endDatetime'].date())
                if idx < len(cal_list):
                    cal_list[idx].append(event)

        # Read html template
        with open(self.currPath + '/calendar_template.html', 'r') as file:
            calendar_template = file.read()

        # Insert month header
        month_name = calendar.month_name[data['today'].month]

        battery_text = self.get_battery_text(data)

        # Populate the day of week row
        cal_days_of_week = self.get_week_days_html()

        # Populate the date and events
        cal_events_text = self.get_event_html(cal_list, data, maxEventsPerDay)
                    
        htmlFile = open(self.currPath + '/calendar.html', "w")
        htmlFile.write(calendar_template.format(month=month_name, battText=battery_text, weekdays=cal_days_of_week,
                                                events=cal_events_text))
        htmlFile.close()
        htmlFileUri = 'file://' + self.currPath + '/calendar.html'

        black_image, red_image = self.get_black_red_images(htmlFileUri)

        return black_image, red_image
    
    def get_black_red_images(self, htmlFile: str) -> Tuple[Image, Image]:
        """This function captures a screenshot of the calendar,
        processes the image to extract the grayscale and red"""

        opts = Options()
        opts.binary_location = '/usr/bin/chromium-browser'
        # opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument('--force-device-scale-factor=1')
        driver = webdriver.Chrome(options=opts)
        self.set_viewport_size(driver=driver)
        driver.get(htmlFile)
        sleep(1)
        driver.get_screenshot_as_file(self.currPath + '/calendar.png')
        driver.quit()

        self.logger.info('Screenshot captured and saved to file.')

        red_img = PIL.Image.open(self.currPath + '/calendar.png')  # get image)
        red_pixels = red_img.load()  # create the pixel map
        black_img = PIL.Image.open(self.currPath + '/calendar.png')  # get image)
        black_pixels = black_img.load()  # create the pixel map

        for i in range(red_img.size[0]):  # loop through every pixel in the image
            for j in range(red_img.size[1]): # since both bitmaps are identical, cycle only once and not both bitmaps
                if red_pixels[i, j][0] <= red_pixels[i, j][1] and red_pixels[i, j][0] <= red_pixels[i, j][2]:  # if is not red
                    red_pixels[i, j] = (255, 255, 255)  # change it to white in the red image bitmap

                elif black_pixels[i, j][0] > black_pixels[i, j][1] and black_pixels[i, j][0] > black_pixels[i, j][2]:  # if is red
                    black_pixels[i, j] = (255, 255, 255)  # change to white in the black image bitmap

        red_img: Image = red_img.rotate(self.rotateAngle, expand=True)
        black_img: Image = black_img.rotate(self.rotateAngle, expand=True)

        self.logger.info('Image colours processed. Extracted grayscale and red images.')
        return black_img, red_img
    
    def get_battery_text(self, data: DisplayData) -> BatteryText:
        displayMode = data['batteryDisplayMode']

        # Insert battery icon
        # batteryDisplayMode - 0: do not show / 1: always show / 2: show when battery is low
        level = data['batteryLevel']
        if displayMode == 0:
            text = 'batteryHide'
        elif displayMode == 1:
            if level >= 80:
                text = 'battery80'
            elif level >= 60:
                text = 'battery60'
            elif level >= 40:
                text = 'battery40'
            elif level >= 20:
                text = 'battery20'
            else:
                text = 'battery0'

        elif displayMode == 2 and level < 20.0:
            text = 'battery0'
        elif displayMode == 2 and level >= 20.0:
            text = 'batteryHide'

        return text
    
    def get_week_days_html(self) -> str:
        dayOfWeekText: list[str] = [day[:2].lower() for day in calendar.day_abbr]

        li_elements = []
        for i in range(0, 7):
            li_element = LI(dayOfWeekText[i % 7], _class='font-weight-bold text-uppercase')
            li_elements.append(li_element)
        
        weekday_list = OL(*li_elements, _class="day-names list-unstyled text-center")

        cal_days_of_week = render(weekday_list, {})
        return cal_days_of_week
    
    def get_event_html(self, cal_list: List[List[Dict]], data: Dict, maxEventsPerDay: int) -> str:
        # Populate the date and events
        cal_events_elements = []

        for i in range(len(cal_list)):
            currDate: dt.datetime = data['calStartDate'] + dt.timedelta(days=i)
            dayOfMonth: int = currDate.day
            
            if currDate == data['today']:
                date_div = DIV(str(dayOfMonth), _class="datecircle")
            elif currDate.month != data['today'].month:
                date_div = DIV(str(dayOfMonth), _class="date text-muted")
            else:
                date_div = DIV(str(dayOfMonth), _class="date")
            
            li_element = LI(date_div)
            
            for j in range(min(len(cal_list[i]), maxEventsPerDay)):
                event = cal_list[i][j]
                event_classes = ['event']
                if event['isUpdated']:
                    event_classes.append('text-danger')
                elif currDate.month != data['today'].month:
                    event_classes.append('text-muted')
                
                if event['isMultiday']:
                    if event['startDatetime'].date() == currDate:
                        event_text = '►' + event['summary']
                    else:
                        event_text = '◄' + event['summary']
                elif event['allday']:
                    event_text = event['summary']
                else:
                    event_text = self.get_short_time(event['startDatetime']) + ' ' + event['summary']
                
                event_div = DIV(event_text, _class=' '.join(event_classes))
                li_element.append(event_div)
            
            if len(cal_list[i]) > maxEventsPerDay:
                more_events_div = DIV(str(len(cal_list[i]) - maxEventsPerDay) + ' more', _class="event text-muted")
                li_element.append(more_events_div)
            
            cal_events_elements.append(li_element)
            ordered_list = OL(*cal_events_elements, _class="days list-unstyled")

            
        
        cal_events_html = render(ordered_list, {}) + '\n'
        return cal_events_html

    def set_viewport_size(self, driver: webdriver.Chrome):

        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html: WebElement = driver.find_element(By.TAG_NAME,'html')
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width: int = self.imageWidth + (current_window_size["width"] - inner_width)
        target_height: int = self.imageHeight + (current_window_size["height"] - inner_height)

        driver.set_window_rect(
            width=target_width,
            height=target_height)

    

    def get_day_in_cal(self, startDate: dt.datetime, eventDate: dt.datetime) -> int:
        """
        Returns the index of the day in the calendar list
        """

        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj) -> str:
        """
        Returns a short time string in the format of 'HH:MM'
        """

        return '{}:{:02d}'.format(datetimeObj.hour, datetimeObj.minute)