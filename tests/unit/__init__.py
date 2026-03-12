import os

import mongomock
import pytest

# Ensure required env vars are set BEFORE app.config.Config is imported
os.environ.setdefault("MONGO_URI", "mongodb://localhost/test")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("MOCK_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET_KEY", "this-is-a-long-enough-secret-key-for-testing")


@pytest.fixture
def mock_db():
    #Generic mongomock-backed DB fixture for unit tests that need direct DB access.
    #Note: tests that use the Flask app should go through app.db.DB instead.
    client = mongomock.MongoClient()
    db = client["test_db"]
    return db