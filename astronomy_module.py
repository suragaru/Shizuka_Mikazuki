import datetime
import random

def astronomy():
    events = [
        ("Earth at Perihelion", datetime.date(2024, 7, 27), ""),
        ("Moon Occults Antares, Part 2", datetime.date(2024, 3, 3), ""),
        ("Mercury High above the Horizon at Sunset", datetime.date(2024, 3, 24), ""),
        ("Jupiter and Uranus a Half-Degree Apart", datetime.date(2024, 4, 20), ""),
        ("Perseids Peak", datetime.date(2024, 8, 12), ""),
        ("Saturn at Opposition", datetime.date(2024, 9, 8), ""),
        ("Moon Occults Saturn", datetime.date(2024, 9, 17), ""),
        ("Supermoon", datetime.date(2024, 9, 18), ""),
        ("Moon Occults Neptune", datetime.date(2024, 11, 11), ""),
        ("Jupiter at Opposition", datetime.date(2024, 12, 7), ""),
        ("Geminid Meteor Shower Peak", datetime.date(2024, 12, 13), ""),
    ]
    today = datetime.date.today()
    next_event = None  
    for event in events:
        if event[1] == today + datetime.timedelta(days=1):  # Check if the event is tomorrow
            next_event = event
            break
    if next_event is not None:
        name, date, info = next_event
        astronomy_announcement = f"*The {name} will happen tomorrow!! {info}*"
        return astronomy_announcement
    else:
        return None
