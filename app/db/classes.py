from app.db.utils import serialize_item, serialize_items
from app.db import DB
from datetime import datetime, timedelta
from app.db.constants import (CLASS_WINDOW_DAYS, CLASS_COLLECTION, class_name, start_time, end_time, location, capacity, trainer_name, remaining_spots)

from bson import ObjectId


class ClassResource:
  def __init__(self):
    self.collection = DB.get_collection(CLASS_COLLECTION)
  def create_class(self, class_name_value:str, start_time_value: str, end_time_value:str, location_value: str, capacity_value:int, trainer_name_value: str):
    new_class = { #build a new class from imput given by trainer/admin
      class_name: class_name_value,
      start_time: start_time_value,
      end_time: end_time_value,
      location: location_value,
      capacity: capacity_value,
      trainer_name: trainer_name_value,
      remaining_spots: capacity_value
    }
    insert_result = self.collection.insert_one(new_class)
    new_class_id = insert_result.inserted_id
    return str(new_class_id)
  
  def parse_class_start_time(self, one_class):
    start_time_value = one_class.get(start_time)
    if not isinstance(start_time_value, str):
      return None
    try:
      return datetime.fromisoformat(start_time_value)
    except ValueError:
      return None
    
  def is_class_within_upcoming_window(self, class_start_datetime):
    now =datetime.now()
    latest_allowed = now+ timedelta(days=CLASS_WINDOW_DAYS) #show classes within next 2 weeks
    return now<= class_start_datetime<=latest_allowed
  
  def get_week_key(self, class_start_datetime):
    year, week_number, _ = class_start_datetime.isocalendar()
    return f"{year}-W{week_number}"


  def get_upcoming_classes_grouped_by_week(self):
    #get all classes from database
    classes = self.collection.find({})
    classes_list = serialize_items(list(classes))

    weekly_classes = {}
    for one_class in classes_list:
      class_start_datetime = self.parse_class_start_time(one_class)
      if class_start_datetime is None:
        continue
      if not self.is_class_within_upcoming_window(class_start_datetime):
        continue
      week_key = self.get_week_key(class_start_datetime)
     
      if week_key not in weekly_classes:
        weekly_classes[week_key] =[]
      weekly_classes[week_key].append(one_class)
    return weekly_classes

  def get_class_by_id(self, class_id: str): #get a class by its id
    try:
      obj_id = ObjectId(class_id)
    except Exception:
        return None
    class_ = self.collection.find_one({"_id": obj_id})
    return serialize_item(class_)
  
  def has_schedule_conflict(self, location_value:str, start_datetime:datetime, end_datetime: datetime):
    classes = self.collection.find({location: location_value})
    for existing_class in classes:
      existing_start_str = existing_class.get(start_time)
      existing_end_str = existing_class.get(end_time)
      # skip if missing values
      if existing_start_str is None or existing_end_str is None:
        continue
      try:
        existing_start = datetime.fromisoformat(existing_start_str)
        existing_end = datetime.fromisoformat(existing_end_str)
      except Exception:
        continue
      #check overlap
      if existing_start<end_datetime and start_datetime<existing_end:
        return True
    return False

  def has_remaining_spots(self, class_id):
    class_obj = self.get_class_by_id(class_id)
    return bool(class_obj and class_obj.get(remaining_spots, 0) > 0)

  def decrement_remaining_spots(self, class_id: str): #decrement remaining spots of a class when a member books it
    from bson import ObjectId
    result = self.collection.update_one(
      {"_id": ObjectId(class_id), remaining_spots: {"$gt": 0}},
      {"$inc": {remaining_spots: -1}},
    )
    return result.modified_count == 1
