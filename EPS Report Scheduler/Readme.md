# 股票投資聊天機器人專案實作 I

## 前言
在前面幾堂課程中我們學習了如何使用 Git 來管理我們的程式碼版本並將我們的聊天機器人部屬到 Heroku 雲端伺服器上。在接下來的兩堂課程中我們將學習如何整合 LINE Messaging API 和定期抓取資料儲存來進行我們的股票聊天機器人專案的實作。

股票投資聊天機器人預計主要功能如下：

定期執行程式抓取指定個股財務資料並計算出個股預估價格更新到 CSV 試算表檔案上
讀取 CSV 試算表檔案，判斷目前股價是否到合適買點。若為合適買賣點則發送通知給使用者

## 定期執行程式
首先，我們來看如何在 Python 定期執行程式。定期在背景執行程式是許多網路服務常見的功能之一（通常我們稱為 `Scheduler`）。
在一般伺服器中我們可以使用 `cron` 這個工具去定期執行我們的工作程式（`job`），而在 Python 中有一個輕量的 APScheduler 套件可以讓我們使用 Python 程式撰寫我們固定要執行的程式。

### 安裝套件
首先，我們先使用 pip 在終端機安裝我們的套件：
```
$ pip install apscheduler
```
#### 在本機端執行程式
我們在我們的專案資料夾下建立一個 `clock.py` 檔案：
```
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler

# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
@sched.scheduled_job('interval', seconds=1)
def timed_job():
    print('每 1 秒鐘執行一次程式工作區塊')

# decorator 設定 Scheduler 為 cron 固定每週週間 6pm. 執行此程式工作區塊（但要注意的是 heroku server 上的時區為 UTC+0，所以台灣時間會是再加約 8 小時，變成隔天凌晨 2 點）
@sched.scheduled_job('cron', day_of_week='mon-fri', hour=18)
def scheduled_job():
    print('每週週間 6 PM UTC+0，2 AM UTC+8. 執行此程式工作區塊')

# 開始執行
sched.start()
```

>特別注意 Heroku server 上的時區為 UTC+0，所以台灣時間會是再加約 8 小時進行轉換

#### 設定 Heroku 如何執行程式
定義 Clock process type 的 `Procfile` 格式如下：
```
clock: python 檔案名稱
```
根據檔案名稱填寫為：
```
clock: python clock.py
```
然後在 `requirements.txt` 中加入安裝套件版本資訊：
```
APScheduler==3.0.0
```
設定 `runtime.txt`：
```
python-3.6.2
```
#### 部屬定期執行工作程式到 Heroku 上
在我們的 Heroku 上新增一個 App （舉例而言叫做 `python-clock-app`）然後新增網址到 git 的遠端倉庫：
```
$ heroku login
$ heroku git:remote -a 你的 heroku app 名稱
```
接著依照部屬到 Heroku 的步驟將專案資料夾下的檔案部屬上去：
```
$ git add .
$ git commit -a -m "init commit"
$ git push heroku master
```
最後設定該定期執行程式只會有一個，才不會重複執行：
```
heroku ps:scale clock=1 -a {請輸入你的 Heroku App 名稱}
```
若要結束終止定期執行程式：
```
heroku ps:scale clock=0 -a {請輸入你的 Heroku App 名稱}
```
若要觀看 Heroku 伺服器顯示除錯訊息：
```
# --tail 代表持續印出
$ heroku logs --tail
```

### 整合網路爬蟲和定期執行程式
我們也可以嘗試整合之前財報分析專案實作個股股價估價法資料（當然也可以替換成不同的資料和更新數據方式），定期進行爬取和更新：
```
import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler

# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

def crawl_for_stock_price():
    url = 'https://goodinfo.tw/StockInfo/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=2412&CHT_CAT=YEAR'

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }

    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    # 根據 HTTP header 的編碼解碼後的內容資料（ex. UTF-8）
    raw_html = resp.text

    # PE Ratio 簡寫 per
    soup = BeautifulSoup(raw_html, 'html.parser')
    per_rows = []
    eps_rows = []
    # 使用選擇器選取最近五年，CSS 選擇器 id #row 從第 0 開始到 5
    for row_line in range(0, 5):
        # 取出 td 標籤內的 EPS（在 index 4） text 取值
        eps_rows.append(soup.select(f'#row{row_line} td')[4].text)
        # 取出 td 標籤內的 PER 本益比（在 index 5） text 取值
        per_rows.append(soup.select(f'#row{row_line} td')[5].text)

    # 取出最高 EPS 和最低 EPS
    max_eps = max(eps_rows)
    min_eps = min(eps_rows)
    # 取出最高本益比和最低本益比
    max_per = max(per_rows)
    min_per = min(per_rows)

    print('max_eps', max_eps)
    print('min_eps', min_eps)


    print('max_per', max_per)
    print('min_per', min_per)

    """
    max_eps 5.16
    min_eps 4.3
    max_per 25.58
    min_per 19.67
    """

# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
@sched.scheduled_job('interval', minutes=5)
def timed_job():
    # 要注意不要太頻繁抓取
    print('每 5 分鐘執行一次程式工作區塊')
    crawl_for_stock_price()

# 開始執行
sched.start()
```

>注意定期執行的排程會依照您設定的時間週期執行，並不會馬上執行，若要開發測試，可以改成比較短的時間來測試


### 綜結
以上我們介紹了如何在 Python 執行定期執行程式和在 Heroku 上的部屬方式，讓我們可以免去將電腦持續開機等待程式執行（當然我們也可以在本機操作定期更新本地的資料庫或檔案）。我們也試著整合個股股價估價法資料，接下來我們會更進一步的整合相關資料進行後續的操作。

