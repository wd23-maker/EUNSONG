# CLAUDE.md

## 네이버 검색 규칙

- 네이버 검색은 NAVER API HUB(`https://naverapihub.apigw.ntruss.com`)로 호출한다.
  - 예: 뉴스 `/search/v1/news`, 블로그 `/search/v1/blog`
- 요청 헤더:
  - `X-NCP-APIGW-API-KEY-ID`: `$NAVER_CLIENT_ID`
  - `X-NCP-APIGW-API-KEY`: `$NAVER_CLIENT_SECRET`
- 블로그·카페 검색은 사용자가 따로 말하지 않으면 항상 `sort=date`(최신순)로 호출한다.
  - 사용자가 "정확도순"이라고 하면 `sort=sim`을 쓴다.
