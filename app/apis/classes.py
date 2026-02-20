from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.classes import class_name, start_time, end_time, location, capacity, remaining_spots, trainer_name
from app.db.users import UserResource, ROLE
from http import HTTPStatus
from flask import request
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity

api = Namespace("classes", description="Endpoint for creating fitness classes")
#Example class
_Example_class_1={
  class_name: "Yoga",
  start_time: "2026-03-02T08:30:00",
  end_time: "2026-03-02T09:45:00",
  location: "Yoga studio",
  capacity: 15,
  trainer_name: "Emily Smith",
  remaining_spots:15
}
class_create_fields = api.model(
  "NewClassEntry",{
    class_name: fields.String(example = _Example_class_1[class_name]),
    start_time: fields.String(example = _Example_class_1[start_time]),
    end_time: fields.String(example = _Example_class_1[end_time]),
    location: fields.String(example = _Example_class_1[location]),
    capacity: fields.Integer(example = _Example_class_1[capacity]),
    trainer_name: fields.String(example = _Example_class_1[trainer_name]),
  },
)
class_list_fields = api.model(
  "ClassList", {
    class_name: fields.String(example= _Example_class_1[class_name]),
    start_time: fields.String(example = _Example_class_1[start_time]),
    end_time: fields.String(example = _Example_class_1[end_time]),
    location: fields.String(example = _Example_class_1[location]),
    capacity: fields.Integer(example = _Example_class_1[capacity]),
    remaining_spots: fields.Integer(example = _Example_class_1[remaining_spots]),
    trainer_name: fields.String(example = _Example_class_1[trainer_name]),
  },
)
@api.route("/")
class ClassList(Resource):
  #Fetches list of upcoming fitness classes, endpoint used by guests, members, trainers and admins, returns all classes scheduled within upcoming 2 weeks, inlcudes full classes
  @api.response(
      HTTPStatus.OK,
      "Success",
      api.model(
        "Upcoming classes",
        {MSG: fields.List(fields.Nested(class_list_fields))}
      ),
  )
  def get(self):
    class_resource = ClassResource()
    upcoming_classes = class_resource.get_upcoming_classes()
    #If there are no upcoming classes return a message
    if len(upcoming_classes) == 0:
      return {MSG: "No upcoming classes available"}, HTTPStatus.OK
    return {MSG: upcoming_classes}, HTTPStatus.OK
  
  #Creates a new fitness class, endpoint used by trainers and admins, validates inputs and applies upcoming 2 weeks rule
  @jwt_required()
  @api.expect(class_create_fields)
  @api.response(
    HTTPStatus.OK,
    "Success",
    api.model(
      "Create Class",
      {MSG: fields.String("Class created with id: abc123baha")},
    ),
  )
  @api.response(
    HTTPStatus.NOT_ACCEPTABLE,
    "Invalid Request",
    api.model(
      "Create Class: Bad request",
      {MSG: fields.String("Invalid value given for one of the fields")},
    ),
  )
  @api.response(
    HTTPStatus.FORBIDDEN,
    "Forbidden",
    api.model(
      "Create Class: Forbidden",
      {MSG: fields.String("Only trainers or admins can create classes")},
    ),
  )
  def post(self):
    if request.json is None or not isinstance(request.json, dict):
      return {MSG: "Requets body must be JSON"}, HTTPStatus.NOT_ACCEPTABLE

    #authorize only trainer/admin roles
    user_id = get_jwt_identity()
    user_res = UserResource()
    user = user_res.get_user_by_id(user_id)
    if user is None or user.get(ROLE) not in ("trainer", "admin"):
      return {MSG: "Only trainers or admins can create classes"}, HTTPStatus.FORBIDDEN

    class_name_value = request.json.get(class_name)
    start_time_value = request.json.get(start_time)
    end_time_value = request.json.get(end_time)
    location_value = request.json.get(location)
    capacity_value = request.json.get(capacity)
    trainer_name_value = request.json.get(trainer_name)
    #Check for value types and make sure all values are non-empty
    if not isinstance(class_name_value, str) or len(class_name_value.strip())==0:
      return {MSG: "Class name is required"}, HTTPStatus.NOT_ACCEPTABLE
    if not isinstance(start_time_value, str) or len(start_time_value.strip())==0:
      return {MSG: "Start time is required"}, HTTPStatus.NOT_ACCEPTABLE
    if not isinstance(end_time_value, str) or len(end_time_value.strip())==0:
      return {MSG: "End time is required"}, HTTPStatus.NOT_ACCEPTABLE
    if not isinstance(location_value, str) or len(location_value.strip())==0:
      return {MSG: "Location is required"}, HTTPStatus.NOT_ACCEPTABLE
    if not isinstance(trainer_name_value, str) or len(trainer_name_value.strip())==0:
      return {MSG: "Trainer name is required"}, HTTPStatus.NOT_ACCEPTABLE
    if not isinstance(capacity_value, int) or capacity_value<=0:
      return {MSG: "Capacity is required"}, HTTPStatus.NOT_ACCEPTABLE
    
    #parse start and end time as datetime objects
    try:
      start_datetime = datetime.fromisoformat(start_time_value)
      end_datetime = datetime.fromisoformat(end_time_value)
    except Exception:
      return {MSG: "Start time and end time must be in the format YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-02T08:30:00)"}, HTTPStatus.NOT_ACCEPTABLE
    #classes can be booked only within upcoming 2 weeks
    now = datetime.now() #current local time
    latest_allowed = now+timedelta(days=14) #latest start date permitted
    if start_datetime<now or start_datetime>latest_allowed:
      return {MSG: "Classes can only be created for upcoming 2 weeks"}, HTTPStatus.NOT_ACCEPTABLE
    #end time must be before start time; class cannot start and end at same time
    if end_datetime<=start_datetime:
      return {MSG:"End time must be after start time"}, HTTPStatus.NOT_ACCEPTABLE
    class_resource = ClassResource()
    class_id = class_resource.create_class(class_name_value, start_time_value, end_time_value, location_value, capacity_value, trainer_name_value)
    return {MSG: f"Class created with id {class_id}"}, HTTPStatus.OK
