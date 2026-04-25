from http import HTTPStatus
from app.apis import MSG
from datetime import datetime, timedelta
from tests.unit.test_helpers import build_valid_class, create_class

DAILY_RECURRENCE = "daily"
WEEKLY_RECURRENCE = "weekly"
RECURRENCE_END_DATE = "recurrence_end_date"


def build_valid_recurring_class(recurrence_type):
  class_payload = build_valid_class()
  class_payload["recurrence_type"] = recurrence_type
  class_payload[RECURRENCE_END_DATE] = (datetime.now()+timedelta(days=7)).isoformat(timespec="seconds")
  return class_payload

def test_create_daily_recurring_classes_success(app_client):
  class_payload = build_valid_recurring_class(DAILY_RECURRENCE)
  
  response = create_class(app_client, class_payload)
  
  assert response.status_code == HTTPStatus.OK
  assert "Recurring classes created with ids" in response.json[MSG]

def test_create_weekly_recurring_classes_success(app_client):
  class_payload = build_valid_recurring_class(WEEKLY_RECURRENCE)
  
  response = create_class(app_client, class_payload)
  
  assert response.status_code == HTTPStatus.OK
  assert "Recurring classes created with ids" in response.json[MSG]

def test_create_recurring_class_with_invalid_recurrence_type_fails(app_client):
  class_payload = build_valid_recurring_class("yearly")
  
  response = create_class(app_client, class_payload)
  
  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE

def test_create_recurring_class_without_recurrence_type_creates_single_class(app_client):
  class_payload = build_valid_class()
  class_payload[RECURRENCE_END_DATE] = (
    datetime.now() +timedelta(days = 7)
  ).isoformat(timespec= "seconds")
  
  response = create_class(app_client, class_payload)
  
  assert response.status_code == HTTPStatus.OK
  assert "Class created with id" in response.json[MSG]

def test_create_recurring_class_with_invalid_recurrence_end_date_fails(app_client):
  class_payload = build_valid_recurring_class(DAILY_RECURRENCE)
  class_payload[RECURRENCE_END_DATE] = "not-a-date"

  response = create_class(app_client, class_payload)

  assert response.status_code == HTTPStatus.NOT_ACCEPTABLE