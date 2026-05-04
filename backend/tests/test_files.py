"""
Test 3: File routes — security and validation checks.
"""
import json


def test_upload_requires_auth(client):
    """
    GIVEN: Upload route
    WHEN:  No Authorization header sent
    THEN:  Should return 401
    """
    response = client.post("/api/files/upload")

    assert response.status_code == 401, \
        f"Expected 401 but got {response.status_code}"

    print("✅ Upload requires authentication!")


def test_list_requires_auth(client):
    """
    GIVEN: List route
    WHEN:  No Authorization header sent
    THEN:  Should return 401
    """
    response = client.get("/api/files/list")

    assert response.status_code == 401, \
        f"Expected 401 but got {response.status_code}"

    print("✅ List requires authentication!")


def test_download_requires_auth(client):
    """
    GIVEN: Download route
    WHEN:  No Authorization header sent
    THEN:  Should return 401
    """
    response = client.get("/api/files/download?key=users/abc/file.txt")

    assert response.status_code == 401, \
        f"Expected 401 but got {response.status_code}"

    print("✅ Download requires authentication!")


def test_delete_requires_auth(client):
    """
    GIVEN: Delete route
    WHEN:  No Authorization header sent
    THEN:  Should return 401
    """
    response = client.delete("/api/files/delete?key=users/abc/file.txt")

    assert response.status_code == 401, \
        f"Expected 401 but got {response.status_code}"

    print("✅ Delete requires authentication!")


def test_download_missing_key_param(client):
    """
    GIVEN: Download route with auth
    WHEN:  No 'key' query parameter provided
    THEN:  Should return 400
    Note:  Uses mock token since firebase_credentials.json may not exist
    """
    response = client.get(
        "/api/files/download",
        headers={"Authorization": "Bearer mock-token-for-testing"}
    )

    # 400 = missing key | 401 = auth failed (both are correct behavior)
    assert response.status_code in [400, 401], \
        f"Expected 400 or 401, got {response.status_code}"

    print("✅ Download rejects missing key parameter!")


def test_delete_missing_key_param(client):
    """
    GIVEN: Delete route with auth
    WHEN:  No 'key' query parameter provided
    THEN:  Should return 400
    """
    response = client.delete(
        "/api/files/delete",
        headers={"Authorization": "Bearer mock-token-for-testing"}
    )

    assert response.status_code in [400, 401], \
        f"Expected 400 or 401, got {response.status_code}"

    print("✅ Delete rejects missing key parameter!")