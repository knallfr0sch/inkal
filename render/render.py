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

import os
import time
import PIL
from PIL.Image import Image
import subprocess
from typing import List, Tuple

import datetime as dt
import logging
import pathlib
import calendar
from PIL import Image

from display_data import DisplayData
from gcal.inkal_event import InkalEvent
from gcal.inkal_task import InkalTask
from render.html_generator import HtmlGenerator


class ChromeRenderer:

    def __init__(self, width: int, height: int, angle: int):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle
        self.html_generator = HtmlGenerator()

    
    def render(self, data: DisplayData) -> Tuple[Image, Image]:
        """
        Writes calendar.png and extracts [black, red] images
        """

        print(data['events'])
        print(data['tasks'])

        # first setup list to represent the 4 weeks in our calendar
        cal_list: List[List[InkalEvent | InkalTask]] = []
        for _ in range(28):
            cal_list.append([])

        # for each item in the eventList, add them to the relevant day in our calendar list
        for event in data['events']:
            idx = self.get_day_in_cal(data['calStartDate'], event['startDatetime'].date())
            if idx >= 0 and idx < len(cal_list):
                cal_list[idx].append(event)
            if event['isMultiday']:
                idx = self.get_day_in_cal(data['calStartDate'], event['endDatetime'].date())
                if idx < len(cal_list):
                    cal_list[idx].append(event)

        for task in data['tasks']:
            idx = self.get_day_in_cal(data['calStartDate'], task['due'])
            if idx >= 0 and idx < len(cal_list):
                cal_list[idx].append(task)

        # Read html template
        with open(self.currPath + '/calendar_template.html', 'r') as file:
            calendar_template = file.read()

        # Insert month header
        month_name = calendar.month_name[data['today'].month]


        grid = self.html_generator.get_grid_html(cal_list, data)
                    
        htmlFile = open(self.currPath + '/calendar.html', "w")
        htmlFile.write(calendar_template.format(
            month=month_name,
            grid=grid,
            # time=dt.datetime.now().strftime('%H:%M')
        ))
        htmlFile.close()
        htmlFileUri = 'file://' + self.currPath + '/calendar.html'

        black_image, red_image = self.get_black_red_images(htmlFileUri)

        return black_image, red_image
    
    def get_black_red_images(self, htmlFile: str) -> Tuple[Image, Image]:
        """This function captures a screenshot of the calendar,
        processes the image to extract the grayscale and red"""

        # png_path = self.chrome_render_calendar_png(htmlFile)
        png_path = self.firefox_render_calendar_png(htmlFile)

        self.logger.info('Screenshot captured and saved to file.')

        red_img = PIL.Image.open(png_path)
        red_pixels = red_img.load()
        black_img = PIL.Image.open(png_path)
        black_pixels = black_img.load()

        # Loop through every pixel in the image
        start = time.perf_counter()
        for i in range(red_img.size[0]):  # loop through every pixel in the image
            for j in range(red_img.size[1]): # since both bitmaps are identical, cycle only once and not both bitmaps
                red_value = red_pixels[i, j][0]
                green_value = red_pixels[i, j][1]
                blue_value = red_pixels[i, j][2]

                if red_value <= green_value and red_value <= blue_value:  # if is not red
                    red_pixels[i, j] = (255, 255, 255)  # change it to white in the red image bitmap

                    red_value = black_pixels[i, j][0]
                    green_value = black_pixels[i, j][1]
                    blue_value = black_pixels[i, j][2]

                elif red_value > green_value and red_value > blue_value:  # if is red
                    black_pixels[i, j] = (255, 255, 255)  # change to white in the black image bitmap

        end = time.perf_counter()
        self.logger.info(f'Processed image in {end - start:0.4f} seconds.')
        # red_img: Image = red_img.rotate(self.rotateAngle, expand=True)
        # black_img: Image = black_img.rotate(self.rotateAngle, expand=True)

        # Extract directory from png_path
        directory = os.path.dirname(png_path)

        # Save images next to the original png_path
        red_img.save(os.path.join(directory, 'red_image.png'))
        black_img.save(os.path.join(directory, 'black_image.png'))

        self.logger.info('Image colours processed. Extracted grayscale and red images.')
        return black_img, red_img
    
    def chrome_render_calendar_png(self, htmlFile: str) -> str:
        png_path = self.currPath + '/calendar.png'
        subprocess.run([
            'chromium-browser',
            '--headless',                   # No use for user interface
            '--disable-gpu',                # For Pi
            '--hide-scrollbars',            
            f'--window-size={self.imageWidth},{self.imageHeight}',
            htmlFile,
            f'--screenshot={png_path}',
            '--force-device-scale-factor=1'# Render correctly on displays smaller than image size
        ], check=True)
        return png_path
    
    def firefox_render_calendar_png(self, htmlFile: str) -> str:
        png_path = self.currPath + '/calendar.png'
        subprocess.run([
            'firefox',
            '--headless',  # Run in headless mode (no GUI)
            f'--window-size={self.imageWidth},{self.imageHeight}',  # Set the window size
            '--screenshot', png_path,  # Take a screenshot and save it to the specified path
            htmlFile  # Path to the HTML file
        ], check=True)
        return png_path

    def get_day_in_cal(self, startDate: dt.datetime, eventDate: dt.datetime) -> int:
        """
        Returns the index of the day in the calendar list
        """

        delta: dt.timedelta = eventDate - startDate
        return delta.days
