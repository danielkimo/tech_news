# 每日科技新聞聚合網站

即時彙整國內外主要科技新聞網站的最新新聞。**不使用資料庫或寫檔案持久化**，
每次使用者瀏覽網頁時即時透過 RSS/Atom feed 抓取，並在伺服器記憶體中做短暫快取
（預設 5 分鐘），避免同時大量請求打爆來源站台。

## 專案結構

```
.
├── app.py                     # Flask 應用程式進入點（路由 / API）
├── sources.py                 # 新聞來源設定（集中定義，方便新增/移除來源）
├── services/
│   ├── news_service.py        # RSS 抓取、正規化、平行處理、記憶體快取
│   └── translation.py         # 翻譯層（目前 no-op，未來可接 Azure OpenAI）
├── templates/
│   └── index.html             # 首頁模板（來源勾選 UI + 新聞卡片容器）
├── static/
│   ├── style.css              # 版面樣式
│   └── app.js                 # 前端邏輯：呼叫 /api/news、渲染卡片、篩選來源
├── requirements.txt
└── README.md
```

## 本機執行

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 方式一
python app.py

# 方式二
export FLASK_APP=app.py
flask run
```

預設監聽 port 5000，若該 port 被佔用（例如 macOS 的 AirPlay Receiver），
可用環境變數指定其他 port：

```bash
PORT=5891 python app.py
```

啟動後開啟瀏覽器造訪 `http://localhost:5000/`（或你指定的 port）。

### 快速驗證 API

```bash
curl http://localhost:5000/api/sources          # 取得所有來源清單
curl http://localhost:5000/api/news             # 抓取全部來源新聞
curl "http://localhost:5000/api/news?sources=techcrunch,ithome"  # 只抓指定來源
```

## 新聞來源

目前內建來源定義於 `sources.py`，皆使用公開 RSS/Atom feed：

| 來源 | 地區 | Feed URL |
| --- | --- | --- |
| TechCrunch | 國外 | https://techcrunch.com/feed/ |
| The Verge | 國外 | https://www.theverge.com/rss/index.xml |
| Ars Technica | 國外 | https://feeds.arstechnica.com/arstechnica/index |
| Hacker News (Front Page) | 國外 | https://hnrss.org/frontpage |
| iThome | 國內 | https://www.ithome.com.tw/rss |
| TechNews 科技新報 | 國內 | https://technews.tw/feed/ |
| INSIDE 硬塞的網路趨勢觀察 | 國內 | https://www.inside.com.tw/feed/rss |
| Yahoo奇摩新聞 - 科技 | 國內 | https://tw.news.yahoo.com/rss/technology |
| 中央社 CNA - 科技 | 國內 | https://feeds.feedburner.com/rsscna/technology |
| 數位時代 Meet創業小聚 | 國內 | https://meet.bnext.com.tw/rss |
| Cool3c | 國內 | https://www.cool3c.com/rss |
| Mashdigi | 國內 | https://mashdigi.com/feed |

> 註：INSIDE 官方文件常提到的 `/feed` 路徑目前會回傳 404，
> 實際可用的 RSS 路徑是 `/feed/rss`，已在 `sources.py` 中更新。

### 如何新增新聞來源

編輯 `sources.py`，在 `NEWS_SOURCES` 清單中新增一個字典即可，例如：

```python
{
    "id": "engadget",
    "name": "Engadget",
    "url": "https://www.engadget.com/rss.xml",
    "region": "intl",       # "intl"（國外）或 "tw"（國內）
    "language": "en",       # 語言代碼，供未來翻譯層判斷
},
```

新增後前端 checkbox 清單與後端 API 會自動包含新來源，不需要改動其他程式碼。

## 翻譯功能（未來擴充）

英文新聞目前**先不翻譯**，直接顯示原文。程式架構已預留翻譯層：
`services/translation.py` 中定義了 `TranslationService` 介面與
`NoOpTranslationService`（目前使用的預設實作，直接回傳原文）。

未來要接 Azure OpenAI 翻譯時：

1. 在 `services/translation.py` 新增一個 `AzureOpenAITranslationService`，
   在其 `translate(text, target_lang)` 方法中呼叫 Azure OpenAI API
   （例如 chat completion，將英文標題/摘要翻成繁體中文）。
2. 修改 `get_translation_service()`，依環境變數（例如 `TRANSLATION_PROVIDER`）
   切換要使用哪個實作。
3. `services/news_service.py` 已經在抓取每則新聞的 `title` / `summary`
   時呼叫 `translate(...)`，不需要再改動呼叫端程式碼。

建議加上快取（例如以文章連結為 key）避免重複呼叫翻譯 API，並考慮加上
逾時與錯誤處理（翻譯失敗時 fallback 回原文）。

## 技術重點

- **Flask**：輕量 web 框架，路由分為頁面（`/`）與 JSON API（`/api/news`、`/api/sources`）。
- **feedparser**：解析各家 RSS/Atom feed。
- **ThreadPoolExecutor**：平行抓取多個來源，加快即時載入速度；單一來源逾時
  或解析失敗會被個別攔截，不影響其他來源或讓整頁掛掉。
- **記憶體快取**：以 `source_id` 為 key，快取 TTL 預設 5 分鐘（`CACHE_TTL_SECONDS`），
  純粹存在於 process 記憶體中，重啟服務即清空，符合「不落地儲存」的需求。
- **前端**：Vanilla JS，勾選來源後以 query param（`?sources=a,b,c`）重新呼叫
  `/api/news`，由後端依快取狀態回傳資料；錯誤來源會在狀態列顯示「抓取失敗」提示。

## iOS App：科技脈動 TechPulse

專案也提供一個原生 iOS App「科技脈動 TechPulse」，用 SwiftUI + WKWebView
包裝本網站，並附上自訂 App Icon。詳見 [`ios/README.md`](ios/README.md)，
內含如何用 Xcode 開啟執行、如何切換模擬器/實機的連線位址、以及如何重新
產生 Xcode 專案與 Icon 圖檔。

```bash
open ios/TechPulse.xcodeproj
```

## 已知限制 / 後續可優化方向

- 目前摘要僅做簡單的 HTML 標籤移除與長度截斷，未做進一步排版清理。
- 翻譯層目前為 no-op，串接真正翻譯 API 時建議加上快取與逾時處理。
- 若來源網站有更嚴格的防爬蟲機制，未來可視情況調整 `User-Agent` 或改用官方 API。
