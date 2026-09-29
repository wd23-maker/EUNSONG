import asyncio

import httpx
import pytest

from naver_mcp.client import NaverAPIError, NaverSearchClient, clean_text


def make_client(handler):
    return NaverSearchClient("id", "secret", http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def test_clean_text():
    assert clean_text("<b>강남</b> 맛집 &quot;추천&quot;") == '강남 맛집 "추천"'


def test_blog_sends_auth_headers_and_cleans_items():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = request.url
        seen["headers"] = request.headers
        return httpx.Response(200, json={
            "total": 1, "start": 1, "display": 1,
            "items": [{"title": "<b>제주</b> 여행", "link": "https://blog.naver.com/x/1", "postdate": "20260929"}],
        })

    result = asyncio.run(make_client(handler).blog("제주 여행", display=500, sort="date"))
    assert seen["url"].path == "/v1/search/blog.json"
    assert seen["url"].params["display"] == "100"  # 최대값으로 제한
    assert seen["url"].params["sort"] == "date"
    assert seen["headers"]["X-Naver-Client-Id"] == "id"
    assert seen["headers"]["X-Naver-Client-Secret"] == "secret"
    assert result["items"][0]["title"] == "제주 여행"


def test_endpoints():
    paths = []

    def handler(request: httpx.Request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"items": []})

    c = make_client(handler)
    asyncio.run(c.cafe("a"))
    asyncio.run(c.web("a"))
    asyncio.run(c.local("a"))
    assert paths == ["/v1/search/cafearticle.json", "/v1/search/webkr.json", "/v1/search/local.json"]


def test_local_limits_and_coordinates():
    def handler(request: httpx.Request):
        assert request.url.params["display"] == "5"
        assert request.url.params["start"] == "1"
        return httpx.Response(200, json={"items": [
            {"title": "<b>카페</b>", "mapx": "1270276000", "mapy": "374979000"},
        ]})

    item = asyncio.run(make_client(handler).local("강남역 카페", display=20))["items"][0]
    assert item["title"] == "카페"
    assert item["longitude"] == pytest.approx(127.0276)
    assert item["latitude"] == pytest.approx(37.4979)


def test_error_response():
    def handler(request):
        return httpx.Response(401, json={"errorMessage": "Authentication failed", "errorCode": "024"})

    with pytest.raises(NaverAPIError, match="024"):
        asyncio.run(make_client(handler).blog("x"))


def test_missing_credentials(monkeypatch):
    monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
    monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
    with pytest.raises(NaverAPIError, match="환경변수"):
        asyncio.run(NaverSearchClient().web("x"))


def test_connection_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(NaverAPIError, match="연결하지 못했습니다"):
        asyncio.run(make_client(handler).blog("x"))
