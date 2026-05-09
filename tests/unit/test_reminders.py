import os
import pytest

from http import HTTPStatus
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from bson import ObjectId
from flask_jwt_extended import create_access_token

from app.services.email import send_reminder_email
from app.services.telegram import send_reminder_telegram
from app.services.notifications import (
    NotificationService,
    EmailNotifier,
    TelegramNotifier,
    BaseNotifier,
    ReminderData,
)
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
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
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
    
    class1_id = ObjectId() # no bookings
    class2_id = ObjectId() # has bookings - email only member + empty email member
    class3_id = ObjectId()  # has bookings - multi channel members
    past_class_id = ObjectId()  # past class

    member1_id = ObjectId() # email only - valid email
    member2_id = ObjectId() # email only - empty email
    member3_id = ObjectId()  # telegram only
    member4_id = ObjectId()  # both email and telegram
    member5_id = ObjectId()  # telegram selected but no chat id yet

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
        "remaining_spots": 3,
    },
    {
        "_id": class3_id,
        "class_name": "Pilates",
        "start_time": (datetime.now() + timedelta(days=3)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=3, hours=1)).isoformat(),
        "location": "Studio A",
        "capacity": 10,
        "trainer_name": "Trainer 1",
        "remaining_spots": 6,
    },
    {
        "_id": past_class_id,
        "class_name": "Yoga",
        "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "end_time": (datetime.now() - timedelta(hours=23)).isoformat(),
        "location": "Yoga studio",
        "capacity": 10,
        "trainer_name": "Trainer 1",
        "remaining_spots": 10,
    },])

    users.insert_many([
        {
            "_id": member1_id,
            "name": "Test Member 1",
            "email": "member1@example.com",
            "phone": "+97150000000",
            "role": "member",
            "password_hash": "x",
            "notification_prefs": ["email"],
            "telegram_chat_id": None,
        },
        {
            "_id": member2_id,
            "name": "Test Member 2",
            "email": "",
            "phone": "+97150000001",
            "role": "member",
            "password_hash": "x",
            "notification_prefs": ["email"],
            "telegram_chat_id": None,
        },
        {
            "_id": member3_id,
            "name": "Test Member 3",
            "email": "member3@example.com",
            "phone": "+97150000002",
            "role": "member",
            "password_hash": "x",
            "notification_prefs": ["telegram"],
            "telegram_chat_id": "111222333",
        },
        {
            "_id": member4_id,
            "name": "Test Member 4",
            "email": "member4@example.com",
            "phone": "+97150000003",
            "role": "member",
            "password_hash": "x",
            "notification_prefs": ["email", "telegram"],
            "telegram_chat_id": "444555666",
        },
        {
            "_id": member5_id,
            "name": "Test Member 5",
            "email": "member5@example.com",
            "phone": "+97150000004",
            "role": "member",
            "password_hash": "x",
            "notification_prefs": ["telegram"],
            "telegram_chat_id": None,  # selected telegram but not linked yet
        },
    ])

    bookings.insert_many([
        {"user_id": str(member1_id), "class_id": str(class2_id)},
        {"user_id": str(member2_id), "class_id": str(class2_id)},
        {"user_id": ObjectId(), "class_id": str(class2_id)},  # non-string id check
        
        # class3: all channel combinations
        {"user_id": str(member1_id), "class_id": str(class3_id)},
        {"user_id": str(member3_id), "class_id": str(class3_id)},
        {"user_id": str(member4_id), "class_id": str(class3_id)},
        {"user_id": str(member2_id), "class_id": str(class3_id)},
        {"user_id": str(member5_id), "class_id": str(class3_id)},
    ])

    return {"class1_id":str(class1_id), 
            "class2_id":str(class2_id), 
            "class3_id": str(class3_id),
            "past_class_id": str(past_class_id),
            "member3_phone": "+97150000002",
            "member5_id": str(member5_id),}

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


def get_reminder_data():
    return ReminderData(
        recipient_name="Test User",
        class_name="Yoga",
        start_time="2026-05-01T08:00:00",
        location="Studio B",
        email="test@example.com",
        telegram_chat_id="123456",
    )

# POST /classes/<id>/reminders

def test_send_reminders_success(app_client, seed_data):
    with patch("app.services.email.send_reminder_email", return_value=True):
        resp = app_client.post(f"/classes/{seed_data['class2_id']}/reminders",headers=get_admin_auth_header(app_client))
        assert resp.status_code == 200
        assert resp.json == {MSG: "Notifications sent: 1, Failed: 1."}

def test_send_reminders_failed(app_client, seed_data):
    with patch("app.services.email.send_reminder_email", return_value=False):
        resp = app_client.post(f"/classes/{seed_data['class2_id']}/reminders",headers=get_admin_auth_header(app_client))
        assert resp.status_code == 200
        assert resp.json == {MSG: "Notifications sent: 0, Failed: 2."}

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

def test_send_reminders_past_class(app_client, seed_data):
    resp = app_client.post(f"/classes/{seed_data['past_class_id']}/reminders", headers=get_admin_auth_header(app_client),)
    assert resp.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert resp.json == {MSG: "Reminders can only be sent for upcoming classes"}

