import signal
from typing import List
from tqdm import tqdm
import undetected_chromedriver as uc
import sys
import os
import subprocess
import json
import logging
import requests
import time

# logger
logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s [%(filename)s:%(lineno)d]')
logger = logging.getLogger(__name__)

# global variables
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

# functions
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

def filter_not_available(ids: List[str]) -> List[str]:
    for id in tqdm(ids, desc = "過濾無效影片"):
        resp = requests.get(f'https://i.ytimg.com/vi/{id}/hqdefault.jpg', headers={
            "User-Agent": user_agent,
        })
        if resp and resp.status_code == 200:
            yield id

def detect_chrome_install_path():
    if sys.platform == 'win32':
        for i in range(2):
            path = 'C:\\Program Files' + (' (x86)' if i else '') +'\\Google\\Chrome\\Application'
            if os.path.isdir(path):
                for f in os.scandir(path):
                    if f.is_file() and f.name == 'chrome.exe':
                        return f.path
    elif sys.platform == 'linux' or sys.platform == 'linux2':
        path = '/usr/bin/google-chrome'
        if os.path.isfile(path):
            return path
    elif sys.platform == 'darwin':
        path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        if os.path.isfile(path):
            return path
    return None

def main():
    # 解析 Mixerbox 播放清單，並過濾無效影片
    playlist = input("請輸入Mixerbox播放清單網址: ")
    result = load_mixerbox_playlist(playlist)
    data = []
    for i in filter_not_available(result):
        data.append(i)
        time.sleep(0.1)
    logger.info(f"共 {len(data)} 筆可用影片")
    
    # 手動登入 Google 帳號
    chrome_path = detect_chrome_install_path()
    user_data_dir = os.path.join(os.getcwd(), 'userdata')
    if not chrome_path:
        logger.error('找不到 Chrome 安裝路徑，離開程式')
        os.exit(1)
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    logger.info(f"Chrome 安裝路徑: {chrome_path}, 使用者資料夾: {user_data_dir}")
    proc = subprocess.Popen(f'"{chrome_path}" --user-data-dir="{user_data_dir}"')

    logger.info("請手動登入 Google 帳號，並輸入 `yes` 繼續")
    while True:
        if input().strip().lower() == 'yes':
            break
    if proc.poll() is None:
        proc.kill()
    
    # 批量新增至 Youtube 播放清單
    driver = uc.Chrome(user_data_dir=user_data_dir)
    driver.get('https://www.youtube.com/')
    logger.info("載入 Javascript 腳本")
    with open('yt.js', 'r', encoding='utf-8') as f:
        js = f.read()
        js += f'\nawait main({json.dumps(data, ensure_ascii=False)})\narguments[arguments.length - 1](true);'
    logger.debug(f"腳本內容: {js}")
    logger.info("開始執行腳本")
    logger.info("請勿關閉視窗，直到腳本執行完畢")
    success = driver.execute_async_script(js)
    logger.info(f"腳本執行完畢，執行結果 {success}，請按下任意鍵離開")
    os.system('pause')

if __name__ == '__main__':
    main()
