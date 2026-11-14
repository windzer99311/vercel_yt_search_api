import json
import re
from bs4 import BeautifulSoup
from fastapi import FastAPI
from workers import WorkerEntrypoint
import asgi
import requests

app = FastAPI()


@app.get("/search")
def search_engine(query: str):
  searched_data = []
  search_url = f"https://www.youtube.com/results?search_query={query}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  response = requests.get(search_url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  script_tag = soup.find("script", string=re.compile(r"ytInitialData"))

  if script_tag:
    match = re.search(r"ytInitialData\s*=\s*({.*?});", script_tag.string)
    if match:
      json_text = match.group(1)
      data = json.loads(json_text)
      try:
        videos = (
            data["contents"]["twoColumnSearchResultsRenderer"][
                "primaryContents"
            ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
                "contents"
            ]
        )
        for video in videos:
          if "videoRenderer" in video:
            res = video["videoRenderer"]
            title = res["title"]["runs"][0]["text"]
            video_id = res["videoId"]
            thumbnail_url = res["thumbnail"]["thumbnails"][0]["url"]
            searched_data.append({
                "title": title,
                "thumbnail": thumbnail_url,
                "videoId": video_id,
            })
      except (KeyError, IndexError):
        pass

  return {"results": searched_data}


class Default(WorkerEntrypoint):

  async def fetch(self, request):
    return await asgi.fetch(app, request.js_object, self.env)
