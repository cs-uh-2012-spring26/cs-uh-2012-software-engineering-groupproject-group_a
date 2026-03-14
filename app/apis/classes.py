from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.classes import class_name, start_time, end_time, location, capacity, remaining_spots, trainer_name
from app.db.users import UserResource, ROLE, USERNAME, EMAIL, PHONE
from app.db.bookings import BookingResource, USER_ID
from app.services.email import send_reminder_email

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
        "Upcoming classes grouped by week",
        {MSG: fields.Raw(description="Dictionary which has ISO week as a key and list of classes as value")}
      ),
  )
  def get(self):
    class_resource = ClassResource()
    weekly_classes = class_resource.get_upcoming_classes_grouped_by_week()
    #If there are no upcoming classes return a message
    if len(weekly_classes) == 0:
      return {MSG: "No upcoming classes available"}, HTTPStatus.OK
    return {MSG: weekly_classes}, HTTPStatus.OK
  
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
    #end time must be after start time; class cannot start and end at same time
    if end_datetime<=start_datetime:
      return {MSG:"End time must be after start time"}, HTTPStatus.NOT_ACCEPTABLE
    
    #Prevent class overlap: two classes at same time at same location
    existing_classes_by_week = ClassResource().get_upcoming_classes_grouped_by_week()
    for classes_in_week in existing_classes_by_week.values():
      for existing_class in classes_in_week:
        if existing_class.get(location)!=location_value:
          continue
        try:
          existing_start = datetime.fromisoformat(existing_class.get(start_time))
          existing_end = datetime.fromisoformat(existing_class.get(end_time))
        except Exception:
          continue
        if existing_start< end_datetime and start_datetime<existing_end:
          return {MSG: "Another class is already scheduled at this location during that time"}, HTTPStatus.NOT_ACCEPTABLE
        

    class_resource = ClassResource()
    class_id = class_resource.create_class(class_name_value, start_time_value, end_time_value, location_value, capacity_value, trainer_name_value)
    return {MSG: f"Class created with id {class_id}"}, HTTPStatus.OK


@api.route("/<string:class_id>/members")
class ClassMembers(Resource):
  @jwt_required()
  @api.response(
      HTTPStatus.OK,
      "Success",
      api.model(
          "ClassMembersResponse",
          {
              MSG: fields.List(
                  fields.Nested(
                      api.model(
                          "MemberItem",
                          {
                              "name": fields.String,
                              "email": fields.String,
                              "phone": fields.String,
                          },
                      )
                  )
              )
          },
      ),
  )
  @api.response(
      HTTPStatus.FORBIDDEN,
      "Forbidden",
      api.model(
          "ClassMembersForbidden",
          {MSG: fields.String(example="Only trainers or admins can view class members")},
      ),
  )
  @api.response(
      HTTPStatus.NOT_FOUND,
      "Class not found",
      api.model("ClassMembersNotFound", {MSG: fields.String(example="Class not found")}),
  )
  def get(self, class_id: str):
      # authorize trainer
      user_id = get_jwt_identity()
      user_res = UserResource()
      user = user_res.get_user_by_id(user_id)

      if user is None or user.get(ROLE) not in ("trainer", "admin"):
          return {MSG: "Only trainers or admins can view class members"}, HTTPStatus.FORBIDDEN

      # ensure class exists
      class_res = ClassResource()
      cls = class_res.get_class_by_id(class_id)
      if cls is None:
          return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

      # get bookings for the class
      booking_res = BookingResource()
      bookings = booking_res.get_class_bookings(class_id)

      # loop bookings to fetch user records
      result = []
      seen = set()

      for booking in bookings:
          member_id = booking.get(USER_ID)
          if not isinstance(member_id, str):
              continue

          if member_id in seen:
              continue
          seen.add(member_id)

          member = user_res.get_user_by_id(member_id)
          if member is None:
              continue

          result.append({
              "name": member.get(USERNAME),
              "email": member.get(EMAIL),
              "phone": member.get(PHONE),
          })

      return {MSG: result}, HTTPStatus.OK
  
@api.route("/<string:class_id>/reminders")
class SendReminders(Resource):
  @jwt_required()
  @api.response(
      HTTPStatus.OK,
      "Reminders sent",
      api.model(
          "RemindersResponse",
          {MSG: fields.String(example="Reminders sent to 5 member(s). Failed: 0.")},
      ),
  )
  @api.response(
      HTTPStatus.FORBIDDEN,
      "Forbidden",
      api.model(
          "RemindersForbidden",
          {MSG: fields.String(example="Only trainers or admins can send reminders")},
      ),
  )
  @api.response(
      HTTPStatus.NOT_FOUND,
      "Class not found",
      api.model(
          "RemindersNotFound",
          {MSG: fields.String(example="Class not found")},
      ),
  )
  def post(self, class_id: str):
    # Authorize: trainer or admin only
    user_id = get_jwt_identity()
    user_res = UserResource()
    user = user_res.get_user_by_id(user_id)
    if user is None or user.get(ROLE) not in ("trainer", "admin"):
      return {MSG: "Only trainers or admins can send reminders"}, HTTPStatus.FORBIDDEN
    
    # Ensure class exists
    class_res = ClassResource()
    cls = class_res.get_class_by_id(class_id)
    if cls is None:
      return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND
    
    # Fetch all bookings for the class
    booking_res = BookingResource()
    bookings = booking_res.get_class_bookings(class_id)
    if not bookings:
      return {MSG: "No members are registered for this class"}, HTTPStatus.OK   
    
    class_name_value = cls.get(class_name, "")
    start_time_value = cls.get(start_time, "")
    location_value   = cls.get(location, "")

    sent   = 0
    failed = 0
    seen = set()
 
    for booking in bookings:
      member_id = booking.get(USER_ID)
      if not isinstance(member_id, str) or member_id in seen:
          continue
      seen.add(member_id)
 
      member = user_res.get_user_by_id(member_id)
      if member is None:
          failed += 1
          continue
 
      member_email = member.get(EMAIL)
      member_name  = member.get(USERNAME, "Member")
 
      if not member_email:
          failed += 1
          continue
 
      success = send_reminder_email(
          recipient_email=member_email,
          recipient_name=member_name,
          class_name=class_name_value,
          start_time=start_time_value,
          location=location_value,
      )
      if success:
          sent += 1
      else:
          failed += 1
 
    return {MSG: f"Reminders sent to {sent} member(s). Failed: {failed}."}, HTTPStatus.OK
 