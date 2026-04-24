#All necessary imports
import os
from http import HTTPStatus
from app.apis import MSG
from datetime import datetime, timedelta
import pytest
from app import create_app
from app.db import DB
from app.db.users import USERNAME, EMAIL, PHONE
from app.db.users import UserResource, Role
from werkzeug.security import generate_password_hash

TEST_PASSWORD = "password123"
DEFAULT_CLASS_NAME = "Yoga"
DEFAULT_LOCATION = "Studio A"
DEFAULT_PHONE = "+97150000123"
ADMIN_PHONE = "+97150000111"

@pytest.fixture(scope ="module")
def app_client():
  os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
  os.environ.setdefault("DB_NAME", "test_db")
  os.environ.setdefault("MOCK_DB", "true")
  os.environ.setdefault("DEBUG", "true")

  app = create_app()
  app.config["TESTING"] = True

  with app.app_context():
    yield app.test_client()

@pytest.fixture(autouse=True)
def clear_classes_collection():
  classes_col = DB.get_collection("classes")
  classes_col.delete_many({})

def get_admin_auth_header(app_client):
  # Create admin user and return valid JWT auth header
  user_res = UserResource()
  unique_suffix = str(int(datetime.now().timestamp() * 1000000))
  username = f"admin_{unique_suffix}"
  email = f"{username}@example.com"
  password = TEST_PASSWORD

  user_res.create_user(
    username, 
    email, 
    generate_password_hash(password),
    ADMIN_PHONE,
    role = Role.ADMIN)
  
  login_response = app_client.post(
    "/auth/login",
    json ={
      "email": email,
      "password": password
    },
  )
  #Make sure login succeded
  assert login_response.status_code == HTTPStatus.OK
  #Extract token from login response
  access_token = login_response.json.get("access_token")
  assert access_token is not None

  #Return authorisation header in JWT format
  return {"Authorization": f"Bearer {access_token}"}

def get_member_auth_header(app_client):
  #Register new member user and return valid JWT auth header for that member
  #Use unique username and email each time so the test does not fail
  unique_suffix = str(int(datetime.now().timestamp() * 1000000))
  username = f"member_{unique_suffix}"
  email = f"{username}@example.com"
  password = TEST_PASSWORD

  #register a new member
  register_response = app_client.post("/auth/register/member",
    json = {
      USERNAME : username,
      EMAIL: email,
      "password": password,
      PHONE : DEFAULT_PHONE
    },
    )
  #registration should suceed
  assert register_response.status_code == HTTPStatus.CREATED

  #Log in as that member
  login_response = app_client.post("/auth/login",
    json = {
      "email": email,
      "password": password
    })
  #Make sure login succeded
  assert login_response.status_code == HTTPStatus.OK

  #Extract token and return auth header
  access_token = login_response.json.get("access_token")
  assert access_token is not None

  return {"Authorization": f"Bearer {access_token}"}

def build_valid_class():
  class_start_time = datetime.now()+timedelta(hours=2) #Done to ensure start date is in the future and within allowed 2-week window
  class_end_time = class_start_time+timedelta(hours = 1)
  return{
    "class_name": DEFAULT_CLASS_NAME,
    "start_time": class_start_time.isoformat(timespec="seconds"),
    "end_time": class_end_time.isoformat(timespec="seconds"),
    "location": DEFAULT_LOCATION,
    "capacity": 15,
    "trainer_name": "Emily Smith"
  }

def flatten_weekly_classes(weekly_classes):
  all_classes = []
  for classes_in_week in weekly_classes.values():
    all_classes.extend(classes_in_week)
  return all_classes

def create_class(app_client, class_payload = None):
  auth_headers = get_admin_auth_header(app_client)
  if class_payload is None:
    class_payload = build_valid_class()
  return app_client.post("/classes/", json = class_payload, headers = auth_headers)


#TESTS FOR FEATURE 1

def test_create_class_success(app_client):
  #Main sucess scenarion for Feature 1
  #Expected behaviour would be that admin/trainer logs in, submits valid data, API creates class, API returns HTTP 200, response contains created class id
  response = create_class(app_client)
  
  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json, dict)
  assert "Class created with id" in response.json.get(MSG)

def test_create_class_with_missing_class_name_fails(app_client):
  class_payload = build_valid_class()
  class_payload["class_name"] = ""

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Class name is required"}

def test_create_class_with_missing_start_time_fails(app_client):
  class_payload = build_valid_class()
  class_payload["start_time"] = ""

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Start time is required"}

def test_create_class_with_missing_end_time_fails(app_client):
  class_payload = build_valid_class()
  class_payload["end_time"] = ""

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "End time is required"}

def test_create_class_with_missing_location_fails(app_client):
  class_payload = build_valid_class()
  class_payload["location"] = ""

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Location is required"}

def test_create_class_with_missing_trainer_name_fails(app_client):
  class_payload = build_valid_class()
  class_payload["trainer_name"] = ""

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Trainer name is required"}


