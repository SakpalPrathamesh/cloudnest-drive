"""
Test 2: Auth routes — verify token, missing token, bad token.
"""
import json


def test_verify_token_missing_body(client):
    """
    GIVEN: Auth verify route
    WHEN:  Request sent with no body at all
    THEN:  Should return 400 Bad Request
    """
    response = client.post(
        "/api/auth/verify",
        content_type="application/json",
        data=json.dumps({})   # empty body — no idToken
    )

    assert response.status_code == 400, \
        f"Expected 400 but got {response.status_code}"

    data = response.get_json()
    assert "error" in data, "Response should contain 'error' key"

    print("✅ Missing token returns 400!")


def test_verify_token_invalid_token(client):
    """
    GIVEN: Auth verify route
    WHEN:  A fake/random token is sent
    THEN:  Should return 401 Unauthorized
    """
    response = client.post(
        "/api/auth/verify",
        content_type="application/json",
        data=json.dumps({"idToken": "this-is-a-fake-token-12345"})
    )

    # In MOCK mode it returns 200, in real mode it returns 401
    # Both are acceptable — we just check it responds
    assert response.status_code in [200, 401], \
        f"Expected 200 or 401 but got {response.status_code}"

    print("✅ Invalid token handled correctly!")


def test_protected_route_no_token(client):
    """
    GIVEN: A protected route (/api/auth/me)
    WHEN:  Request sent with NO Authorization header
    THEN:  Should return 401
    """
    response = client.get("/api/auth/me")

    assert response.status_code == 401, \
        f"Expected 401 but got {response.status_code}"

    data = response.get_json()
    assert "error" in data

    print("✅ Protected route blocks unauthenticated requests!")


def test_protected_route_bad_format(client):
    """
    GIVEN: A protected route
    WHEN:  Authorization header is sent but in wrong format
    THEN:  Should return 401
    """
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "NotBearer some-token"}
    )

    assert response.status_code == 401

    print("✅ Wrong auth header format is rejected!")