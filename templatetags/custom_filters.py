# In custom_filters.py

from django import template
from datetime import datetime, timedelta, time

register = template.Library()

@register.filter
def format_time(hour, minute):
    if hour >= 12:
        suffix = 'PM'
        hour = hour - 12 if hour > 12 else hour
    else:
        suffix = 'AM'
    return f"{hour}:{minute:02d} {suffix}"

@register.filter
def add_time(hour, minute):
    total_minutes = hour * 60 + minute + 30
    new_hour = (total_minutes // 60) % 24
    new_minute = total_minutes % 60
    return format_time(new_hour, new_minute)


@register.filter
def time_to_hour(minute):
    return minute // 30

@register.filter
def calculate_duration(schedule):
    start_time_minutes = schedule.start_time.hour * 60 + schedule.start_time.minute
    end_time_minutes = schedule.end_time.hour * 60 + schedule.end_time.minute
    return end_time_minutes - start_time_minutes

# Filter to calculate how many 30-minute slots the duration spans
@register.filter
def slots_to_span(duration):
    return duration // 30

@register.filter
def is_in_time_range(schedule, time_slot):
    hour, minute = time_slot  # Unpack the time_slot tuple
    start_time = schedule.start_time
    end_time = schedule.end_time

    # Define the slot start and end times
    slot_start = time(hour, minute)
    slot_end = time(hour + (minute + 30) // 60, (minute + 30) % 60)

    # Check if the schedule overlaps with the time slot
    return start_time <= slot_end and end_time > slot_start


@register.filter
def is_occupied_in_timeslot(room_schedules, hour_minute_tuple):
    hour, minute = hour_minute_tuple
    for schedule in room_schedules:
        if schedule.start_time.hour == hour and schedule.start_time.minute == minute:
            return True
    return False

@register.filter
def slots_to_span(duration):
    # Assuming duration is in minutes and each time slot is 30 minutes
    # Adjust this based on your exact time slot duration
    time_slot_duration = 30  # 30 minutes per time slot
    return duration // time_slot_duration

@register.filter(name='add_px')
def add_px(value):
    try:
        return f"{value}px"
    except (ValueError, TypeError):
        return value
    
@register.filter
def time_difference_in_minutes(end_time, start_time):
    """Calculates the difference in minutes between two datetime.time objects."""
    # Combine time with a default date (so we can subtract them)
    today = datetime.today().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)

    # Calculate the difference in time
    delta = end_datetime - start_datetime
    return delta.total_seconds() / 60

@register.filter
def time_to_minutes(time_obj):
    """Converts a datetime.time object to minutes since midnight."""
    if time_obj:
        return time_obj.hour * 60 + time_obj.minute
    return 0


@register.filter
def timeslot_height(duration_minutes):
    """Converts a duration in minutes into a height for the schedule item."""
    # Height for a 30-minute slot
    slot_height = 50  # Height of each time slot in pixels
    max_duration = 30  # Maximum time duration in minutes for a single slot

    # Scale the duration to fit within the maximum height (50px for 30 minutes).
    if duration_minutes > max_duration:
        # Limit height to 50px for longer exams (ensures they don’t overflow the slot)
        return slot_height
    else:
        return (duration_minutes / max_duration) * slot_height


@register.filter
def time_diff(end_time, start_time):
    """
    Calculate the difference between two times in minutes.
    Assumes end_time and start_time are datetime objects.
    """
    duration = end_time - start_time
    return duration.total_seconds() / 60  # Return the difference in minutes


@register.filter
def has_schedule_for_day(rooms, day):
    return [room for room in rooms if any(schedule.day == day for schedule in room.schedules)]

# Filter to check if a room has any schedules for a specific time slot
@register.filter
def has_schedule_for_time_slot(rooms, time_slot):
    return [room for room in rooms if any(schedule.start_time.hour == time_slot[0] and schedule.start_time.minute == time_slot[1] for schedule in room.schedules)]

# Filter to check if a room has any schedules for a specific time slot and day
@register.filter
def has_schedule_for_time_slot_and_day(rooms, args):
    time_slot, day = args
    return [room for room in rooms if any(schedule.start_time.hour == time_slot[0] and schedule.start_time.minute == time_slot[1] and schedule.day == day for schedule in room.schedules)]

@register.filter
def year_sem_color(year_sem_id):
    mapping = {
        (1, 2): 'red',
        (3, 4): 'blue',
        (5, 6): 'yellow',
        (7, 8): 'pink',
    }
    for key, color in mapping.items():
        if year_sem_id in key:
            return color
    return '#FCB316'

@register.filter
def in_list(value, arg):
    """
    Check if a value exists in a comma-separated list (arg).
    """
    if value is None:
        return False  # Return False if the value is None
    try:
        value = int(value)  # Convert the value to an integer
        list_values = [int(item) for item in arg.split(",")]  # Convert the list to integers
        return value in list_values
    except ValueError:
        return False  # If conversion fails, return False
    

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
