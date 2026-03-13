import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from flask_jwt_extended import create_access_token

from app import create_app
from app.db import DB
from app.db.classes import (
    class_name,
    start_time,
    end_time,
    location,
    capacity,
    remaining_spots,
    trainer_name,
)
from app.db.bookings import CLASS_ID, USER_ID, BOOKING_DATETIME
from app.apis import MSG


@pytest.fixture(scope="module")
def app_client():  #Flask test client backed by an mongomock database 
    os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("MOCK_DB", "true")
    os.environ.setdefault("DEBUG", "true")

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app.test_client()


@pytest.fixture
def seed_data():
    #Seed a test user and class into the mock database
    users_col = DB.get_collection("users")
    classes_col = DB.get_collection("classes")
    bookings_col = DB.get_collection("bookings")

    #Clean previous test data
    users_col.delete_many({})
    classes_col.delete_many({})
    bookings_col.delete_many({})

    user_id = ObjectId()
    users_col.insert_one(
        {
            "_id": user_id,
            "name": "Test Member",
            "email": "member@example.com",
            "password_hash": "hashed-password",
            "phone": "+971500000000",
            "role": "member",
        }
    )

    class_id = ObjectId()
    classes_col.insert_one(
        {
            "_id": class_id,
            class_name: "Yoga",
            start_time: (datetime.now() + timedelta(days=2)).isoformat(),
            end_time: (datetime.now() + timedelta(days=2, hours=1)).isoformat(),
            location: "Room A",
            capacity: 10,
            remaining_spots: 5,
            trainer_name: "Trainer 1",
        }
    )

    return {"user_id": str(user_id), "class_id": str(class_id)}


def _auth_headers(app_client, user_id: str) -> dict:
    #Helper to build Authorization header with a valid JWT for the given user id
    app = app_client.application
    with app.app_context():
        token = create_access_token(identity=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_book_class_success(app_client, seed_data): #test if member can successfully book a class with available spots
    user_id = seed_data["user_id"]
    class_id = seed_data["class_id"]

    headers = _auth_headers(app_client, user_id)
    classes_col = DB.get_collection("classes")
    bookings_col = DB.get_collection("bookings")

    before_spots = classes_col.find_one({"_id": ObjectId(class_id)})[remaining_spots]

    resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: class_id},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert MSG in body
    assert "Booking successful" in body[MSG]

    booking = bookings_col.find_one({USER_ID: user_id, CLASS_ID: class_id})
    assert booking is not None
    assert BOOKING_DATETIME in booking

    after_spots = classes_col.find_one({"_id": ObjectId(class_id)})[remaining_spots]
    assert after_spots == before_spots - 1


def test_book_class_not_found(app_client, seed_data): #test if the class id does not exist, the API should return 404
    user_id = seed_data["user_id"]
    headers = _auth_headers(app_client, user_id)

    non_existent_class_id = str(ObjectId())

    resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: non_existent_class_id},
        headers=headers,
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body[MSG] == "Class not found"


def test_book_class_duplicate_booking(app_client, seed_data): #test if booking the same class twice for the same user should be rejected
    user_id = seed_data["user_id"]
    class_id = seed_data["class_id"]
    headers = _auth_headers(app_client, user_id)

    #First booking succeeds
    first_resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: class_id},
        headers=headers,
    )
    assert first_resp.status_code == 200

    #Second booking should be rejected as duplicate
    second_resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: class_id},
        headers=headers,
    )
    assert second_resp.status_code == 400
    body = second_resp.get_json()
    assert body[MSG] == "You have already booked this class"


def test_book_class_full(app_client, seed_data): #test if remaining_spots is 0, booking should be rejected as full
    user_id = seed_data["user_id"]
    class_id = seed_data["class_id"]
    headers = _auth_headers(app_client, user_id)

    classes_col =DB.get_collection("classes")
    classes_col.update_one(
        {"_id": ObjectId(class_id)},
        {"$set": {remaining_spots: 0}},
    )

    resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: class_id},
        headers=headers,
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body[MSG] == "Class is full"


def test_my_bookings_returns_only_current_user_bookings(app_client, seed_data): #test if /bookings/mine should return bookings for the authenticated user only
    user_id = seed_data["user_id"]
    class_id = seed_data["class_id"]
    headers = _auth_headers(app_client, user_id)

    bookings_col = DB.get_collection("bookings")
    #booking for this user
    bookings_col.insert_one(
        {
            USER_ID: user_id,
            CLASS_ID: class_id,
            BOOKING_DATETIME: datetime.now().isoformat(),
        }
    )
    #Booking for a different user (should not be returned)
    bookings_col.insert_one(
        {
            USER_ID: str(ObjectId()),
            CLASS_ID: class_id,
            BOOKING_DATETIME: datetime.now().isoformat(),
        }
    )

    resp = app_client.get("/bookings/mine", headers=headers)
    assert resp.status_code == 200
    body=resp.get_json()
    items = body[MSG]
    assert len(items) == 1
    assert items[0]["class_id"] == class_id


def test_book_class_uses_booking_resource_create(app_client, seed_data): #Use MagicMock to verify that the API calls BookingResource.create_booking with the expected arguments
    user_id = seed_data["user_id"]
    class_id = seed_data["class_id"]
    headers = _auth_headers(app_client, user_id)

    with patch(
        "app.apis.bookings.BookingResource.create_booking",
        MagicMock(return_value="mock_booking_id"),
    ) as mock_create:
        resp = app_client.post(
            "/bookings/",
            json={CLASS_ID: class_id},
            headers=headers,
        )

    assert resp.status_code == 200
    mock_create.assert_called_once_with(user_id, class_id)


def test_book_class_unauthenticated(app_client, seed_data):
    #missing JWT should be caught by the NoAuthorizationError handler -- 401
    class_id = seed_data["class_id"]

    resp = app_client.post(
        "/bookings/",
        json={CLASS_ID: class_id},
    )

    assert resp.status_code == 401


def test_book_class_missing_class_id(app_client, seed_data):
    #missing CLASS_ID should be caught by the BadRequest handler -- 400
    user_id = seed_data["user_id"]
    headers = _auth_headers(app_client, user_id)

    resp = app_client.post(
        "/bookings/",
        json={},  #missing CLASS_ID in request body
        headers=headers,
    )

    assert resp.status_code == 400