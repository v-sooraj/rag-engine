from fastapi.testclient import TestClient


def test_openapi_documentation_is_available(
    client: TestClient,
):
    response = client.get(
        "/docs"
    )

    assert response.status_code == 200


def test_openapi_schema_is_available(
    client: TestClient,
):
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200