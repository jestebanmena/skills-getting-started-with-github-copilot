import copy

import copy

import pytest
from fastapi.testclient import TestClient
import src.app as app_module
from src.app import app, activities as activities_template


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activity state before each test."""
    app_module.activities = copy.deepcopy(activities_template)


@pytest.fixture
def client():
    """Fixture providing a TestClient for making requests to the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_activity_name():
    """Fixture providing a sample activity name for testing."""
    return "Chess Club"


@pytest.fixture
def test_email():
    """Fixture providing a test email address."""
    return "student@example.com"


@pytest.fixture
def additional_test_email():
    """Fixture providing an additional test email address."""
    return "another_student@example.com"
