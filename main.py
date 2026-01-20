import requests
import re
import json
from bs4 import BeautifulSoup
from fastapi import FastAPI
app = FastAPI()
@app.get("/search")
def search_engine(query):
    searched_data = []
    search_url = f"https://www.youtube.com/results?search_query={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # YouTube hides video data in a script tag starting with "var ytInitialData ="
    script_tag = soup.find("script", string=re.compile(r'ytInitialData'))

    if script_tag:
        # Clean the string to get pure JSON
        json_text = re.search(r'ytInitialData\s*=\s*({.*?});', script_tag.string).group(1)
        data = json.loads(json_text)

        # Dig into the JSON layers to find the video list
        # Note: The path below is specific to how YouTube structures its data
        videos = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        for video in videos:
            if 'videoRenderer' in video:
                res = video['videoRenderer']
                title = res['title']['runs'][0]['text']
                video_id = res['videoId']
                thumbnail_url = res['thumbnail']['thumbnails'][0]['url']
                searched_data.append({
                    "title": title,
                    "thumbnail": thumbnail_url,
                    "videoId": video_id
                })
        return {"results": searched_data}
if __name__ == "__main__":
    uvicorn.run(app)
