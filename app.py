"""每日科技新聞聚合網站 - Flask 應用程式進入點。"""

import os

from flask import Flask, jsonify, render_template, request

from services.news_service import fetch_news, get_all_sources

app = Flask(__name__)


@app.route("/")
def index():
    """首頁：顯示所有來源的 checkbox 清單，新聞內容由前端 JS 呼叫 /api/news 載入。"""
    return render_template("index.html", sources=get_all_sources())


@app.route("/api/news")
def api_news():
    """回傳新聞資料的 JSON API。

    可用 query param `sources` 指定要抓取的來源，以逗號分隔，例如：
        /api/news?sources=techcrunch,ithome
    不帶 `sources` 參數時，預設抓取全部來源。

    可用 query param `force=1` 無視伺服器端快取，強制重新抓取最新資料，
    例如：/api/news?force=1
    """
    sources_param = request.args.get("sources", "")
    source_ids = [s.strip() for s in sources_param.split(",") if s.strip()] or None
    force = request.args.get("force", "").lower() in ("1", "true", "yes")

    result = fetch_news(source_ids, force=force)
    return jsonify(result)


@app.route("/api/sources")
def api_sources():
    """回傳所有可用新聞來源的清單（id / name / region）。"""
    return jsonify(get_all_sources())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
