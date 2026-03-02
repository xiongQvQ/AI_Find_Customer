"""
Tests for core/search_client.py

All tests are offline — real HTTP calls are mocked.
Run with:
    python -m pytest tests/test_search_client.py -v
"""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── helpers ────────────────────────────────────────────────────────────────

def _serper_resp(results):
    """Build a fake requests.Response for Serper."""
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"organic": results}
    return mock


def _tavily_resp(results):
    """Return a fake Tavily client.search() response."""
    return {"results": results}


# ── get_search_provider / is_search_available ──────────────────────────────

class TestSearchProviderConfig:
    def test_defaults_to_serper(self, monkeypatch):
        monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.get_search_provider() == "serper"

    def test_reads_tavily(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.get_search_provider() == "tavily"

    def test_is_available_serper_true(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "test-key")
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.is_search_available() is True

    def test_is_available_serper_false(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.delenv("SERPER_API_KEY", raising=False)
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.is_search_available() is False

    def test_is_available_tavily_true(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.is_search_available() is True

    def test_is_available_tavily_false(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        assert sc.is_search_available() is False


# ── Serper search ──────────────────────────────────────────────────────────

class TestSerperSearch:
    def test_returns_normalised_results(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "test-key")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        fake_items = [
            {"title": "Acme Corp", "link": "https://www.acme.com/page", "snippet": "We sell pumps."},
            {"title": "Beta Ltd",  "link": "https://beta.de/about",     "snippet": "German supplier."},
        ]
        with patch("requests.post", return_value=_serper_resp(fake_items)):
            results = sc.search("hydraulic pump Germany", num_results=5, gl="de")

        assert len(results) == 2
        assert results[0]["title"] == "Acme Corp"
        assert results[0]["domain"] == "acme.com"
        assert results[0]["provider"] == "serper"
        assert results[1]["domain"] == "beta.de"

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.delenv("SERPER_API_KEY", raising=False)
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        try:
            sc.search("test query")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "SERPER_API_KEY" in str(e)

    def test_retries_on_failure(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "test-key")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        call_count = {"n": 0}
        def _fail(*a, **kw):
            call_count["n"] += 1
            raise Exception("network error")

        with patch("requests.post", side_effect=_fail):
            with patch("time.sleep"):  # skip actual sleeps
                try:
                    sc.search("test", retries=3)
                except RuntimeError:
                    pass
        assert call_count["n"] == 3

    def test_limits_num_results(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "test-key")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        # serper caps at 20
        captured = {}
        def _mock_post(url, headers, json, timeout):
            captured["num"] = json.get("num")
            return _serper_resp([])
        with patch("requests.post", side_effect=_mock_post):
            sc.search("test", num_results=50, gl="us")
        assert captured["num"] == 20

    def test_domain_extracted_correctly(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "serper")
        monkeypatch.setenv("SERPER_API_KEY", "key")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        items = [{"title": "T", "link": "https://www.example.co.uk/path?q=1", "snippet": "s"}]
        with patch("requests.post", return_value=_serper_resp(items)):
            results = sc.search("q")
        assert results[0]["domain"] == "example.co.uk"


# ── Tavily search ──────────────────────────────────────────────────────────

class TestTavilySearch:
    def test_returns_normalised_results(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        fake_items = [
            {"title": "Solar Co", "url": "https://solar.de/home", "content": "Solar panels.", "score": 0.9},
            {"title": "Wind Ltd", "url": "https://wind.pl/about", "content": "Wind turbines.", "score": 0.7},
        ]

        mock_client = MagicMock()
        mock_client.search.return_value = _tavily_resp(fake_items)

        with patch("tavily.TavilyClient", return_value=mock_client):
            results = sc.search("solar inverter Poland", num_results=5)

        assert len(results) == 2
        assert results[0]["title"] == "Solar Co"
        assert results[0]["domain"] == "solar.de"
        assert results[0]["score"] == 0.9
        assert results[0]["provider"] == "tavily"

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        try:
            sc.search("test")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "TAVILY_API_KEY" in str(e)

    def test_score_defaults_to_zero(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
        from importlib import reload
        import core.search_client as sc
        reload(sc)

        items = [{"title": "T", "url": "https://example.com", "content": "c"}]  # no score
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": items}
        with patch("tavily.TavilyClient", return_value=mock_client):
            results = sc.search("q")
        assert results[0]["score"] == 0.0


# ── _extract_domain helper ─────────────────────────────────────────────────

class TestExtractDomain:
    def setup_method(self):
        from importlib import reload
        import core.search_client as sc
        reload(sc)
        self._extract = sc._extract_domain

    def test_basic_https(self):
        assert self._extract("https://www.example.com/page") == "example.com"

    def test_http(self):
        assert self._extract("http://shop.acme.co.uk/products") == "shop.acme.co.uk"

    def test_no_www(self):
        assert self._extract("https://beta.de/") == "beta.de"

    def test_empty(self):
        assert self._extract("") == ""

    def test_non_url(self):
        assert self._extract("just text") == ""
