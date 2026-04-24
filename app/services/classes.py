from app.db.classes import ClassResource
from app.db.users import UserResource
from datetime import datetime, timedelta
from app.db.classes import class_name, start_time, end_time, location, capacity, trainer_name

CLASS_WINDOW_DAYS = 14
DATETIME_FORMAT_ERROR = "Start time and end time must be in the format YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-02T08:30:00)"
CLASS_WINDOW_ERROR = "Classes can only be created for upcoming 2 weeks"
CLASS_END_TIME_ERROR = "End time must be after start time"
CLASS_OVERLAP_ERROR = "Another class is already scheduled at this location during that time"

def can_user_create_class(user_id):
  user_res = UserResource()
  user = user_res.get_user_by_id(user_id)
  return user_res.can_create_class(user)

def parse_class_datetimes(class_data):
  try:
    start_datetime = datetime.fromisoformat(class_data[start_time])
    end_datetime = datetime.fromisoformat(class_data[end_time])
    return start_datetime, end_datetime
  except ValueError:
    return None

def validate_class_schedule(start_datetime, end_datetime):
  now = datetime.now() #current local time
  latest_allowed = now+timedelta(days=CLASS_WINDOW_DAYS) #latest start date permitted
  if start_datetime<now or start_datetime>latest_allowed:
    return CLASS_WINDOW_ERROR
  #end time must be after start time; class cannot start and end at same time
  if end_datetime<=start_datetime:
    return CLASS_END_TIME_ERROR
  return None 

def create_class_with_validation(class_data):
  parsed_datetimes = parse_class_datetimes(class_data)
  if parsed_datetimes is None:
    return None, DATETIME_FORMAT_ERROR
  start_datetime, end_datetime = parsed_datetimes

  schedule_error = validate_class_schedule(start_datetime, end_datetime)
  if schedule_error:
    return None, schedule_error
  class_resource = ClassResource()

  if class_resource.has_schedule_conflict(class_data[location], start_datetime, end_datetime):
    return None, CLASS_OVERLAP_ERROR
  
  class_id = class_resource.create_class(
    class_data[class_name], 
    class_data[start_time], 
    class_data[end_time], 
    class_data[location], 
    class_data[capacity], 
    class_data[trainer_name]
  )
  return class_id, None