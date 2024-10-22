from typing import Any, List, Literal, TypedDict
import pytz


class Config(TypedDict):
    """
    Configuration settings for the Maginkcal application.
    """
    
    batteryDisplayMode: Literal[0, 1, 2]
    accounts: List[Any]
    displayTZ: pytz.timezone
    imageHeight: int
    imageWidth: int
    isDisplayToScreen: bool
    isShutdownOnComplete: bool
    maxEventsPerDay: int
    rotateAngle: int
    screenHeight: int
    screenWidth: int
    thresholdHours: int
