"""네이버 검색 Open API 클라이언트.

API 문서: https://developers.naver.com/docs/serviceapi/search/blog/blog.md
"""

from __future__ import annotations

import html
import os
import re
from typing import Any

import httpx

BASE_URL = "https://openapi.naver.com/v1/search"
_TAG_RE = re.compile(r"<[^>]+>")


class NaverAPIError(RuntimeError):
    """네이버 API가 오류 응답을 돌려줬을 때 발생합니다."""


def clean_text(value: str) -> str:
    """검색어 강조용 <b> 태그와 HTML 엔티티(&quot; 등)를 제거합니다."""
    return html.unescape(_TAG_RE.sub("", value)).strip()


def _clean_item(item: dict[str, Any]) -> dict[str, Any]:
    return {k: clean_text(v) if isinstance(v, str) else v for k, v in item.items()}


def _add_coordinates(item: dict[str, Any]) -> dict[str, Any]:
    """지역 검색의 mapx/mapy(WGS84 좌표 × 10^7 정수)를 위경도로 변환해 덧붙입니다."""
    try:
        x, y = int(item["mapx"]), int(item["mapy"])
    except (KeyError, TypeError, ValueError):
        return item
    # 구형 KATEC 좌표(수십만 단위)는 변환하지 않고 원본만 둡니다.
    if abs(x) > 10_000_000 and abs(y) > 10_000_000:
        item["longitude"] = x / 1e7
        item["latitude"] = y / 1e7
    return item


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


class NaverSearchClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("NAVER_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("NAVER_CLIENT_SECRET", "")
        self._http = http or httpx.AsyncClient(timeout=10.0)

    async def _search(self, kind: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise NaverAPIError(
                "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다."
            )
        try:
            response = await self._http.get(
                f"{BASE_URL}/{kind}.json",
                params=params,
                headers={
                    "X-Naver-Client-Id": self.client_id,
                    "X-Naver-Client-Secret": self.client_secret,
                },
            )
        except httpx.HTTPError as e:
            raise NaverAPIError(f"네이버 API에 연결하지 못했습니다: {e!r}") from e
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code != 200:
            code = data.get("errorCode", response.status_code)
            message = data.get("errorMessage", response.text[:200])
            raise NaverAPIError(f"네이버 API 오류 ({code}): {message}")
        return {
            "total": data.get("total", 0),
            "start": data.get("start", params.get("start", 1)),
            "display": data.get("display", 0),
            "items": [_clean_item(item) for item in data.get("items", [])],
        }

    async def blog(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> dict[str, Any]:
        return await self._search("blog", {
            "query": query,
            "display": _clamp(display, 1, 100),
            "start": _clamp(start, 1, 1000),
            "sort": sort if sort in ("sim", "date") else "sim",
        })

    async def cafe(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> dict[str, Any]:
        return await self._search("cafearticle", {
            "query": query,
            "display": _clamp(display, 1, 100),
            "start": _clamp(start, 1, 1000),
            "sort": sort if sort in ("sim", "date") else "sim",
        })

    async def web(self, query: str, display: int = 10, start: int = 1) -> dict[str, Any]:
        return await self._search("webkr", {
            "query": query,
            "display": _clamp(display, 1, 100),
            "start": _clamp(start, 1, 1000),
        })

    async def local(self, query: str, display: int = 5, sort: str = "random") -> dict[str, Any]:
        # 지역 검색은 display 최대 5, start는 1만 허용됩니다.
        result = await self._search("local", {
            "query": query,
            "display": _clamp(display, 1, 5),
            "start": 1,
            "sort": sort if sort in ("random", "comment") else "random",
        })
        result["items"] = [_add_coordinates(item) for item in result["items"]]
        return result

    async def aclose(self) -> None:
        await self._http.aclose()
