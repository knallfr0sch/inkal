#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This part of the code exposes functions to interface with the eink display
"""

import display.epd_12_in_48_colour_V2 as eink
from PIL import Image
import logging


class EInkDisplay:

    def __init__(self, width: int, height: int) -> None:
        # Initialise the display
        self.logger = logging.getLogger('maginkcal')
        self.screenwidth = width
        self.screenheight = height
        self.epd = eink.EPD()
        self.epd.Init()

    def display(self, black_image: Image.Image, red_image: Image.Image):
        # Updates the display with the grayscale and red images
        # start displaying on eink display
        # self.epd.clear()
        self.epd.display(black_image, red_image)
        self.logger.info('Showing image on E-Ink display.')

    def calibrate(self, cycles=1):
        # Calibrates the display to prevent ghosting
        white = Image.new('1', (self.screenwidth, self.screenheight), 'white')
        black = Image.new('1', (self.screenwidth, self.screenheight), 'black')
        for _ in range(cycles):
            self.epd.display(black, white)
            self.epd.display(white, black)
            self.epd.display(white, white)
        self.logger.info('E-Ink display calibration complete.')

    def sleep(self):
        # send E-Ink display to deep sleep
        self.epd.EPD_Sleep()
        self.logger.info('E-Ink display entered deep sleep.')