def test_send_reminders_multi_channel_all_succeed(app_client, seed_data):
    with patch("app.services.email.send_reminder_email", return_value=True), \
         patch("app.services.telegram.send_reminder_telegram", return_value=True):
        resp = app_client.post(
            f"/classes/{seed_data['class3_id']}/reminders",
            headers=get_admin_auth_header(app_client),
        )
        assert resp.status_code == HTTPStatus.OK
        assert resp.json == {MSG: "Notifications sent: 4, Failed: 2."}
 
def test_send_reminders_multi_channel_telegram_fails(app_client, seed_data):
    with patch("app.services.email.send_reminder_email", return_value=True), \
         patch("app.services.telegram.send_reminder_telegram", return_value=False):
        resp = app_client.post(
            f"/classes/{seed_data['class3_id']}/reminders",
            headers=get_admin_auth_header(app_client),
        )
        assert resp.status_code == HTTPStatus.OK
        assert resp.json == {MSG: "Notifications sent: 2, Failed: 4."}
 
# GET /notifications/preferences
 
def test_get_preferences(app_client):
    #Newly registered member defaults to email only
    headers = get_member_auth_header(app_client)
    resp = app_client.get("/notifications/preferences", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json[MSG]
    assert "email" in data["channels"]
    assert data["telegram_linked"] == False

# PUT /notifications/preferences
 
def test_update_preferences(app_client):
    resp = app_client.put(
        "/notifications/preferences",
        json={"notification_prefs": ["email", "telegram"]},
        headers=get_member_auth_header(app_client),
    )
    assert resp.status_code == HTTPStatus.OK
 
def test_update_preferences_invalid_channel(app_client):
    resp = app_client.put(
        "/notifications/preferences",
        json={"notification_prefs": ["fax"]},
        headers=get_member_auth_header(app_client),
    )
    assert resp.status_code == HTTPStatus.NOT_ACCEPTABLE
  
# send_reminder_email tests

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

# send_reminder_telegram tests

def test_send_reminder_telegram_success():
    with patch("app.services.telegram.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        result = send_reminder_telegram("123456", "Alice", "Yoga", "2026-05-01T08:00:00", "Studio B")
        assert result == True

def test_send_reminder_telegram_code_failure():
    with patch("app.services.telegram.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=400)
        result = send_reminder_telegram("123456", "Alice", "Yoga", "2026-05-01T08:00:00", "Studio B")
        assert result == False

def test_send_reminder_telegram_exception_failure():
    with patch("app.services.telegram.requests.post", side_effect=Exception("timeout")):
        result = send_reminder_telegram("123456", "Alice", "Yoga", "2026-05-01T08:00:00", "Studio B")
        assert result == False

# EmailNotifier tests

def test_email_notifier_success():
    with patch("app.services.email.send_reminder_email", return_value=True):
        notifier = EmailNotifier()
        assert notifier.send(get_reminder_data()) == True

def test_email_notifier_failure():
    with patch("app.services.email.send_reminder_email", return_value=False):
        notifier = EmailNotifier()
        assert notifier.send(get_reminder_data()) == False

def test_email_notifier_empty_email():
    notifier = EmailNotifier()
    reminder = get_reminder_data()
    reminder.email = ""
    assert notifier.send(reminder) == False
 
def test_email_notifier_no_email_key():
    notifier = EmailNotifier()
    reminder = get_reminder_data()
    reminder.email = None
    assert notifier.send(reminder) == False

def test_email_notifier_exception():
    with patch("app.services.email.send_reminder_email", side_effect=Exception("SES down")):
        notifier = EmailNotifier()
        assert notifier.send(get_reminder_data()) == False

# TelegramNotifier tests

def test_telegram_notifier_success():
    with patch("app.services.telegram.send_reminder_telegram", return_value=True):
        notifier = TelegramNotifier()
        assert notifier.send(get_reminder_data()) == True

def test_telegram_notifier_failure():
    with patch("app.services.telegram.send_reminder_telegram", return_value=False):
        notifier = TelegramNotifier()
        assert notifier.send(get_reminder_data()) == False

def test_telegram_notifier_no_chat_id():
    notifier = TelegramNotifier()
    reminder = get_reminder_data()
    reminder.telegram_chat_id = None
    assert notifier.send(reminder) == False
 
def test_telegram_notifier_empty_chat_id():
    notifier = TelegramNotifier()
    reminder = get_reminder_data()
    reminder.telegram_chat_id = ""
    assert notifier.send(reminder) == False
  
def test_telegram_notifier_exception():
    with patch("app.services.telegram.send_reminder_telegram", side_effect=Exception("network error")):
        notifier = TelegramNotifier()
        assert notifier.send(get_reminder_data()) == False

# Telegram bot polling tests

def test_telegram_bot_valid_phone_links_chat_id(app_client, seed_data):
    from app.services.telegram_bot import handle_updates
    with patch("app.services.telegram_bot.send_message"):
        updates = [{
            "update_id": 1,
            "message": {"chat": {"id": 999888}, "text": seed_data["member3_phone"]}
        }]
        handle_updates(updates)
        users = DB.get_collection("users")
        user = users.find_one({"phone": seed_data["member3_phone"]})
        assert user["telegram_chat_id"] == "999888"
 
