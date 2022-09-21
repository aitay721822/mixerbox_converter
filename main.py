from typing import List, Optional
from tqdm import tqdm
import requests

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

def load_mixerbox_playlist(url: str) -> List[str]:
    def parse(url: str) -> str:
        return url.strip('/').split('/')[-1]

    resp = requests.get(f"https://www.mbplayer.com/api/playlist?reverse=true&type=playlist&vectorId={parse(url)}", headers = {
        "User-Agent": user_agent,
        "Referer": url
    })
    if resp and resp.status_code == 200:
        data = resp.json()
        items = data['items']
        return [i['f'] for i in items if 't' in i and i['t'].lower() == 'yt']
    return []

def parse_to_youtube_links(video_ids: List[str], per_page: int = 50) -> List[str]:
    long_link = [f"https://www.youtube.com/watch_videos?video_ids={','.join(video_ids[i * per_page:(i + 1) * per_page])}" for i in range(len(video_ids) // per_page + 1)]

    playlist_link = []
    for i in tqdm(long_link):
        resp = requests.get(i, headers = {
            "User-Agent": user_agent
        })
        if resp and resp.status_code == 200:
            playlist_link.append(resp.url)
    return playlist_link


def main():
    playlist = input("請輸入Mixerbox播放清單網址: ")
    result = load_mixerbox_playlist(playlist)
    if len(result) > 0:
        links = parse_to_youtube_links(result)
        print("請用以下這些連結逐一加入 Youtube 播放清單哦: ")
        print("推薦使用 Multiselect for youtube 這個擴充套件: https://chrome.google.com/webstore/detail/multiselect-for-youtube/gpgbiinpmelaihndlegbgfkmnpofgfei")
        print("可以一次選取多個影片加入播放清單")
        print()
        print(f"總共有 {len(links)} 筆資料: ")
        print('\r\n'.join([f"{i + 1}. {links[i]}" for i in range(len(links))]))


if __name__ == '__main__':
    main()
