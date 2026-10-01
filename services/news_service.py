"""新聞抓取服務。

負責：
    1. 用 feedparser 平行（ThreadPoolExecutor）抓取多個 RSS/Atom 來源。
    2. 將抓取結果做簡單的正規化（統一欄位：title, summary, link, published, source）。
    3. 對每個來源做短暫的記憶體快取（預設 5 分鐘），避免同時大量請求打爆來源站台。
    4. 單一來源抓取失敗（timeout / parse error）時，回傳該來源的錯誤狀態，
       不影響其他來源，也不會讓整頁掛掉。

注意：這裡刻意不使用資料庫或寫檔案，快取只存在於 process 記憶體中，
重啟服務快取就會清空，符合「不需要存檔/資料庫持久化」的需求。
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from threading import Lock

import feedparser

from services.translation import translate
from sources import NEWS_SOURCES, SOURCES_BY_ID

logger = logging.getLogger(__name__)

# 快取存活時間（秒）。5~10 分鐘皆合理，這裡取 5 分鐘。
CACHE_TTL_SECONDS = 5 * 60

# 每個來源最多顯示幾則新聞
MAX_ITEMS_PER_SOURCE = 15

# 抓取單一 feed 的逾時秒數
FETCH_TIMEOUT_SECONDS = 8

# 摘要最多顯示字數（過長會截斷並加上 ...）
SUMMARY_MAX_LENGTH = 200

_HTML_TAG_RE = re.compile(r"<[^>]+>")

# AI 相關關鍵字（英文用 \b 詞界避免誤判，例如 "AI" 不會誤中 "AIR"、"MAIN"）。
# 中文關鍵字不需要詞界，直接子字串比對即可。
_AI_KEYWORDS_EN = [
    "ai", "a.i.", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "generative ai",
    "genai", "chatgpt", "openai", "anthropic", "claude", "gemini", "copilot",
    "midjourney", "stable diffusion", "sora", "nvidia ai", "agentic",
]
_AI_KEYWORDS_ZH = [
    "人工智慧", "人工智能", "機器學習", "深度學習", "神經網路", "神经网络",
    "大型語言模型", "大语言模型", "生成式ai", "生成式人工智慧", "生成式人工智能",
    "自然語言處理", "自然语言处理", "聊天機器人", "聊天机器人",
]
_AI_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _AI_KEYWORDS_EN) + r")\b",
    re.IGNORECASE,
)

# {source_id: {"items": [...], "fetched_at": float, "error": str | None}}
_cache: dict = {}
_cache_lock = Lock()


def _is_ai_related(title: str, summary: str) -> bool:
    """依標題與摘要的關鍵字，粗略判斷這則新聞是否與 AI 相關。

    這是簡單的關鍵字比對，不是語意分類，目的是提供「AI 新聞 / 非AI新聞」
    篩選功能的合理近似值，未來若需要更準確的分類，可以在這裡改接
    語意分類模型或 LLM API。
    """
    text = f"{title} {summary}"
    if _AI_KEYWORD_RE.search(text):
        return True
    lowered = text.lower()
    return any(keyword in lowered for keyword in _AI_KEYWORDS_ZH)


def _strip_html(raw_html: str) -> str:
    """移除 HTML 標籤並解碼 HTML entity，回傳純文字摘要。"""
    if not raw_html:
        return ""
    text = _HTML_TAG_RE.sub("", raw_html)
    text = unescape(text)
    return " ".join(text.split())


def _truncate(text: str, max_length: int = SUMMARY_MAX_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def _fetch_single_source(source: dict) -> dict:
    """抓取單一來源的 RSS/Atom feed，回傳正規化後的結果。"""
    source_id = source["id"]
    try:
        parsed = feedparser.parse(source["url"], request_headers={"User-Agent": "Mozilla/5.0"})

        # feedparser 對於網路層錯誤會設定 bozo_exception，但部分 feed 仍可正常解析
        # （例如某些非嚴格 XML），因此只在完全沒有 entries 時才視為失敗。
        if getattr(parsed, "bozo", False) and not parsed.entries:
            raise parsed.bozo_exception or ValueError("RSS 解析失敗")

        items = []
        for entry in parsed.entries[:MAX_ITEMS_PER_SOURCE]:
            title = _strip_html(entry.get("title", "(無標題)"))
            summary_raw = entry.get("summary", "") or entry.get("description", "")
            summary = _truncate(_strip_html(summary_raw))
            published = entry.get("published", "") or entry.get("updated", "")
            link = entry.get("link", "")

            items.append(
                {
                    "title": translate(title),
                    "summary": translate(summary),
                    "link": link,
                    "published": published,
                    "source_id": source_id,
                    "source_name": source["name"],
                    "is_ai": _is_ai_related(title, summary),
                }
            )

        return {"items": items, "error": None}
    except Exception as exc:  # noqa: BLE001 - 任何抓取/解析錯誤都要被攔截，不能讓整頁掛掉
        logger.warning("抓取新聞來源 %s 失敗: %s", source_id, exc)
        return {"items": [], "error": str(exc)}


def _get_cached_or_fetch(source: dict, force: bool = False) -> dict:
    """取得該來源的快取結果，若快取過期（或 force=True）則重新抓取。"""
    source_id = source["id"]
    now = time.time()

    if not force:
        with _cache_lock:
            cached = _cache.get(source_id)
            if cached and now - cached["fetched_at"] < CACHE_TTL_SECONDS:
                return cached

    result = _fetch_single_source(source)
    result["fetched_at"] = now

    with _cache_lock:
        _cache[source_id] = result

    return result


def fetch_news(source_ids: list[str] | None = None, force: bool = False) -> dict:
    """平行抓取指定來源（預設全部）的新聞，回傳彙整結果。

    `force=True` 時會無視記憶體快取，強制重新抓取每個來源的最新資料
    （對應前端的「立即重新整理」按鈕）。

    回傳格式：
        {
            "items": [...按發布時間排序後的新聞列表...],
            "sources": {
                "<source_id>": {"name": ..., "status": "ok" | "error",
                                 "error": str | None, "count": int},
                ...
            },
        }
    """
    if source_ids:
        selected_sources = [s for s in NEWS_SOURCES if s["id"] in set(source_ids)]
    else:
        selected_sources = NEWS_SOURCES

    all_items = []
    source_status = {}

    with ThreadPoolExecutor(max_workers=max(len(selected_sources), 1)) as executor:
        future_to_source = {
            executor.submit(_get_cached_or_fetch, source, force): source
            for source in selected_sources
        }
        for future in as_completed(future_to_source, timeout=FETCH_TIMEOUT_SECONDS + 5):
            source = future_to_source[future]
            try:
                result = future.result(timeout=FETCH_TIMEOUT_SECONDS)
            except Exception as exc:  # noqa: BLE001
                logger.warning("等待來源 %s 結果逾時或失敗: %s", source["id"], exc)
                result = {"items": [], "error": str(exc)}

            all_items.extend(result["items"])
            source_status[source["id"]] = {
                "name": source["name"],
                "status": "error" if result.get("error") else "ok",
                "error": result.get("error"),
                "count": len(result["items"]),
            }

    all_items.sort(key=lambda item: item.get("published", ""), reverse=True)

    return {"items": all_items, "sources": source_status}


def get_all_sources() -> list[dict]:
    """回傳所有可用的新聞來源設定（供前端顯示 checkbox 清單）。"""
    return NEWS_SOURCES


def is_valid_source_id(source_id: str) -> bool:
    return source_id in SOURCES_BY_ID
