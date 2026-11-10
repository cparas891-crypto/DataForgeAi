from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_dashboard():

    response = client.get("/")

    assert response.status_code == 200
    assert "DataForge AI" in response.text


def test_upload_page():

    response = client.get("/upload")

    assert response.status_code == 200
    assert "Upload" in response.text


def test_dataset_history():

    response = client.get("/datasets")

    assert response.status_code == 200
    assert "Dataset" in response.text


def test_cleaning_studio():

    response = client.get("/clean")

    assert response.status_code == 200
    assert "Cleaning Studio" in response.text


def test_analytics():

    response = client.get("/analytics")

    assert response.status_code == 200
    assert "Analytics" in response.text


def test_ai_analyst():

    response = client.get("/ai")

    assert response.status_code == 200
    assert "AI Analyst" in response.text


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "DataForge AI"
    assert data["status"] in [
        "healthy",
        "degraded"
    ]

    assert "database" in data
    assert "templates" in data
    assert "packaged" in data


def test_invalid_route():

    response = client.get(
        "/this-route-does-not-exist"
    )

    assert response.status_code == 404