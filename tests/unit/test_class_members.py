import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from flask_jwt_extended import create_access_token

from app import create_app
from app.apis import MSG
from app.db import DB
from app.db.bookings import CLASS_ID, USER_ID
from app.db.classes import (
    class_name,
    start_time,
    end_time,
    location,
    capacity,
    remaining_spots,
    trainer_name,
)


@pytest.fixture(scope="module")
def app_client():
    #ensure env vars exist before Config is imported
    os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("MOCK_DB", "true")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("JWT_SECRET_KEY", "this-is-a-long-enough-secret-key-for-testing")

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app.test_client()


def _auth_headers(app_client, user_id: str) -> dict:
    app = app_client.application
    with app.app_context():
        token = create_access_token(identity=user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_class_and_users():
    # Seed:
    # -one trainer user (authorized)
    # -one member user (unauthorized)
    # -two member users who booked the class (including duplicate bookings)
    # -one class
    # -bookings for the class
    
    users_col = DB.get_collection("users")
    classes_col = DB.get_collection("classes")
    bookings_col = DB.get_collection("bookings")

    users_col.delete_many({})
    classes_col.delete_many({})
    bookings_col.delete_many({})

    trainer_id = ObjectId()
    users_col.insert_one(
        {
            "_id": trainer_id,
            "name": "Trainer User",
            "email": "trainer@example.com",
            "password_hash": "x",
            "phone": "+971500000000",
            "role": "trainer",
        }
    )

    member_id = ObjectId()
    users_col.insert_one(
        {
            "_id": member_id,
            "name": "Member User",
            "email": "member@example.com",
            "password_hash": "x",
            "phone": "+971500000001",
            "role": "member",
        }
    )

    booked_member_1_id = ObjectId()
    booked_member_2_id = ObjectId()
    users_col.insert_one(
        {
            "_id": booked_member_1_id,
            "name": "Booked One",
            "email": "booked1@example.com",
            "password_hash": "x",
            "phone": "+971500000010",
            "role": "member",
        }
    )
    users_col.insert_one(
        {
            "_id": booked_member_2_id,
            "name": "Booked Two",
            "email": "booked2@example.com",
            "password_hash": "x",
            "phone": "+971500000011",
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
            trainer_name: "Trainer Name",
        }
    )

    #bookings store ids as strings in this project
    class_id_str = str(class_id)
    bookings_col.insert_one({USER_ID: str(booked_member_1_id), CLASS_ID: class_id_str})
    bookings_col.insert_one({USER_ID: str(booked_member_1_id), CLASS_ID: class_id_str})  #duplicate
    bookings_col.insert_one({USER_ID: str(booked_member_2_id), CLASS_ID: class_id_str})

    return {
        "class_id": class_id_str,
        "trainer_id": str(trainer_id),
        "member_id": str(member_id),
        "booked_member_1_id": str(booked_member_1_id),
        "booked_member_2_id": str(booked_member_2_id),
    }


def test_view_class_members_success_unique(app_client, seed_class_and_users):
    class_id = seed_class_and_users["class_id"]
    trainer_id = seed_class_and_users["trainer_id"]
    headers = _auth_headers(app_client, trainer_id)

    resp = app_client.get(f"/classes/{class_id}/members", headers=headers)
    assert resp.status_code == 200

    body = resp.get_json()
    assert MSG in body
    members = body[MSG]
    assert isinstance(members, list)

    #ensure unique members (no duplicates)
    emails = [m.get("email") for m in members]
    assert len(emails) == len(set(emails))
    assert set(emails) == {"booked1@example.com", "booked2@example.com"}


def test_view_class_members_forbidden_for_member(app_client, seed_class_and_users):
    class_id = seed_class_and_users["class_id"]
    member_id = seed_class_and_users["member_id"]
    headers = _auth_headers(app_client, member_id)

    resp = app_client.get(f"/classes/{class_id}/members", headers=headers)
    assert resp.status_code == 403
    assert resp.get_json()[MSG] == "Only trainers or admins can view class members"


def test_view_class_members_class_not_found(app_client, seed_class_and_users):
    trainer_id = seed_class_and_users["trainer_id"]
    headers = _auth_headers(app_client, trainer_id)

    non_existent_class_id = str(ObjectId())
    resp = app_client.get(f"/classes/{non_existent_class_id}/members", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()[MSG] == "Class not found"

def test_view_class_members_empty_class(app_client, seed_class_and_users):
    #valid class with no bookings should return 200 with an empty list
    trainer_id = seed_class_and_users["trainer_id"]
    headers = _auth_headers(app_client, trainer_id)

    #insert a new class with no bookings
    classes_col = DB.get_collection("classes")
    empty_class_id = ObjectId()
    classes_col.insert_one({
        "_id": empty_class_id,
        class_name: "Pilates",
        start_time: (datetime.now() + timedelta(days=3)).isoformat(),
        end_time: (datetime.now() + timedelta(days=3, hours=1)).isoformat(),
        location: "Room B",
        capacity: 10,
        remaining_spots: 10,
        trainer_name: "Trainer Name",
    })

    resp = app_client.get(f"/classes/{str(empty_class_id)}/members", headers=headers) #make the API call
    assert resp.status_code == 200
    assert resp.get_json()[MSG] == []


def test_view_class_members_calls_booking_lookup(app_client, seed_class_and_users):
    #MagicMock to verify that the endpoint asks BookingResource for bookings for the given class id.
    class_id = seed_class_and_users["class_id"]
    trainer_id = seed_class_and_users["trainer_id"]
    headers = _auth_headers(app_client, trainer_id)

    with patch( #patch BookingResource.get_class_bookings to return an empty list
        "app.apis.classes.BookingResource.get_class_bookings",
        MagicMock(return_value=[]),
    ) as mock_get_class_bookings: 
        resp = app_client.get(f"/classes/{class_id}/members", headers=headers) #make the API call

    assert resp.status_code == 200
    mock_get_class_bookings.assert_called_once_with(class_id)


def test_view_class_members_unauthenticated(app_client, seed_class_and_users): #missing JWT should be caught by the NoAuthorizationError handler -- 401
    class_id = seed_class_and_users["class_id"]

    resp = app_client.get(f"/classes/{class_id}/members")
    assert resp.status_code == 401