def test_create_class_with_invalid_capacity_fails(app_client):
  class_payload = build_valid_class()
  class_payload["capacity"] = 0

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_negative_capacity_fails(app_client):
  class_payload = build_valid_class()
  class_payload["capacity"] = -5

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_non_integer_capacity_fails(app_client):
  class_payload = build_valid_class()
  class_payload["capacity"] = "fifteen"

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_end_time_before_start_time_fails(app_client):
  class_payload = build_valid_class()

  class_start_time = datetime.now()+timedelta(hours = 2) #start time is in future
  class_end_time = class_start_time -timedelta(hours = 1) #end_time is before start time

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"End time must be after start time"}

def test_create_class_with_start_time_in_past_fails(app_client):
  class_payload = build_valid_class()

  class_start_time = datetime.now()-timedelta(hours = 2) #start time is in past
  class_end_time = class_start_time +timedelta(hours = 1) #end_time is after start time as required 

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"Classes can only be created for upcoming 2 weeks"}

def test_create_class_with_equal_start_time_and_end_time_fails(app_client):
  #Validation failed; end_time must strictly be after start_time, not equal to it
  class_payload = build_valid_class()

  class_start_time = datetime.now()+timedelta(hours = 2) #start time is in future(as it should be)
  class_end_time = class_start_time #end_time is equal to start time

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"End time must be after start time"}


def test_create_class_outside_upcoming_two_weeks_fails(app_client):
  class_payload = build_valid_class()

  class_start_time = datetime.now() + timedelta(days = 25) #outside of allowed 2 weeks window
  class_end_time = class_start_time +timedelta(hours = 1) #end time remains valid

  class_payload["start_time"] = class_start_time.isoformat(timespec= "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"Classes can only be created for upcoming 2 weeks"}

def test_create_class_with_invalid_datetime_format_fails(app_client):
  class_payload = build_valid_class()

  class_payload["start_time"] = "03/11/2026 08:30" #invalid date format

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Start time and end time must be in the format YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-02T08:30:00)"}

def test_create_class_without_auth_fails(app_client):
  class_payload = build_valid_class()

  response = app_client.post("/classes/", json = class_payload)
  #missing JWT should be caught by the NoAuthorizationError handler -- 401
  assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_create_class_authenticated_member_fails(app_client):
  member_auth_header = get_member_auth_header(app_client)
  class_payload = build_valid_class()

  response = app_client.post("/classes/", json=class_payload, headers=member_auth_header)

  assert response.status_code == HTTPStatus.FORBIDDEN
  assert response.json == {MSG: "Only trainers or admins can create classes"}

def test_create_class_with_overlapping_time_and_location_fails(app_client):
  first_class_payload = build_valid_class()

  first_response = create_class(app_client, first_class_payload)

  assert first_response.status_code == HTTPStatus.OK

  #Create a second class with overlapping time at the same location
  overlapping_class_payload = build_valid_class()

  #Use first class time range as a base
  first_start_time = datetime.fromisoformat(first_class_payload["start_time"])
  overlapping_start_time = first_start_time + timedelta(minutes = 30) # done to catch partial overlaps as opposed to only classes that start at exactly same time
  overlapping_end_time = overlapping_start_time +timedelta(hours=1)

  #Keep same location and create overlapping times
  overlapping_class_payload["location"] = first_class_payload["location"]
  overlapping_class_payload["start_time"] = overlapping_start_time.isoformat(timespec="seconds")
  overlapping_class_payload["end_time"] = overlapping_end_time.isoformat(timespec="seconds")

  second_response = create_class(app_client, overlapping_class_payload)

  assert second_response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert second_response.json == {MSG: "Another class is already scheduled at this location during that time"}

#TESTS FOR FEATURE 2

def test_view_class_list_with_no_upcoming_classes(app_client):
  #if there are no upcoming classes API should indeed return "No upcoming classes availible"

  response = app_client.get("/classes/")

  assert response.status_code == HTTPStatus.OK
  assert response.json == {MSG: "No upcoming classes available"}

def test_view_class_list_returns_upcoming_classes_grouped_by_week(app_client):
  #if upcoming classes do exist, API should return them grouped by week
  
  create_response = create_class(app_client)

  assert create_response.status_code == HTTPStatus.OK

  #request the class list
  response = app_client.get("/classes/")

  #check the structure of response
  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json, dict)
  assert isinstance(response.json.get(MSG), dict)

  weekly_classes = response.json.get(MSG)

  assert len(weekly_classes)>0 #should be at least one week group

  all_classes = flatten_weekly_classes(weekly_classes)
  
  assert any(one_class["class_name"] == DEFAULT_CLASS_NAME for one_class in all_classes)

def test_view_class_list_includes_full_classes(app_client):
  #full classes still appear in class list, with remaining_spots = 0
  #Log in as admin to create a class first
  create_response = create_class(app_client)
  assert create_response.status_code == HTTPStatus.OK

  #update one class to simulate it being full
  classes_col = DB.get_collection("classes")
  classes_col.update_one(
    {"class_name" : DEFAULT_CLASS_NAME},
    {"$set": {"remaining_spots":0}}
    )
  #request class list
  response = app_client.get("/classes/")

  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json.get(MSG), dict)

  weekly_classes = response.json.get(MSG)
  all_classes = flatten_weekly_classes(weekly_classes)

  #make sure that class is present and has remaining_spots as 0
  matching_classes = [one_class for one_class in all_classes if one_class["class_name"] == DEFAULT_CLASS_NAME]

  assert len(matching_classes)>0
  assert matching_classes[0]["remaining_spots"] == 0
