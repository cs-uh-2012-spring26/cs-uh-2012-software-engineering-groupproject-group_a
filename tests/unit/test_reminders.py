import os
import pytest

from http import HTTPStatus
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from bson import ObjectId
from flask_jwt_extended import create_access_token

from app.services.email import send_reminder_email
from app.apis import MSG
from app import create_app
from app.db import DB

@pytest.fixture(scope="module")
def app_client():
    os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("MOCK_DB", "true")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("AWS_REGION", "us-east-1")
    os.environ.setdefault("SES_SENDER_EMAIL", "test@example.com")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield app.test_client()

@pytest.fixture
def seed_data():
    classes = DB.get_collection("classes")
    users = DB.get_collection("users")
    bookings = DB.get_collection("bookings")
    
    classes.delete_many({})
    bookings.delete_many({})
    
    class1_id = ObjectId() # test class with no bookings
    class2_id = ObjectId() # test class with bookings
    member1_id = ObjectId() # test member with valid email
    member2_id = ObjectId() # test member with no email provided
    member3_id = ObjectId() # test member not registered in database

    classes.insert_many([{
        "_id": class1_id,
        "class_name": "Yoga",
        "start_time": (datetime.now()+timedelta(days=4)).isoformat(),
        "end_time": (datetime.now()+timedelta(days=4, hours=1)).isoformat(),
        "location": "Yoga studio",
        "capacity": 15,
        "trainer_name": "Trainer 1",
        "remaining_spots": 15,
    },{
        "_id": class2_id,
        "class_name": "Zumba",
        "start_time": (datetime.now()+timedelta(days=2)).isoformat(),
        "end_time": (datetime.now()+timedelta(days=2, hours=1)).isoformat(),
        "location": "Dance studio",
        "capacity": 5,
        "trainer_name": "Trainer 1",
        "remaining_spots": 4,
    }])

    users.insert_many([{
        "_id": member1_id,
        "name": "Test Member 1",
        "email": "member1@example.com",
        "phone": "+97150000000",
        "role": "member",
        "password_hash": "x"
    }, {
        "_id": member2_id,
        "name": "Test Member 2",
        "email": "",
        "phone": "+97150000001",
        "role": "member",
        "password_hash": "x"
    }])

    bookings.insert_many([{
        "user_id": str(member1_id),
        "class_id": str(class2_id)
    }, {
        "user_id": str(member2_id),
        "class_id": str(class2_id)
    },{
        "user_id": str(member3_id),
        "class_id": str(class2_id)
    }, {
        "user_id": ObjectId(), # covers checking for non-string member id
        "class_id": str(class2_id)
    }])

    return {"class1_id":str(class1_id), "class2_id":str(class2_id), "member_id":str(member1_id)}

def get_admin_auth_header(app_client):
  #Log in as seeded admin user and return valid JWT auth header
  login_response = app_client.post(
    "/auth/login",
    json ={
      "email": "admin1@test.com",
      "password": "password123"
    },
  )
  assert login_response.status_code == HTTPStatus.OK

  access_token = login_response.json.get("access_token")
  assert access_token is not None

  return {"Authorization": f"Bearer {access_token}"}

def get_member_auth_header(app_client):
  #Register new member user and return valid JWT auth header for that member
  #Use unique username and email each time so the test does not fail
  unique_suffix = str(int(datetime.now().timestamp() * 1000000))
  username = f"member_{unique_suffix}"
  email = f"{username}@example.com"
  password = "password123"

  #register a new member
  register_response = app_client.post("/auth/register/member",
    json = {
      "name" : username,
      "email" : email,
      "password": password,
      "phone" : "+97150000123"
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

def test_send_reminders_success(app_client, seed_data):
    with patch("app.apis.classes.send_reminder_email", return_value=True):
        resp = app_client.post(f"/classes/{seed_data['class2_id']}/reminders",headers=get_admin_auth_header(app_client))
        assert resp.status_code == 200
        assert resp.json == {MSG: "Reminders sent to 1 member(s). Failed: 2."}

def test_send_reminders_failed(app_client, seed_data):
    with patch("app.apis.classes.send_reminder_email", return_value=False):
        resp = app_client.post(f"/classes/{seed_data['class2_id']}/reminders",headers=get_admin_auth_header(app_client))
        assert resp.status_code == 200
        assert resp.json == {MSG: "Reminders sent to 0 member(s). Failed: 3."}

def test_send_reminders_unauthenticated_user(app_client, seed_data):
    resp = app_client.post(f"/classes/{seed_data['class1_id']}/reminders")
    assert resp.status_code == 401

def test_send_reminders_forbidden_for_member(app_client, seed_data):
    resp = app_client.post(f"/classes/{seed_data['class1_id']}/reminders", headers=get_member_auth_header(app_client))
    assert resp.status_code == 403

def test_send_reminders_class_not_found(app_client):
    invalid_class = str(ObjectId())
    resp = app_client.post(f"/classes/{invalid_class}/reminders",headers=get_admin_auth_header(app_client))
    assert resp.status_code == 404
    
def test_send_reminders_no_bookings(app_client, seed_data):
    resp = app_client.post(f"/classes/{seed_data['class1_id']}/reminders", headers=get_admin_auth_header(app_client))
    assert resp.status_code == 200
    assert resp.json == {MSG: "No members are registered for this class"}

def test_send_reminder_email_success():
    with patch("app.services.email.boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_boto.return_value = mock_ses
        result = send_reminder_email("test@example.com", "Test", "Yoga", "2026-03-20T08:00:00", "Yoga Studio")
        assert result == True

def test_send_reminder_email_failure():
    from botocore.exceptions import ClientError
    with patch("app.services.email.boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = ClientError({"Error": {"Code": "500", "Message": "fail"}}, "send_email")
        mock_boto.return_value = mock_ses
        result = send_reminder_email("test@example.com", "Test", "Yoga", "2026-03-20T08:00:00", "Yoga Studio")
        assert result == False


    

