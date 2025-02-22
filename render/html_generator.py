from typing import Dict, List, Literal

import datetime as dt
import calendar

from htmlgenerator import LI, OL, HTMLElement, Tuple, render, DIV
from display_data import DisplayData
from gcal.inkal_event import InkalEvent
from gcal.inkal_task import InkalTask

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

    def get_grid_html(self, cal_list: List[List[InkalEvent | InkalTask]], data: DisplayData) -> str:
        grid = DIV(
            self.get_week_days(),
            self.get_events(cal_list, data),
            *self.get_dividers(),
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
    
    def get_events(self, cal_list: List[List[InkalEvent | InkalTask]], data: DisplayData) -> HTMLElement:
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

            if currDate.day < today.day and currDate.month <= today.month and currDate.year <= today.year:
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
                calendar_entry = cal_list[i][j]
                entry_div = None
                if calendar_entry['kind'] == 'calendar#event':
                    event: InkalEvent = calendar_entry
                    entry_div = self.get_event_html(event, currDate, today)
                elif calendar_entry['kind'] == 'tasks#task':
                    task: InkalTask = calendar_entry
                    entry_div = self.get_task_html(task, currDate, today)
                day.append(entry_div)
            
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
    
    def get_event_html(self, event: InkalEvent, currDate: dt.datetime, today: dt.datetime) -> HTMLElement:
        event_classes = ['event']

        if event['isUpdated']:
            event_classes.append('text-danger')
        elif currDate.month != today.month:
            event_classes.append('text-muted')
        
        # Multiday events
        if event['isMultiday']:
            if event['startDatetime'].date() == currDate:
                prefix = '►'
            else:
                prefix = '◄'
            prefix_html = DIV(prefix, _class='event-prefix')
        
            return DIV(
                prefix_html,
                event['summary'],
                _class=' '.join(event_classes)
            )
        
        # All day events
        elif event['allday']:
            return DIV(
                DIV('', _class='event-prefix'),
                event['summary'],
                _class=' '.join(event_classes)
            )
        
        # Events with time
        else:
            time_div = self.get_time_element(event['startDatetime'])
            return DIV(
                time_div,
                event['summary'],
                _class=' '.join(event_classes)
            )

    
    def get_task_html(self, task: InkalTask, currDate: dt.datetime, today: dt.datetime) -> HTMLElement:
        task_classes = ['task']

        if task['isUpdated']:
            task_classes.append('text-danger')
        elif currDate.month != today.month:
            task_classes.append('text-muted')

        prefix = None
        if task['isCompleted']:
            prefix = '✓'
            task_classes.append('completed')
        else:
            prefix = '🛠'
        
        task_div = DIV(
            DIV(
                prefix,
                _class='task-prefix'
            ),
            task['title'],
            _class=' '.join(task_classes)
        )
        return task_div
    
    def get_dividers(self) -> List[HTMLElement]:
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
    
    def get_time_element(self, datetimeObj) -> HTMLElement:
        """
        Returns a short time string in the format of 'HH:MM'
        """
        return DIV(
            DIV(str(datetimeObj.hour), _class='hour'),
            DIV('{:02d}'.format(datetimeObj.minute), _class='minute'),
            _class='time'
        )
