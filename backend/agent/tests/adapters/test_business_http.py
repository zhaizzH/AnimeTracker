"""Tests for adapters.business_http."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from app.adapters.business_http import HttpBusinessGateway


class TestBatchEvidence:
    def test_calls_correct_endpoint(self):
        gw = HttpBusinessGateway("http://localhost:8080")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.request", return_value=mock_resp) as mock_request:
            gw.batch_evidence([1, 2, 3], token="test-token")

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args.args[0] == "POST"
        assert call_args.args[1] == "http://localhost:8080/api/client/evidence/batch"
        assert call_args.kwargs["json"] == {"subjectIds": [1, 2, 3]}
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-token"

    def test_returns_data_field(self):
        gw = HttpBusinessGateway("http://localhost:8080")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"subjectId": 1, "name": "Test"}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.request", return_value=mock_resp):
            result = gw.batch_evidence([1], token=None)

        assert result == [{"subjectId": 1, "name": "Test"}]

    def test_handles_timeout(self):
        import httpx
        gw = HttpBusinessGateway("http://localhost:8080")

        with patch("httpx.request", side_effect=httpx.TimeoutException("timeout")):
            result = gw.batch_evidence([1], token=None)

        assert result == {"error": True, "message": "后端服务超时"}

    def test_handles_connection_error(self):
        import httpx
        gw = HttpBusinessGateway("http://localhost:8080")

        with patch("httpx.request", side_effect=httpx.ConnectError("refused")):
            result = gw.batch_evidence([1], token=None)

        assert result["error"] is True
        assert "不可用" in result["message"]
