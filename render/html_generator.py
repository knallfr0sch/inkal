from typing import Dict, List, Literal

import datetime as dt
import calendar

from htmlgenerator import LI, OL, HTMLElement, Tuple, render, DIV
from display_data import DisplayData

BatteryText = Literal[
    'batteryHide',
    'battery0'
    'battery20',
    'battery40',
    'battery60',
    'battery80',
    ]

class HtmlGenerator:
    """
    Declarative HTML generator for the calendar display
    """

    def get_grid_html(self, cal_list, data: DisplayData) -> str:
        grid = DIV(
            self.get_week_days(),
            self.get_events(cal_list, data),
            *self.get_divider(),
            style="""
                display: grid;
                position: relative;
                grid-template-columns: repeat(7, 1fr); gap: 0.5rem;
                """,
        )

        return render(grid, basecontext={})

    def get_week_days(self) -> HTMLElement:
        """
        First row, displaying the days of the week  
        """        
        # dayOfWeekText: list[str] = [day[:2].capitalize() for day in calendar.day_abbr]
        dayOfWeekText: List[str] = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

        li_elements = []
        for i in range(0, 7):
            li_element = DIV(
                dayOfWeekText[i % 7],
                _class='weekday'
                )
            li_elements.append(li_element)
        
        weekday_list = DIV(
            *li_elements,
            _class="day-names text-center grid__item",
            style="display: contents;"
        )

        return weekday_list
    
    def get_events(self, cal_list: List[List[Dict]], data: DisplayData) -> HTMLElement:
        """
        Generate the HTML for the events 
        """
        cal_events_elements = []
        maxEventsPerDay: int = data['maxEventsPerDay']

        for i in range(len(cal_list)):
            currDate: dt.datetime = data['calStartDate'] + dt.timedelta(days=i)
            dayOfMonth: int = currDate.day
            today = data['today']
            day_class: str = ""
            
            if currDate == today:
                classes = 'datecircle'
            elif currDate.month != today.month:
                classes = "date text-muted"
            else:
                classes = "date"

            if currDate.day < today.day and currDate.month <= today.month:
                day_class = "past"
            elif today + dt.timedelta(days=14) <= currDate:
                day_class = "future"
            
            day = DIV(
                DIV(
                    str(dayOfMonth),
                    _class=classes
                ),
                _class = "grid__item day " + day_class
            )
            
            for j in range(min(len(cal_list[i]), maxEventsPerDay)):
                event = cal_list[i][j]
                event_classes = ['event']
                if event['isUpdated']:
                    event_classes.append('text-danger')
                elif currDate.month != today.month:
                    event_classes.append('text-muted')
                
                if event['isMultiday']:
                    if event['startDatetime'].date() == currDate:
                        event_text = '►' + event['summary']
                    else:
                        event_text = '◄' + event['summary']
                elif event['allday']:
                    event_text = event['summary']
                else:
                    time_div = self.get_time_element(event['startDatetime'])
                    event_text = event['summary']
                
                event_div = DIV(
                    time_div,
                    event_text,
                    _class=' '.join(event_classes)
                )
                day.append(event_div)
            
            if len(cal_list[i]) > maxEventsPerDay:
                more_events_div = DIV(str(len(cal_list[i]) - maxEventsPerDay) + ' more', _class="event text-muted")
                day.append(more_events_div)
            
            cal_events_elements.append(day)
            days = DIV(
                *cal_events_elements,
                _class="days",
                style="display: contents;"
            )            
        
        return days
    
    def get_divider(self) -> List[HTMLElement]:
        return [
            DIV(
                str(""),
                style="""
                    position: absolute;
                    background-color: grey;
                    width: 96%;
                    height: 1px;
                    top: 75px;
                    left: 2%;
                """
            ),
            DIV(
                str(""),
                style="""
                    position: absolute;
                    background-color: grey;
                    width: 1px;
                    height: 80%;
                    top: 75px;
                    left: 71%;
                """
            ),
            DIV(
                str(""),
                style="""
                    position: absolute;
                    background-color: grey;
                    width: 1px;
                    height: 80%;
                    top: 75px;
                    left: 28%;
                """
            ),
        ]

    def get_battery_text(self, data: DisplayData) -> BatteryText:
        displayMode: Literal[0, 1, 2] = data['batteryDisplayMode']

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
    
    
    def get_time_element(self, datetimeObj) -> HTMLElement:
        """
        Returns a short time string in the format of 'HH:MM'
        """
        return DIV(
            DIV(str(datetimeObj.hour), _class='hour'),
            DIV('{:02d}'.format(datetimeObj.minute), _class='minute'),
            _class='time'
        )
