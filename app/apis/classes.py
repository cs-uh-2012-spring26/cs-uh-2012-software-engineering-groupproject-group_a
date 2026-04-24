from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.classes import class_name, start_time, end_time, location, capacity, remaining_spots, trainer_name
from app.db.users import UserResource, ROLE, USERNAME, EMAIL, PHONE
from app.db.bookings import BookingResource, USER_ID
from app.services.email import send_reminder_email
from app.services.classes import can_user_create_class, create_class_with_validation 


from http import HTTPStatus
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

api = Namespace("classes", description="Endpoint for creating fitness classes")

def validate_json_body(data):
  if data is None or not isinstance(data, dict):
    return {MSG: "Request body must be JSON"}, HTTPStatus.NOT_ACCEPTABLE
  return None

def validate_class_creator_access():
  user_id = get_jwt_identity()
  if not can_user_create_class(user_id):
    return {MSG: "Only trainers or admins can create classes"}, HTTPStatus.FORBIDDEN
  return None

def extract_class_data(data):
  return{
    class_name: data.get(class_name),
    start_time: data.get(start_time),
    end_time: data.get(end_time),
    location: data.get(location),
    capacity: data.get(capacity),
    trainer_name: data.get(trainer_name),
  }  

def validate_required_string(value, error_message):
  if not isinstance(value, str) or not value.strip():
    return {MSG: error_message}, HTTPStatus.NOT_ACCEPTABLE
  return None

def validate_positive_int(value, error_message):
  if not isinstance(value, int) or value<=0:
    return {MSG: error_message}, HTTPStatus.NOT_ACCEPTABLE
  return None

def validate_class_data(class_data):
  required_string_fields = [
    (class_name, "Class name is required"), 
    (start_time, "Start time is required"),
    (end_time, "End time is required"),
    (location, "Location is required"),
    (trainer_name, "Trainer name is required")
  ]
  for field, error_message in required_string_fields:
    validation_error = validate_required_string(class_data[field], error_message)
    if validation_error:
      return validation_error
  return validate_positive_int(class_data[capacity], "Capacity is required")

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
    if not weekly_classes:
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
    #Validate that request is json
    data = request.json
    json_validation_error = validate_json_body(data)
    if json_validation_error:
      return json_validation_error

    #authorize only trainer/admin roles
    access_error = validate_class_creator_access()
    if access_error:
      return access_error
    #obtain class information
    class_data = extract_class_data(data)

    #Check for value types and make sure all values are non-empty
    validation_error = validate_class_data(class_data)
    if validation_error:
      return validation_error
    
    #Create class through service layer
    class_id, creation_error = create_class_with_validation(class_data)
    if creation_error:
       return {MSG: creation_error}, HTTPStatus.NOT_ACCEPTABLE
    return {MSG:f"Class created with id {class_id}"}, HTTPStatus.OK
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
 