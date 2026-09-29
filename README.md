# naver-mcp

네이버 검색 API를 Claude(Claude Desktop / Claude Code)에서 도구로 쓸 수 있게 해주는 MCP 서버입니다.

| 도구 | 네이버 API | 용도 |
|---|---|---|
| `search_blog` | 블로그 | 후기·리뷰·경험담 |
| `search_local` | 지역 | 맛집·장소·업체 (이름, 주소, 전화, 카테고리, 위경도) |
| `search_web` | 웹문서 | 일반 웹페이지 |
| `search_cafe` | 카페 | 카페 커뮤니티 글 |

결과의 `<b>` 강조 태그와 `&quot;` 같은 HTML 엔티티는 자동으로 제거됩니다.

## 1. 준비

- Python 3.10 이상
- [네이버 개발자센터](https://developers.naver.com/apps) → 내 애플리케이션 → **사용 API**에 `검색`이 추가되어 있어야 합니다.
- **인증 정보**에서 Client ID / Client Secret을 확인합니다.

## 2. 설치

```bash
git clone https://github.com/wd23-maker/EUNSONG.git
cd EUNSONG
python3 -m venv .venv
.venv/bin/pip install -e .
```

Windows에서는 `.venv\Scripts\pip install -e .` 을 사용하세요.

설치하면 `.venv/bin/naver-mcp` 실행 파일이 생깁니다. 아래 설정에서 이 파일의 **절대 경로**를 사용합니다.

## 3. Claude에 연결

### Claude Code

```bash
claude mcp add naver \
  -e NAVER_CLIENT_ID=발급받은_ID \
  -e NAVER_CLIENT_SECRET=발급받은_SECRET \
  -- /절대경로/EUNSONG/.venv/bin/naver-mcp
```

`claude mcp list` 로 연결 상태를 확인할 수 있습니다.

### Claude Desktop

설정 → 개발자 → 구성 편집으로 `claude_desktop_config.json` 을 열고 아래를 추가한 뒤 Claude Desktop을 재시작합니다.

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "naver": {
      "command": "/절대경로/EUNSONG/.venv/bin/naver-mcp",
      "env": {
        "NAVER_CLIENT_ID": "발급받은_ID",
        "NAVER_CLIENT_SECRET": "발급받은_SECRET"
      }
    }
  }
}
```

Windows 경로 예: `"C:\\Users\\me\\EUNSONG\\.venv\\Scripts\\naver-mcp.exe"`

## 4. 사용 예

Claude에게 이렇게 요청하면 됩니다.

- "네이버 블로그에서 제주도 3박4일 여행 후기 최신순으로 찾아줘"
- "강남역 근처 리뷰 많은 카페 알려줘"
- "네이버 카페에서 아이폰 배터리 교체 관련 글 찾아서 요약해줘"

## 호출 한도

검색 API는 애플리케이션당 **하루 25,000회**입니다. 개발자센터 → API 관리에서 사용량을 확인할 수 있습니다.

| 도구 | display (결과 수) | start (시작 위치) | sort |
|---|---|---|---|
| 블로그 / 카페 | 1~100 | 1~1000 | `sim` 정확도, `date` 최신 |
| 웹문서 | 1~100 | 1~1000 | - |
| 지역 | 1~5 | 1 고정 | `random` 정확도, `comment` 리뷰 많은 순 |

## 개발

```bash
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest
```

## 문제 해결

- `NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다` → 위 설정의 `env` 값을 확인하세요.
- `네이버 API 오류 (024): Authentication failed` → Client ID/Secret 오타를 확인하세요.
- `네이버 API 오류 (010)` 또는 403 → 사용 API에 `검색`이 추가되어 있는지, 호출 한도를 넘지 않았는지 확인하세요.
