from app.db.classes import ClassResource
from app.db.users import UserResource
from datetime import datetime, timedelta
from app.db.constants import class_name, start_time, end_time, location, capacity, trainer_name
from app.services.recurrence import RecurrenceStrategy, DailyRecurrenceStrategy, WeeklyRecurrenceStrategy

CLASS_WINDOW_DAYS = 14
DATETIME_FORMAT_ERROR = "Start time and end time must be in the format YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-02T08:30:00)"
CLASS_WINDOW_ERROR = "Classes can only be created for upcoming 2 weeks"
CLASS_END_TIME_ERROR = "End time must be after start time"
CLASS_OVERLAP_ERROR = "Another class is already scheduled at this location during that time"

RECURRING_TYPE_FIELD = "recurrence_type"
RECURRING_END_DATE_FIELD = "recurrence_end_date"

RECURRING_TYPE_ERROR = "Unsupported recurrence_type. Supported: daily, weekly"
RECURRING_END_DATE_ERROR = "recurrence_end_date must be a valid ISO datetime and not before start_time"

def user_has_management_access(user_id):
  user_res = UserResource()
  user = user_res.get_user_by_id(user_id)
  return user_res.has_management_access(user)

def validate_class(class_id):
  class_res = ClassResource()
  return class_res.get_class_by_id(class_id)

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

#Selects the correct recurrence algorithm at runtime based on recurrence_type from the request
def resolve_recurrence_strategy(recurrence_type: str) -> RecurrenceStrategy | None: 
    recurrence_type = (recurrence_type or "").strip().lower()
    if recurrence_type == "daily":
        return DailyRecurrenceStrategy()
    if recurrence_type == "weekly":
        return WeeklyRecurrenceStrategy()
    return None

def parse_series_end_date(class_data, first_start: datetime):
    end_date_str = class_data.get(RECURRING_END_DATE_FIELD)
    if not end_date_str:
        #default: up to CLASS_WINDOW_DAYS from first_start
        return first_start + timedelta(days=CLASS_WINDOW_DAYS)

    try:
        series_end = datetime.fromisoformat(end_date_str)
    except ValueError:
        return None

    if series_end < first_start: #recurrence end must be on/after the first class start
        return None

    return series_end

def is_class_in_future(cls):
  start_time_value = cls.get(start_time)
  if not isinstance(start_time_value, str):
      return False
  try:
      class_start = datetime.fromisoformat(start_time_value)
  except ValueError:
      return False
  return class_start > datetime.now()

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


def create_recurring_classes_with_validation(class_data):
  recurrence_type = class_data.get(RECURRING_TYPE_FIELD)
  strategy = resolve_recurrence_strategy(recurrence_type)
  if strategy is None:
      return None, RECURRING_TYPE_ERROR

  #Parse first occurrence times using existing logic
  parsed_datetimes = parse_class_datetimes(class_data)
  if parsed_datetimes is None:
      return None, DATETIME_FORMAT_ERROR
  first_start, first_end = parsed_datetimes

  #Reuse schedule validation for the first occurrence
  schedule_error = validate_class_schedule(first_start, first_end)
  if schedule_error:
      return None, schedule_error

  recurrence_end = parse_series_end_date(class_data, first_start)
  if recurrence_end is None:
      return None, RECURRING_END_DATE_ERROR

  class_resource = ClassResource()

  #Generate all occurrences via strategy
  occurrences = strategy.generate_occurrences(first_start, first_end, recurrence_end)

  created_ids: list[str] = []
  for occ in occurrences:
      start_date = occ["start_time"]
      end_date = occ["end_time"]

      #Enforce overlap constraints per occurrence
      if class_resource.has_schedule_conflict(
          class_data[location], start_date, end_date
      ):
          #On first conflict, stop and report error
          return None, CLASS_OVERLAP_ERROR

      class_id = class_resource.create_class(
          class_data[class_name],
          start_date.isoformat(),
          end_date.isoformat(),
          class_data[location],
          class_data[capacity],
          class_data[trainer_name],
      )
      created_ids.append(class_id)

  return created_ids, None