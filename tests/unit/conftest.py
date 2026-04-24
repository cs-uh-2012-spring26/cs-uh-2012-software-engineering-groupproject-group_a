import os
import pytest
from app import create_app
from app.db import DB

@pytest.fixture(scope ="module")
def app_client():
  os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
  os.environ.setdefault("DB_NAME", "test_db")
  os.environ.setdefault("MOCK_DB", "true")
  os.environ.setdefault("DEBUG", "true")

  app = create_app()
  app.config["TESTING"] = True
  app.config["JWT_SECRET_KEY"] = "test-secret-key"

  with app.app_context():
    yield app.test_client()

@pytest.fixture(autouse=True)
def clear_classes_collection():
  classes_col = DB.get_collection("classes")
  classes_col.delete_many({})

