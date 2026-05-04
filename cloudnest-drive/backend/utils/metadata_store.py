"""
Metadata Store — remembers file info in memory.
Note: This resets when the server restarts.
In production, replace with a real database like Firestore.
"""

from datetime import datetime
from threading import Lock

# This is our "database" for now — just a Python dictionary
# Structure: { "user_id": [ {file info}, {file info} ] }
_store = {}
_lock = Lock()


def save_file_metadata(user_id: str, metadata: dict) -> dict:
    """Save info about an uploaded file"""
    record = {
        "s3_key":       metadata["s3_key"],
        "filename":     metadata["filename"],
        "size":         metadata["size"],
        "content_type": metadata.get("content_type", "application/octet-stream"),
        "uploaded_at":  datetime.utcnow().isoformat(),
        "user_id":      user_id,
    }

    with _lock:
        if user_id not in _store:
            _store[user_id] = []

        # Update if file already exists, else add new
        existing = next(
            (f for f in _store[user_id] if f["s3_key"] == record["s3_key"]),
            None
        )
        if existing:
            existing.update(record)
        else:
            _store[user_id].append(record)

    return record


def get_user_files(user_id: str) -> list:
    """Get all files for a user"""
    with _lock:
        return list(_store.get(user_id, []))


def delete_file_metadata(user_id: str, s3_key: str) -> bool:
    """Remove a file's info from the store"""
    with _lock:
        if user_id not in _store:
            return False
        before = len(_store[user_id])
        _store[user_id] = [
            f for f in _store[user_id] if f["s3_key"] != s3_key
        ]
        return len(_store[user_id]) < before