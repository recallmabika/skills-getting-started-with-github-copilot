"""Pytest configuration and fixtures for the FastAPI app tests."""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


# Store a deep copy of the original activities for resetting between tests
original_activities = copy.deepcopy(activities)


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test."""
    # Reset to original state before test
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    
    yield
    
    # Reset to original state after test
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
