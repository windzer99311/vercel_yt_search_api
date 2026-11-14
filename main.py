import json
from urllib.parse import quote_plus

from fastapi import FastAPI
from pyodide.http import pyfetch
from workers import WorkerEntrypoint
import asgi

app = FastAPI()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_initial_data(html: str):
    """Pull the ytInitialData JSON object out of the page without bs4/regex."""
    marker = "ytInitialData"
    pos = html.find(marker)
    while pos != -1:
        brace = html.find("{", pos)
        eq = html.find("=", pos)
        if eq != -1 and brace != -1 and eq < brace and brace - eq < 5:
            try:
                data, _ = json.JSONDecoder().raw_decode(html, brace)
                return data
            except json.JSONDecodeError:
                pass
        pos = html.find(marker, pos + 1)
    return None


@app.get("/search")
async def search_engine(query: str):
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    response = await pyfetch(url, headers=HEADERS)
    html = await response.string()

    data = extract_initial_data(html)
    results = []
    if not data:
        return {"results": results}

    try:
        sections = data["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"
        ]["sectionListRenderer"]["contents"]
        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                res = item.get("videoRenderer")
                if not res:
                    continue
                results.append({
                    "title": res["title"]["runs"][0]["text"],
                    "thumbnail": res["thumbnail"]["thumbnails"][0]["url"],
                    "videoId": res["videoId"],
                })
    except (KeyError, IndexError, TypeError):
        pass

    return {"results": results}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
