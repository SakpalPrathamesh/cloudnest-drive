"""
conftest.py — Sets up the test environment.
pytest automatically reads this file before running any tests.
"""
import pytest
import sys
import os

# Make sure Python can find our backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture
def app():
    """Create a test version of the Flask app."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """
    Create a test client.
    This lets us send fake HTTP requests without a real browser.
    """
    return app.test_client()