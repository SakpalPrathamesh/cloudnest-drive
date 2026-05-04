import os
import json
import logging
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

_firebase_app = None

def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        try:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app
        except ValueError:
            pass

        # Option 1: Load from JSON file (local development)
        cred_path = os.getenv(
            "FIREBASE_CREDENTIALS_PATH",
            "firebase_credentials.json"
        )

        # Option 2: Load from environment variable (production)
        cred_json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if cred_json_str:
            # Parse the JSON string from environment variable
            import json
            cred_dict = json.loads(cred_json_str)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from environment variable.")

        elif os.path.exists(cred_path):
            # Load from local file
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from credentials file.")

        else:
            logger.warning("No Firebase credentials found. MOCK mode active.")
            _firebase_app = "MOCK"

        return _firebase_app

    except ImportError:
        logger.error("firebase-admin not installed.")
        _firebase_app = "MOCK"
        return _firebase_app


def verify_firebase_token(id_token: str) -> dict:
    app = _get_firebase_app()

    if app == "MOCK":
        logger.warning("MOCK mode: skipping real token verification.")
        return {
            "uid": "mock-user-123",
            "email": "mockuser@cloudnest.dev"
        }

    try:
        from firebase_admin import auth
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing Authorization header"}), 401

        id_token = auth_header.split("Bearer ")[1].strip()

        try:
            decoded = verify_firebase_token(id_token)
            g.user_id = decoded.get("uid")
            g.user_email = decoded.get("email", "unknown")
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated_function