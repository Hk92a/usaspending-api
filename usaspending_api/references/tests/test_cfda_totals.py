import pytest
from rest_framework import status


def mock_api_response(monkeypatch, status, json_data):
    class MockResponse:
        def __init__(self, status, json_data):
            self.status = status
            self.json_data = json_data

        @property
        def status_code(self):
            return self.status

        def json(self):
            return self.json_data

    monkeypatch.setattr(
        "usaspending_api.references.v2.views.cfda.post", lambda *args, **kwargs: MockResponse(status, json_data)
    )


@pytest.mark.django_db
def test_api_err(client, monkeypatch):
    mock_api_response(monkeypatch=monkeypatch, status=status.HTTP_200_OK, json_data={"errorMsgs": ["error msg"]})
    response = client.get("/api/v2/references/cfda/totals/")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        response.json()["detail"]
        == "Error returned by https://www.grants.gov/grantsws/rest/opportunities/search/cfda/totals: ['error msg']"
    )


@pytest.mark.django_db
def test_service_unavailable(client, monkeypatch):
    mock_api_response(monkeypatch=monkeypatch, status=status.HTTP_503_SERVICE_UNAVAILABLE, json_data={})
    response = client.get("/api/v2/references/cfda/totals/")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert (
        response.json()["detail"]
        == "https://www.grants.gov/grantsws/rest/opportunities/search/cfda/totals not available (status 503)"
    )


@pytest.mark.django_db
def test_bad_format(client, monkeypatch):
    mock_api_response(
        monkeypatch=monkeypatch,
        status=status.HTTP_200_OK,
        json_data={
            "cfdas": {"00.000": {"code": "00.000", "posted": 1, "closed": 3, "archived": 962, "forecasted": 0}},
            "errorMsgs": [],
        },
    )
    response = client.get("/api/v2/references/cfda/totals/00.000/")
    print(response.json())
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        response.json()["detail"]
        == "Dictionary from https://www.grants.gov/grantsws/rest/opportunities/search/cfda/totals not in expected format: {'code': '00.000', 'posted': 1, 'closed': 3, 'archived': 962, 'forecasted': 0}"
    )


@pytest.mark.django_db
def test_code_not_found(client, monkeypatch):
    mock_api_response(
        monkeypatch=monkeypatch,
        status=status.HTTP_200_OK,
        json_data={
            "cfdas": {"00.000": {"cfda": "00.000", "posted": 1, "closed": 3, "archived": 962, "forecasted": 0}},
            "errorMsgs": [],
        },
    )
    response = client.get("/api/v2/references/cfda/totals/0.1/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
