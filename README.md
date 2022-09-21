# mixerbox_converter

用以轉換 Mixerbox 播放清單之歌曲至 Youtube 播放清單(TL開頭，意味著您需手動加入至自己的播放清單)。

不串接 Youtube Data v3 api 之原因為，每個人每天的免費 API Quota(額度) 為 **10,000**，一次調用的成本為 **50**，這意味著在使用 API 的情況下您一天只能保存 **200** 首影片，太雞肋了，故不採用。

建議使用 [Multiselect for youtube](https://chrome.google.com/webstore/detail/multiselect-for-youtube/gpgbiinpmelaihndlegbgfkmnpofgfei) 擴充套件，用於加快保存至播放清單的時間。

## Requirement

- Python 3.5 up
- tqdm
- requests

## Usage

1. 安裝依賴套件

   `pip install -r requirements.txt`

2. 使用終端機打入下列指令:

   `python main.py` or `python3 main.py`

3. 依步驟執行即可自動轉換成 Youtube playlist!
