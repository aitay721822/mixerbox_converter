from typing import Callable, List, Optional, Generator
from tqdm import tqdm
import undetected_chromedriver as uc
import sys
import os
import subprocess
import json
import logging
import requests
import time
import argparse

# arguments
parser = argparse.ArgumentParser(description='Mixerbox playlist to Youtube playlist')
parser.add_argument('--chrome-path', type=str, default=None, help='Chrome executable file path')
parser.add_argument('--debug', action='store_true', help='enable debug mode')
parser.add_argument('--save-script', action='store_true', help='save script to file')

# global variables
app_name = 'mb2yt'
app_task_name = 'data.json'
app_script_name = 'script.js'
log_level = logging.INFO
log_filename = f'{app_name}.log'
log_format = '[%(asctime)s][%(name)s][%(levelname)s] %(message)s [%(filename)s:%(lineno)d]'
client_userdata_path = os.path.join(os.getcwd(), 'userdata')
client_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

# logger
logger = logging.getLogger(app_name)

# functions
def load_mixerbox_playlist(url: str) -> List[str]:
    def parse(url: str) -> str:
        return url.strip('/').split('/')[-1]

    resp = requests.get(f"https://www.mbplayer.com/api/playlist?reverse=true&type=playlist&vectorId={parse(url)}", headers = {
        "User-Agent": client_user_agent,
        "Referer": url
    })
    if resp and resp.status_code == 200:
        data = resp.json()
        items = data['items']
        return [i['f'] for i in items if 't' in i and i['t'].lower() == 'yt']
    return []

def filter_not_available(ids: List[str]) -> Generator[str]:
    for id in tqdm(ids, desc = "過濾無效影片"):
        resp = requests.get(f'https://i.ytimg.com/vi/{id}/hqdefault.jpg', headers={
            "User-Agent": client_user_agent,
        })
        if resp and resp.status_code == 200:
            yield id
        else:
            logger.warning(f"影片 {id} 無法取得預覽圖，可能已被下架")

def detect_chrome_install_path(chrome_path: str = None) -> Optional[str]:
    if chrome_path and os.path.isfile(chrome_path):
        return chrome_path

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

def load_task() -> List[str]:
    try:
        if not os.path.isfile(app_task_name):
            return []
        with open(app_task_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"讀取上次未完成的任務時發生錯誤，重新開始，錯誤訊息: {e}")
        return []

def save_task(data: List[str]) -> None:
    try:
        with open(app_task_name, 'w', encoding='utf-8') as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.warning(f"儲存未完成的任務時發生錯誤，錯誤訊息: {e}")

check_yes_or_no = lambda resp: resp.strip().lower() in ['yes', 'no']
check_yes_only = lambda resp: resp.strip().lower() == 'yes'
def get_validate_response(msg: str, validate_fn: Callable[[str], bool]) -> str:
    while True:
        result = input(msg).strip().lower()
        if validate_fn(result):
            return result

def configure_logger(debug: bool):
    logging.basicConfig(level=log_level if not debug else logging.DEBUG, 
                       format=log_format,
                       handlers=[
                            logging.FileHandler(log_filename, encoding='utf-8'),
                            logging.StreamHandler()
                       ])

def main():
    args = parser.parse_args()
    
    # 設定 logger
    configure_logger(args.debug)
    
    # 檢測是否有上次未完成的任務
    continue_last_task = False
    data = load_task()
    if data:
        continue_last_task = get_validate_response("發現上次的任務，是否繼續? (yes/no): ", check_yes_or_no) == 'yes'

    if not continue_last_task:
        # 刪除上次未完成的任務
        if os.path.isfile(app_task_name):
            os.remove(app_task_name)
            
        # 解析 Mixerbox 播放清單，並過濾無效影片
        playlist = input("請輸入Mixerbox播放清單網址: ")
        result = load_mixerbox_playlist(playlist)
        data = []
        for i in filter_not_available(result):
            data.append(i)
            time.sleep(0.1)
        save_task(data)
        logger.info(f"共 {len(data)} 筆可用影片")

    # 手動登入 Google 帳號
    chrome_path = detect_chrome_install_path(args.chrome_path)
    user_data_dir = client_userdata_path
    if not chrome_path:
        logger.error('找不到 Chrome 安裝路徑，離開程式')
        os.exit(1)
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    logger.info(f"Chrome 安裝路徑: {chrome_path}, 使用者資料夾: {user_data_dir}")
    proc = subprocess.Popen(f'"{chrome_path}" --user-data-dir="{user_data_dir}" "https://accounts.google.com/ServiceLogin?hl=zh-TW"')

    logger.info("請手動登入 Google 帳號，並輸入 `yes` 繼續")
    get_validate_response('請輸入 `yes` 繼續: ', check_yes_only)
    if proc.poll() is None:
        proc.kill()
    
    # 批量新增至 Youtube 播放清單
    driver = uc.Chrome(user_data_dir=user_data_dir)
    driver.get('https://www.youtube.com/')
    
    logger.info("請到 Youtube 首頁時，輸入 `yes` 繼續")
    get_validate_response('請輸入 `yes` 繼續: ', check_yes_only)
    
    logger.info("載入 Javascript 腳本")
    with open('yt.js', 'r', encoding='utf-8') as f:
        js = f.read()
        js += f'\nawait main({json.dumps(data, ensure_ascii=False)})\narguments[arguments.length - 1](true);'
    if args.save_script:
        with open(app_script_name, 'w', encoding='utf-8') as f:
            f.write(js)
    logger.debug(f"腳本內容: {js}")
    logger.info("開始執行腳本")
    logger.info("請勿關閉視窗，直到腳本執行完畢")
    success = driver.execute_async_script(js)
    logger.info(f"腳本執行完畢，執行結果 {success}，請輸入任意鍵離開")
    input("請輸入任意鍵離開...")

if __name__ == '__main__':
    main()
