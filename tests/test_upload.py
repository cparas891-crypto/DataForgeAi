from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_csv_upload():

    csv_data = (
        "name,score\n"
        "Alice,90\n"
        "Bob,85\n"
        "Charlie,95\n"
    )

    files = {
        "file": (
            "test_upload.csv",
            csv_data,
            "text/csv"
        )
    }

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 200

    assert "test_upload.csv" in response.text

    assert "Alice" in response.text

    assert "Bob" in response.text


def test_json_upload():

    json_data = """
    [
        {
            "name": "Alice",
            "score": 90
        },
        {
            "name": "Bob",
            "score": 85
        }
    ]
    """

    files = {
        "file": (
            "test_upload.json",
            json_data,
            "application/json"
        )
    }

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 200

    assert "test_upload.json" in response.text

    assert "Alice" in response.text


def test_reject_unsupported_file():

    files = {
        "file": (
            "malware.exe",
            b"not actually an executable",
            "application/octet-stream"
        )
    }

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 400

    assert "Unsupported file type" in response.text


def test_reject_empty_csv():

    files = {
        "file": (
            "empty.csv",
            b"",
            "text/csv"
        )
    }

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 400

    assert "empty" in response.text.lower()