"""
Auth Routes — handles token verification
"""
import logging
from flask import Blueprint, request, jsonify, g
from utils.firebase_utils import require_auth, verify_firebase_token

logger = logging.getLogger(__name__)

# A Blueprint is like a mini Flask app — keeps routes organized
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/verify", methods=["POST"])
def verify_token():
    """
    Frontend sends Firebase token here after login.
    We check it's valid and return user info.
    """
    data = request.get_json(silent=True)

    if not data or "idToken" not in data:
        return jsonify({"error": "Please send an idToken"}), 400

    id_token = data["idToken"].strip()

    try:
        decoded = verify_firebase_token(id_token)
        return jsonify({
            "success": True,
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """
    Returns info about the currently logged-in user.
    Requires: Authorization: Bearer <token> header
    """
    return jsonify({
        "uid": g.user_id,
        "email": g.user_email,
    }), 200