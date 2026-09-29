"""Claude Desktop / Claude Code에서 쓰는 네이버 검색 MCP 서버 (stdio)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from naver_mcp.client import NaverAPIError, NaverSearchClient

mcp = MCPServer(
    "naver-search",
    instructions=(
        "네이버 검색 API 도구입니다. 한국어 블로그 후기, 맛집/장소, 웹문서, 카페 글을 찾을 때 사용하세요. "
        "결과의 link를 출처로 함께 알려주세요."
    ),
)
client = NaverSearchClient()

Query = Annotated[str, Field(description="검색어 (UTF-8)")]
Display = Annotated[int, Field(ge=1, le=100, description="한 번에 가져올 결과 수 (1~100)")]
Start = Annotated[int, Field(ge=1, le=1000, description="검색 시작 위치 (1~1000), 페이지 넘김용")]
Sort = Annotated[Literal["sim", "date"], Field(description="sim: 정확도순, date: 최신순")]


async def _run(coro) -> dict[str, Any]:
    try:
        return await coro
    except NaverAPIError as e:
        raise ToolError(str(e)) from e


@mcp.tool()
async def search_blog(query: Query, display: Display = 10, start: Start = 1, sort: Sort = "sim") -> dict[str, Any]:
    """네이버 블로그 글을 검색합니다. 후기, 리뷰, 경험담을 찾을 때 유용합니다."""
    return await _run(client.blog(query, display, start, sort))


@mcp.tool()
async def search_cafe(query: Query, display: Display = 10, start: Start = 1, sort: Sort = "sim") -> dict[str, Any]:
    """네이버 카페 글을 검색합니다. 커뮤니티 질문/답변, 정보 공유 글을 찾을 때 유용합니다."""
    return await _run(client.cafe(query, display, start, sort))


@mcp.tool()
async def search_web(query: Query, display: Display = 10, start: Start = 1) -> dict[str, Any]:
    """네이버 웹문서를 검색합니다. 일반 웹페이지, 공식 사이트 등을 찾을 때 사용합니다."""
    return await _run(client.web(query, display, start))


@mcp.tool()
async def search_local(
    query: Query,
    display: Annotated[int, Field(ge=1, le=5, description="결과 수 (1~5, 네이버 제한)")] = 5,
    sort: Annotated[
        Literal["random", "comment"], Field(description="random: 정확도순, comment: 리뷰 많은 순")
    ] = "random",
) -> dict[str, Any]:
    """네이버 지역(장소/업체) 검색. 맛집, 카페, 병원 등의 이름·주소·전화·카테고리·좌표를 돌려줍니다.
    '강남역 맛집'처럼 지역명을 함께 넣으면 정확도가 높아집니다."""
    return await _run(client.local(query, display, sort))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
