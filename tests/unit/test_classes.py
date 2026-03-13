#Test for Feature 1
#All necessary imports
import os
from http import HTTPStatus
from app.apis import MSG
from datetime import datetime, timedelta
import pytest
from app import create_app
from app.db import DB
from app.db.users import USERNAME, EMAIL, PHONE


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

def get_trainer_auth_header(app_client):
  #Log in as seeded trainer user and return valid JWT auth header
  login_response = app_client.post(
    "/auth/login",
    json ={
      USERNAME: "trainer1",
      "password": "password123"
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
  password = "password123"

  #register a new member
  register_response = app_client.post("/auth/register",
    json = {
      USERNAME : username,
      EMAIL: email,
      "password": password,
      PHONE : "+97150000123"
    },
    )
  #registration should suceed
  assert register_response.status_code == HTTPStatus.CREATED

  #Log in as that member
  login_response = app_client.post("/auth/login",
    json = {
      "name": username,
      "password": password
    })
  #Make sure login succeded
  assert login_response.status_code == HTTPStatus.OK

  #Extract token and return auth header
  acces_token = login_response.json.get("access_token")
  assert acces_token is not None

  return {"Authorization": f"Bearer {acces_token}"}

def build_valid_class():
  class_start_time = datetime.now()+timedelta(hours=2) #Done to ensure start date is in the future and within allowed 2-week window
  class_end_time = class_start_time+timedelta(hours = 1)
  return{
    "class_name": "Yoga",
    "start_time": class_start_time.isoformat(timespec="seconds"),
    "end_time": class_end_time.isoformat(timespec="seconds"),
    "location": "Studio A",
    "capacity": 15,
    "trainer_name": "Emily Smith"
  }

#TESTS FOR FEATURE 1

def test_create_class_success(app_client):
  #Main sucess scenarion for Feature 1
  #Expected behaviour would be that trainer logs in, submits valid data, API creates class, API returns HTTP 200, response contains created class id
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers )

  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json, dict)
  assert "Class created with id" in response.json.get(MSG)

def test_create_class_with_missing_class_name_fails(app_client):
  #Validation failed; class_name is required
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["class_name"] = ""

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Class name is required"}

def test_create_class_with_missing_start_time_fails(app_client):
  #Validation failed; start_time is required
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["start_time"] = ""

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Start time is required"}

def test_create_class_with_missing_end_time_fails(app_client):
  #Validation failed; end_time is required
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["end_time"] = ""

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "End time is required"}

def test_create_class_with_missing_location_fails(app_client):
  #Validation failed; location is required
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["location"] = ""

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Location is required"}

def test_create_class_with_missing_trainer_name_fails(app_client):
  #Validation failed; trainer_name is required
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["trainer_name"] = ""

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Trainer name is required"}


def test_create_class_with_invalid_capacity_fails(app_client):
  #Validation failed; invalid capacity
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["capacity"] = 0

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_negative_capacity_fails(app_client):
  #Validation failed, capacity must be a positive number
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["capacity"] = -5

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_non_integer_capacity_fails(app_client):
  #Validation failed, capacity must be an integer
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()
  class_payload["capacity"] = "fifteen"

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Capacity is required"}

def test_create_class_with_end_time_before_start_time_fails(app_client):
  #Validation failed; end_time must be after start_time
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  class_start_time = datetime.now()+timedelta(hours = 2) #start time is in future
  class_end_time = class_start_time -timedelta(hours = 1) #end_time is before start time

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"End time must be after start time"}

def test_create_class_with_start_time_in_past_fails(app_client):
  #Validation failed; start_time must be in future
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  class_start_time = datetime.now()-timedelta(hours = 2) #start time is in past
  class_end_time = class_start_time +timedelta(hours = 1) #end_time is after start time as required 

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"Classes can only be created for upcoming 2 weeks"}

