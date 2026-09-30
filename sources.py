"""新聞來源設定檔。

集中定義所有 RSS/Atom 新聞來源，方便日後新增或移除來源。
每個來源是一個字典，包含：
    id: 唯一識別碼（英數字，會用在 checkbox 的 value 與快取 key 上）
    name: 顯示名稱
    url: RSS/Atom feed 網址
    region: "intl"（國外）或 "tw"（國內繁體中文）
    language: 內容語言代碼（例如 "en" / "zh-Hant"），供未來翻譯層判斷是否需要翻譯
"""

NEWS_SOURCES = [
    {
        "id": "techcrunch",
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "region": "intl",
        "language": "en",
    },
    {
        "id": "theverge",
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "region": "intl",
        "language": "en",
    },
    {
        "id": "arstechnica",
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "region": "intl",
        "language": "en",
    },
    {
        "id": "hackernews",
        "name": "Hacker News (Front Page)",
        "url": "https://hnrss.org/frontpage",
        "region": "intl",
        "language": "en",
    },
    {
        "id": "ithome",
        "name": "iThome",
        "url": "https://www.ithome.com.tw/rss",
        "region": "tw",
        "language": "zh-Hant",
    },
    {
        "id": "technews",
        "name": "TechNews 科技新報",
        "url": "https://technews.tw/feed/",
        "region": "tw",
        "language": "zh-Hant",
    },
    {
        "id": "inside",
        "name": "INSIDE 硬塞的網路趨勢觀察",
        # 官方 /feed 已失效（404），改用 /feed/rss，內容相同。
        "url": "https://www.inside.com.tw/feed/rss",
        "region": "tw",
        "language": "zh-Hant",
    },
]

# 方便用 id 快速查詢來源設定
SOURCES_BY_ID = {source["id"]: source for source in NEWS_SOURCES}
