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
from PIL.Image import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from time import sleep
from typing import Dict, List, Tuple
from typings_google_calendar_api.events import Event

import datetime as dt
import logging
import pathlib
import calendar


from display_data import DisplayData
from render.html_generator import HtmlGenerator


class ChromeRenderer:

    def __init__(self, width: int, height: int, angle: int):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle
        self.html_generator = HtmlGenerator()

    
    def render(self, data: DisplayData, events: List[Event]) -> Tuple[Image, Image]:
        # first setup list to represent the 4 weeks in our calendar
        cal_list: List[List[Dict]] = []
        for i in range(28):
            cal_list.append([])

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

        battery_text = self.html_generator.get_battery_text(data)

        grid = self.html_generator.get_grid_html(cal_list, data)
                    
        htmlFile = open(self.currPath + '/calendar.html', "w")
        htmlFile.write(calendar_template.format(month=month_name, battText=battery_text, grid=grid))
        htmlFile.close()
        htmlFileUri = 'file://' + self.currPath + '/calendar.html'

        black_image, red_image = self.get_black_red_images(htmlFileUri)

        return black_image, red_image
    
    def get_black_red_images(self, htmlFile: str) -> Tuple[Image, Image]:
        """This function captures a screenshot of the calendar,
        processes the image to extract the grayscale and red"""

        png_path = self.chrome_render_calendar_png(htmlFile)

        self.logger.info('Screenshot captured and saved to file.')

        red_img = PIL.Image.open(png_path)
        red_pixels = red_img.load()
        black_img = PIL.Image.open(png_path)
        black_pixels = black_img.load()

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
    
    def chrome_render_calendar_png(self, htmlFile: str) -> str:
        opts = Options()
        opts.binary_location = '/usr/bin/chromium-browser'
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument('--force-device-scale-factor=1')
        driver = webdriver.Chrome(options=opts)
        service = webdriver.ChromeService(executable_path='/usr/bin/chromedriver')
        self.set_viewport_size(driver=driver, service=service)
        driver.get(htmlFile)
        sleep(1)
        png_path = self.currPath + '/calendar.png'
        driver.get_screenshot_as_file(png_path)
        driver.quit()
        return png_path    

    def set_viewport_size(self, driver: webdriver.Chrome) -> None:
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

        delta: dt.timedelta = eventDate - startDate
        return delta.days
