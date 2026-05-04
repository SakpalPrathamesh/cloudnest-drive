"""
Test 4: Metadata store — save, get, delete file info.
This tests our in-memory "database" directly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.metadata_store import (
    save_file_metadata,
    get_user_files,
    delete_file_metadata,
)


def test_save_and_get_metadata():
    """
    GIVEN: A user uploads a file
    WHEN:  Metadata is saved
    THEN:  We can retrieve it back
    """
    user_id = "test-user-001"

    # Save some file metadata
    saved = save_file_metadata(user_id, {
        "s3_key":      f"users/{user_id}/hello.txt",
        "filename":    "hello.txt",
        "size":        1024,
        "content_type": "text/plain"
    })

    # Check save returned the record
    assert saved["filename"] == "hello.txt", \
        "Saved filename should match"
    assert saved["size"] == 1024, \
        "Saved size should match"
    assert "uploaded_at" in saved, \
        "Should have uploaded_at timestamp"

    # Now retrieve it
    files = get_user_files(user_id)
    assert len(files) >= 1, \
        "Should have at least 1 file"

    # Find our file in the list
    found = next(
        (f for f in files if f["filename"] == "hello.txt"),
        None
    )
    assert found is not None, \
        "Should find the file we saved"

    print("✅ Save and get metadata works!")


def test_delete_metadata():
    """
    GIVEN: A file was saved
    WHEN:  We delete it
    THEN:  It should no longer appear in the list
    """
    user_id = "test-user-002"
    s3_key  = f"users/{user_id}/delete-me.pdf"

    # Save it first
    save_file_metadata(user_id, {
        "s3_key":       s3_key,
        "filename":     "delete-me.pdf",
        "size":         2048,
        "content_type": "application/pdf"
    })

    # Confirm it exists
    files_before = get_user_files(user_id)
    assert any(f["s3_key"] == s3_key for f in files_before), \
        "File should exist before deletion"

    # Delete it
    result = delete_file_metadata(user_id, s3_key)
    assert result is True, \
        "delete_file_metadata should return True on success"

    # Confirm it's gone
    files_after = get_user_files(user_id)
    assert not any(f["s3_key"] == s3_key for f in files_after), \
        "File should NOT exist after deletion"

    print("✅ Delete metadata works!")


def test_users_files_are_separate():
    """
    GIVEN: Two different users upload files
    WHEN:  We get files for user A
    THEN:  We should NOT see user B's files
    This tests our per-user isolation!
    """
    user_a = "user-aaa-111"
    user_b = "user-bbb-222"

    # User A uploads a file
    save_file_metadata(user_a, {
        "s3_key":       f"users/{user_a}/user-a-secret.txt",
        "filename":     "user-a-secret.txt",
        "size":         500,
        "content_type": "text/plain"
    })

    # User B uploads a file
    save_file_metadata(user_b, {
        "s3_key":       f"users/{user_b}/user-b-secret.txt",
        "filename":     "user-b-secret.txt",
        "size":         600,
        "content_type": "text/plain"
    })

    # Get User A's files
    user_a_files = get_user_files(user_a)

    # Make sure User B's file is NOT in User A's list
    filenames_a = [f["filename"] for f in user_a_files]
    assert "user-b-secret.txt" not in filenames_a, \
        "User A should NOT see User B's files!"

    print("✅ User isolation works — files are not shared between users!")


def test_empty_user_returns_empty_list():
    """
    GIVEN: A brand new user who has never uploaded
    WHEN:  We get their files
    THEN:  Should return an empty list (not an error)
    """
    files = get_user_files("brand-new-user-xyz-999")

    assert isinstance(files, list), \
        "Should return a list"
    assert len(files) == 0, \
        "New user should have 0 files"

    print("✅ New user gets empty list!")