def test_create_class_with_equal_start_time_and_end_time_fails(app_client):
  #Validation failed; end_time must strictly be after start_time, not equal to it
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  class_start_time = datetime.now()+timedelta(hours = 2) #start time is in future(as it should be)
  class_end_time = class_start_time #end_time is equal to start time

  #overwrite valid times with invalid ones
  class_payload["start_time"] = class_start_time.isoformat(timespec = "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"End time must be after start time"}


def test_create_class_outside_upcoming_two_weeks_fails(app_client):
  #Validation failed; Classes can be created only within upcoming 2 weeks
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  class_start_time = datetime.now() + timedelta(days = 25) #outside of allowed 2 weeks window
  class_end_time = class_start_time +timedelta(hours = 1) #end time remains valid

  class_payload["start_time"] = class_start_time.isoformat(timespec= "seconds")
  class_payload["end_time"] = class_end_time.isoformat(timespec= "seconds")

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers) 

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG:"Classes can only be created for upcoming 2 weeks"}

def test_create_class_with_invalid_datetime_format_fails(app_client):
  #Validation failed; start_time and end_time must be valid ISO datetime strings
  auth_headers = get_trainer_auth_header(app_client)
  class_payload = build_valid_class()

  class_payload["start_time"] = "03/11/2026 08:30" #invalid date format

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
  assert response.json == {MSG: "Start time and end time must be in the format YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-02T08:30:00)"}

def test_create_class_without_auth_fails(app_client):
  #Test behaviour when no JWT object is provided
  class_payload = build_valid_class()

  response = app_client.post("/classes/", json = class_payload)
  #Because of app's global exception handler missing auth currently becomes HTTP 500 instead of more specific HTTP 401
  assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

def test_create_class_authenticated_member_fails(app_client):
  #Only trainers/admins can create the class
  auth_headers = get_member_auth_header(app_client)
  class_payload = build_valid_class()

  response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert response.status_code == HTTPStatus.FORBIDDEN
  assert response.json == {MSG: "Only trainers or admins can create classes"}

def test_create_class_with_overlapping_time_and_location_fails(app_client):
  #Validation fails; no two classes can be scheduled at same place and same time
  auth_headers = get_trainer_auth_header(app_client)
  first_class_payload = build_valid_class()

  first_response = app_client.post("/classes/", json = first_class_payload, headers = auth_headers)

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

  second_response = app_client.post("/classes/", json = overlapping_class_payload, headers = auth_headers)

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
  
  #Log in as trainer to create a class first
  auth_headers = get_trainer_auth_header(app_client)
  #create a valid class
  class_payload = build_valid_class()
  create_response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert create_response.status_code == HTTPStatus.OK

  #request the class list
  response = app_client.get("/classes/")

  #check the structure of response
  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json, dict)
  assert isinstance(response.json.get(MSG), dict)

  weekly_classes = response.json.get(MSG)

  assert len(weekly_classes)>0 #should be at least one week group

  #make sure created class appears
  all_classes = []
  for classes_in_week in weekly_classes.values():
    all_classes.extend(classes_in_week)
  
  assert any(one_class["class_name"] == "Yoga" for one_class in all_classes)

def test_view_class_list_includes_full_classes(app_client):
  #full classes still appear in class list, with remaining_spots = 0
  #Log in as trainer to create a class first
  auth_headers = get_trainer_auth_header(app_client)
  #create a valid class
  class_payload = build_valid_class()
  create_response = app_client.post("/classes/", json = class_payload, headers = auth_headers)

  assert create_response.status_code == HTTPStatus.OK

  #update one class to simulate it being full
  classes_col = DB.get_collection("classes")
  classes_col.update_one(
    {"class_name" : "Yoga"},
    {"$set": {"remaining_spots":0}}
    )
  #request class list
  response = app_client.get("/classes/")

  assert response.status_code == HTTPStatus.OK
  assert isinstance(response.json.get(MSG), dict)

  weekly_classes = response.json.get(MSG)
  all_classes = []
  for classes_in_week in weekly_classes.values():
    all_classes.extend(classes_in_week)

  #make sure that class is present and has remaining_spots as 0
  matching_classes = [one_class for one_class in all_classes if one_class["class_name"] == "Yoga"]

  assert len(matching_classes)>0
  assert matching_classes[0]["remaining_spots"] == 0
