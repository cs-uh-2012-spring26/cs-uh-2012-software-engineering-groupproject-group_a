from http import HTTPStatus
from datetime import datetime, timedelta
from app.db.users import USERNAME, EMAIL, PHONE
from app.db.users import UserResource, Role
from werkzeug.security import generate_password_hash

TEST_PASSWORD = "password123"
DEFAULT_CLASS_NAME = "Yoga"
DEFAULT_LOCATION = "Studio A"
DEFAULT_PHONE = "+97150000123"
ADMIN_PHONE = "+97150000111"

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

def create_class(app_client, class_payload = None):
  auth_headers = get_admin_auth_header(app_client)
  if class_payload is None:
    class_payload = build_valid_class()
  return app_client.post("/classes/", json = class_payload, headers = auth_headers)
