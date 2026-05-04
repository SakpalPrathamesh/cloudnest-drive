"""
File Routes — handles upload, list, download, delete
"""
import logging
from flask import Blueprint, request, jsonify, g
from utils.firebase_utils import require_auth
from utils.s3_utils import (
    upload_file_to_s3,
    list_user_files_from_s3,
    generate_presigned_download_url,
    delete_file_from_s3,
)
from utils.metadata_store import (
    save_file_metadata,
    get_user_files,
    delete_file_metadata,
)

logger = logging.getLogger(__name__)
file_bp = Blueprint("files", __name__)


@file_bp.route("/upload", methods=["POST"])
@require_auth
def upload_file():
    """
    Upload a file to S3.
    Request: multipart/form-data with a 'file' field.
    """
    # Check a file was actually sent
    if "file" not in request.files:
        return jsonify({"error": "No file was sent. Use field name 'file'."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    try:
        # Upload to S3
        result = upload_file_to_s3(file, g.user_id, file.filename)

        # Save metadata so we remember it
        metadata = save_file_metadata(g.user_id, result)

        return jsonify({
            "success": True,
            "message": f"'{file.filename}' uploaded!",
            "file": metadata
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@file_bp.route("/list", methods=["GET"])
@require_auth
def list_files():
    """
    Get all files belonging to the logged-in user.
    """
    try:
        # Get files directly from S3
        files = list_user_files_from_s3(g.user_id)

        # Merge with local metadata to get uploaded_at time
        local = {f["s3_key"]: f for f in get_user_files(g.user_id)}
        for f in files:
            if f["s3_key"] in local:
                f["uploaded_at"] = local[f["s3_key"]].get("uploaded_at", "")

        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        }), 200

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@file_bp.route("/download", methods=["GET"])
@require_auth
def download_file():
    """
    Generate a temporary download link for a file.
    Usage: GET /api/files/download?key=users/uid/filename.pdf
    """
    s3_key = request.args.get("key", "").strip()

    if not s3_key:
        return jsonify({"error": "Missing 'key' parameter"}), 400

    # Security: only allow downloading your own files
    if not s3_key.startswith(f"users/{g.user_id}/"):
        return jsonify({"error": "Access denied."}), 403

    try:
        url = generate_presigned_download_url(s3_key)
        return jsonify({
            "success": True,
            "download_url": url,
            "expires_in": 3600
        }), 200

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@file_bp.route("/delete", methods=["DELETE"])
@require_auth
def delete_file():
    """
    Delete a file from S3.
    Usage: DELETE /api/files/delete?key=users/uid/filename.pdf
    """
    s3_key = request.args.get("key", "").strip()

    if not s3_key:
        return jsonify({"error": "Missing 'key' parameter"}), 400

    try:
        delete_file_from_s3(s3_key, g.user_id)
        delete_file_metadata(g.user_id, s3_key)

        return jsonify({
            "success": True,
            "message": "File deleted."
        }), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500