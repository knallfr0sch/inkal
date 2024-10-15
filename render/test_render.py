from calendar import Calendar
import os
from pathlib import Path
import pickle
from typing import List, Tuple
from PIL import Image

from display_data import DisplayData
from gcal.google_calendar import GoogleCalendar
from typings_google_calendar_api.events import Event

from render.render import ChromeRenderer



def test_render_calendar() -> None:
    """
    Renders the calendar from a static file containing mock data
    """
    data_path = Path(__file__).parent / 'test_display_data.pickle'
    events_path = Path(__file__).parent / 'test_events.pickle'
    
    with open(data_path, 'rb') as file:
        data: DisplayData = pickle.load(file)
    
    with open(events_path, 'rb') as file:
        events: List[Event] = pickle.load(file)

    imageWidth = 984
    imageHeight = 1304
    rotateAngle = 270

    renderer = ChromeRenderer(imageWidth, imageHeight, rotateAngle)
    black_image, red_image = renderer.render(data, events)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    black_image.save(os.path.join(current_dir, 'black_image.png'))
    red_image.save(os.path.join(current_dir, 'red_image.png'))

def test_get_calendars() -> None:
    """
    Tests Google Authentication
    """
    google_calendar = GoogleCalendar()
    calendars: List[Calendar] = google_calendar.list_calendars()
    assert len(calendars) > 0