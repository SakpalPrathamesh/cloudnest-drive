"""
Test 1: Make sure the backend is alive and responding.
"""


def test_health_check(client):
    """
    GIVEN: Flask app is running
    WHEN:  GET /api/health is called
    THEN:  Response should be 200 OK with status "ok"
    """
    response = client.get("/api/health")

    # Check status code
    assert response.status_code == 200, \
        f"Expected 200 but got {response.status_code}"

    # Check response content
    data = response.get_json()
    assert data["status"] == "ok", \
        f"Expected 'ok' but got {data['status']}"

    print("✅ Health check passed!")


def test_unknown_route_returns_404(client):
    """
    GIVEN: Flask app is running
    WHEN:  A route that doesn't exist is called
    THEN:  Should return 404
    """
    response = client.get("/api/this-does-not-exist")

    assert response.status_code == 404, \
        f"Expected 404 but got {response.status_code}"

    print("✅ 404 handling works!")