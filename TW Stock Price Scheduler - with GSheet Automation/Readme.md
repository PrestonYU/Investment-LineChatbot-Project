# 股票投資聊天機器人專案實作 II

## 前言
在上一堂課程中我們學習了如何使用 Scheduler 定時執行我們的程式。在這個股票投資聊天機器人中，我們預計的主要功能如下：

定期執行程式抓取指定個股財務資料並計算出個股便宜價、合理價（便宜價 + 昂貴價 / 2）和昂貴價更新到 Google Spread Sheet 試算表上
讀取 Google Spread Sheet 試算表資料，判斷目前股價是否到合適買點。若為合適買賣點則發送通知給使用者
所以接下來我們要學習如何串接 Google Sheets API 將我們定時執行的程式把抓下來的程式寫入 Google Sheets 上。

Google Sheets 試算表 API


圖片來源

Google Sheets 是 Google 雲端服務的其中一個重要產品，它可以讓你透過瀏覽器介面操作試算表並分享給其他使用者，雖然功能不一定比 Excel 完整，但有更彈性的使用方式。只要我們有 Google 帳號就能免費在一定的限制下使用。

由於我們從網路爬取的資料需要儲存起來以利我們後續的分析和查詢，所以這邊我們會使用 Python Google Sheets API 來將我們的資料儲存到 Google Sheets 上（當然你也可以使用其他儲存方式），方便我們接下來 LINE Bot API 查詢和比對使用。

建立 Google Sheets 試算表


Spreadsheet（試算表）是 Google Sheets 試算表的基本單位，當我們新增檔案時就是新增一個試算表。而 Worksheet（工作表）為試算表下的分頁單位，每個試算表可以有多個工作表。為切分不同的工作資料的單位。在工作表中直的為 Column（欄），橫的是 Row（列）。在指定的欄和列的區域是 Cell（儲存格），也是我們輸入資料值的地方。由一格格的儲存格網格和內含的資料就組成一份工作表。

設定 Google Sheets API
接著我們來設定 Google Sheets API，事實上 Google Sheets API 在使用上並不困難但是相關設定較為繁瑣。要開始使用 Google Sheets API 我們需要進入 Google Sheets API 後點選建立專案啟用 Google Sheets API。



另外，我們還需要申請 Service Account 服務帳號（意思是為給應用服務使用的帳戶，例如：我們的程式）和對應的金鑰，才能在我們的程式使用 Google Sheets API 進行操作。

建立專案和啟用 Google Sheets API 後我們會進入新增憑證的畫面：



這邊我們是要建立 Service Account 服務帳號，所以點選取消：



在下拉選單選擇建立服務帳戶：



自定義服務名稱：



直接點選繼續：



點選建立金鑰（選擇 JSON 格式），正常會下載一個 JSON 檔案，請妥善保存（此為你控制 Google Sheets API 的金鑰）：





金鑰檔案格式：



將其存成 credentials.json 檔案，方便接下來專案程式使用（放在同一個資料夾下）

安裝套件
接著我們在終端機安裝操作試算表的套件，在這邊我們使用 gspread 這個第三方套件（包裝方便使用）和驗證服務帳號套件 oauth2client，進行 Google Sheets API 的操作。

$ pip install gspread oauth2client
我們可以到 Google Drive 使用 Google 帳號登入後可以新增試算表：



另外，請先點選 Google Sheets 上的共用按鈕，我們將我們的試算表權限共享給金鑰中的 client_email ：



接著把 Google Sheets 網址中試算表 ID 複製下來，同樣輸出到環境變數上（也要放入 Heroku 的環境變數 SPREAD_SHEETS_KEY）。



環境變數為系統使用的變數，主要用來儲存參數設定值，讓系統中的程式可以讀取使用

若是 Windows 作業系統的請使用：

set SPREAD_SHEETS_KEY=xxxxxxx

# 列印出 %SPREAD_SHEETS_KEY% 看是否有設置成功
echo %SPREAD_SHEETS_KEY%
若是 MacOS 或是 Linux 作業系統的環境變數設定方式如下：

export SPREAD_SHEETS_KEY=xxxxxxx

# 列印出 $環境變數名稱 看是否有成功
echo $SPREAD_SHEETS_KEY


我們接下來要測試一下我們的金鑰是否可以正常使用，在 Python 使用 Google Sheets API 金鑰有兩種方式（Windows/MacOS/Linux 都適用），選擇一種使用即可：

直接讀取金鑰檔案
將金鑰檔案和程式放在同一個資料夾，使用 ServiceAccountCredentials.from_json_keyfile_name 方法讀取金鑰檔案，簡單方便。使用方式如下：

 # 金鑰檔案路徑
 credential_file_path = 'credentials.json'

 # auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
 def auth_gsp_client(file_path, scopes):
     # 從檔案讀取金鑰資料
     credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

     return gspread.authorize(credentials)

 gsp_client = auth_gsp_client(credential_file_path, gss_scopes)
使用環境變數讀取金鑰資訊
在終端機 Anaconda Prompt 或是 Terminal 使用環境變數儲存金鑰相關資訊。若是較注重資訊安全可以考慮使用，這樣就不需要將金鑰檔案提交到 git 上，但使用步驟較為繁瑣。主要操作方式是將金鑰內容透過環境變數組裝成一個 dict 後傳給 ServiceAccountCredentials.from_json_keyfile_dict 使用。

 def get_google_sheets_creds_dict():
     google_sheets_creds = {
         'type': os.environ.get('GOOGLE_SHEETS_TYPE'),
         'project_id': os.environ.get('GOOGLE_SHEETS_PROJECT_ID'),
         'private_key_id': os.environ.get('GOOGLE_SHEETS_PRIVATE_KEY_ID'),
         'private_key': os.environ.get('GOOGLE_SHEETS_PRIVATE_KEY'),
         'client_email': os.environ.get('GOOGLE_SHEETS_CLIENT_EMAIL'),
         'client_id': os.environ.get('GOOGLE_SHEETS_CLIENT_ID'),
         'auth_uri': os.environ.get('GOOGLE_SHEETS_AUTH_URI'),
         'token_uri': os.environ.get('GOOGLE_SHEETS_TOKEN_URI'),
         'auth_provider_x509_cert_url': os.environ.get('GOOGLE_SHEETS_AUTH_PROVIDER_X509_CERT_URL'),
         'client_x509_cert_url': os.environ.get('GOOGLE_SHEETS_CLIENT_X509_CERT_URL')
     }
     return google_sheets_creds

 # 取得組成 Google Sheets 金鑰
 google_sheets_creds_dict = get_google_sheets_creds_dict()

 # auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
 def auth_gsp_client(creds_dict, scopes):
     # 在設定環境變數時會系統會將 \n 換行符號轉成 \\n，所以讀入時要把它替換回來
     creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
     credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)

     return gspread.authorize(credentials)

 gsp_client = auth_gsp_client(google_sheets_creds_dict, gss_scopes)
Windows 設定環境變數：

 set GOOGLE_SHEETS_TYPE=xxxxx
 set GOOGLE_SHEETS_PROJECT_ID=xxxxx
 set GOOGLE_SHEETS_PRIVATE_KEY_ID=xxxxx
 set GOOGLE_SHEETS_PRIVATE_KEY=xxxxx
 set GOOGLE_SHEETS_CLIENT_EMAIL=xxxxx
 set GOOGLE_SHEETS_CLIENT_ID=xxxxx
 set GOOGLE_SHEETS_AUTH_URI=xxxxx
 set GOOGLE_SHEETS_TOKEN_URI=xxxxx
 set GOOGLE_SHEETS_AUTH_PROVIDER_X509_CERT_URL=xxxxx
 set GOOGLE_SHEETS_CLIENT_X509_CERT_URL=xxxxx
若要確認是否有寫入成功，可以使用：

 echo %GOOGLE_SHEETS_PRIVATE_KEY%
記得推送上去 Heroku 之前需要在 Heroku Settings 後台設定環境變數

MacOS/Linux 設定環境變數（特別注意在 GOOGLE_SHEETS_PRIVATE_KEY 因為有換行問題需要額外加 '' 單引號括起來）：

 export GOOGLE_SHEETS_TYPE=xxxxx
 export GOOGLE_SHEETS_PROJECT_ID=xxxxx
 export GOOGLE_SHEETS_PRIVATE_KEY_ID=xxxxx
 export GOOGLE_SHEETS_PRIVATE_KEY='xxxxx'
 export GOOGLE_SHEETS_CLIENT_EMAIL=xxxxx
 export GOOGLE_SHEETS_CLIENT_ID=xxxxx
 export GOOGLE_SHEETS_AUTH_URI=xxxxx
 export GOOGLE_SHEETS_TOKEN_URI=xxxxx
 export GOOGLE_SHEETS_AUTH_PROVIDER_X509_CERT_URL=xxxxx
 export GOOGLE_SHEETS_CLIENT_X509_CERT_URL=xxxxx
觀看成果：

 echo $GOOGLE_SHEETS_PRIVATE_KEY
同樣推送上去 Heroku 之前需要在 Heroku Settings 後台設定環境變數。

接著我們建立一個 clock_gsp.py 檔案：

# 引入套件
import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials 

# 我們使用 Google API 的範圍為 spreadsheets
gsp_scopes = ['https://spreadsheets.google.com/feeds']

# 讀入環境變數參數
SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')

# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

    return gspread.authorize(credentials)

gsp_client = auth_gsp_client(credential_file_path, gss_scopes)
# 我們透過 open_by_key 這個方法來開啟 sheet1 工作表一
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).sheet1
# 每次清除之前資料
worksheet.clear()

# 將資料插入第 1 列
worksheet.insert_row(['測試資料欄 1', '測試資料欄 2'], 1)


執行完程式後，我們可以發現我們成功透過程式將資料寫到 Google Sheets 了，Cheers！

接著我們延續 clock.py 這個程式把抓到的個股財報股價估算資料定期寫入 Google Sheets 中（計算出來的昂貴價、合理價、便宜價寫入第二列）：

import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials 
import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler

# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

# 我們使用 Google API 的範圍為 spreadsheets
gsp_scopes = ['https://spreadsheets.google.com/feeds']
SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')

# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

    return gspread.authorize(credentials)


gsp_client = auth_gsp_client(credential_file_path, gss_scopes)
# 我們透過 open_by_key 這個方法來開啟工作表一 worksheet
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).sheet1


def crawl_for_stock_price(sotck_no):
    print('擷取股票代號:', sotck_no)
    url = f'https://goodinfo.tw/StockInfo/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={sotck_no}&CHT_CAT=YEAR'

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
    }

    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    # 根據 HTTP header 的編碼解碼後的內容資料（ex. UTF-8）
    raw_html = resp.text

    print('raw_html', raw_html)

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

    # 取出最高 EPS 和最低 EPS，將字串轉為 float 浮點數小數
    max_eps = float(max(eps_rows))
    min_eps = float(min(eps_rows))
    # 取出最高本益比和最低本益比，將字串轉為 float 浮點數小數
    max_per = float(max(per_rows))
    min_per = float(min(per_rows))

    # PE = Price / EPS
    high_price = max_eps * max_per
    low_price = min_eps * min_per
    middle_price = (high_price + low_price) / 2
    # 將資料插入第 2 列
    print('開始寫入資料...')
    worksheet.insert_row([sotck_no, high_price, middle_price, low_price], 2)
    print('成功寫入資料...')


# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
@sched.scheduled_job('interval', minutes=5)
def crawl_for_stock_price_job():
    # 要注意不要太頻繁抓取
    print('每 5 分鐘執行一次程式工作區塊')
    # 每次清除之前資料
    worksheet.clear()
    # 將標頭插入第 1 列
    print('開始寫入標頭...')
    worksheet.insert_row(['stock_no', 'high_price', 'middle_price', 'low_price'], 1)
    print('成功寫入標頭...')
    sotck_no_list = ['2330']
    # 第一筆資料股票代號
    crawl_for_stock_price(sotck_no_list[0])

# 開始執行
sched.start()
開始執行：

python clock.py
後就會發現我們計算的資料已經寫入試算表中了！

讀取資料
若是要從 Google 讀取資料的話可以參考文件說明使用以下方法。

# 取出第一列的值
values_list = worksheet.row_values(1)

# 取出第一欄的值
values_list = worksheet.col_values(1)

# 取出所有值
list_of_lists = worksheet.get_all_values()
查詢即時股價
接著我們要透過 twstock 這個第三方套件進行台灣股市股票價格擷取，進而比對目前價格所在的區間帶。

首先，我們需要安裝套件 twstock 和 lxml：

$ pip install twstock lxml
接著我們可以使用以下方式取得即時股價：

from twstock import Stock

# 擷取台積電股價 '300.00'
latest_trade_price = twstock.realtime.get('2330')['realtime']['latest_trade_price']
"""
{
    'timestamp': 1583422151.0,
    'info': {
        'code': '2330', 'channel': '2330.tw', 'name': '台積電', 'fullname': '台灣積體電路製造股份有限公司', 'time': '2020-03-12 13:29:11'
    },
    'realtime': {
        'latest_trade_price': '300',
        'trade_volume': '7',
        'accumulate_trade_volume': '107548',
        'best_bid_price': [
            '268.00', '267.50', '267.00', '266.50', '266.00'
        ],
        'best_bid_volume': [
            '585', '528', '1411', '644', '1651'
        ],
        'best_ask_price': [
            '268.50', '269.00', '269.50', '270.00', '270.50'
        ],
        'best_ask_volume': [
            '162', '150', '115', '537', '342'
        ],
        'open': '265.00',
        'high': '276.50',
        'low': '265.00'
    },
    'success': True
}
"""
主動傳送訊息
主動傳送訊息 API

若是需要主動傳送資訊給使用者我們需要使用 Push API push_message 而非 reply_message ，然而 Push API 訊息在免費額度下有每月 500 則的限制，所以要留意不過度使用。



使用方式如下，需填入 USER_ID，messages 可以攜帶多個訊息元件：

line_bot_api.push_message(
    to={USER_ID},
    messages=[
        TextSendMessage(text='主動推送的文字')
    ]
 )
我們可以從 LINE App 後台查詢到我們自己的 User ID（在 Basic Settings）：



此時同樣把 User ID 存到我們的電腦環境變數：

若是 Windows 作業系統的請使用：

set LINE_USER_ID=xxxxxxx

# 列印出 %LINE_USER_ID% 看是否有設置成功
echo %LINE_USER_ID%
若是 MacOS 或是 Linux 作業系統的環境變數設定方式如下：

export LINE_USER_ID=xxxxxxx

# 列印出 $環境變數名稱 看是否有成功
echo $LINE_USER_ID
同樣於定時執行程式的 Heroku 後台環境變數中：LINE_USER_ID 設定。



整合建立判斷預警系統
由於 Heroku 預設的時區是 UTC+0 所以我們記得先把 Heroku App 的 config 加上 TZ（timezone）時區的設定，這樣才能使用 UTC+8 時區：

heroku config:add TZ="Asia/Taipei"
若是要在瀏覽器設定同樣是在後台的 Settings 的 Config Vars 部分設定：



這樣一來我們就可以設計一個定時執行程式在週間 9-14 整點，每小時執行一次：

@sched.scheduled_job('cron', day_of_week='mon-fri', hour='9-14')
def scheduled_job():
    print('每週週間 9am-14pm UTC+8. 執行此程式工作區塊!')
我們要確認目前股價的區間，所以我們設計一個函式進行條件判斷，傳入的參數有：stock_no、high_price、middle_price、low_price 和 latest_trade_price，最後會回傳目前是屬於哪一個區間的字串和目前成交價格。

def get_check_price_rule_message(stock_no, high_price, middle_price, low_price, latest_trade_price):
    """
    目前股價太貴了：成交價 > 昂貴價
    目前股價介於昂貴價和合理價之間：昂貴價 > 成交價 > 合理價
    目前股價介於合理價和便宜價之間：合理價 > 成交價 > 便宜價
    目前股價很便宜：便宜價 > 成交價
    """
    if latest_trade_price > high_price:
        message_str = f'{stock_no}:目前股價太貴了({latest_trade_price})'
    elif high_price > latest_trade_price and latest_trade_price > middle_price:
        message_str = f'{stock_no}:目前股價介於昂貴價和合理價之間({latest_trade_price})'
    elif middle_price > latest_trade_price and latest_trade_price > low_price:
        message_str = f'{stock_no}:目前股價介於合理價和便宜價之間({latest_trade_price})'
    elif low_price > latest_trade_price:
        message_str = f'{stock_no}:目前股價很便宜({latest_trade_price})'

    return message_str
設計一個定時執行程式在週間 9-14 整點，每小時執行一次（測試時可以改為每 30 秒執行 一次），同時要記得更新 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID 環境變數（本機端測試）和 Heroku 後台：

# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 設計一個定時執行程式在週間 9-14 整點，每小時執行一次
@sched.scheduled_job('cron', day_of_week='mon-fri', hour='9-14')
def get_notify():
    print('開始讀取資料')
    stock_item_lists = worksheet.get_all_values()
    # 目前以一檔股票為範例
    sotck_no_list = ['2330']
    for stock_item in stock_item_lists:
        stock_no = stock_item[0]
        high_price = stock_item[1]
        middle_price = stock_item[2]
        low_price = stock_item[3]
        if str(stock_no) in sotck_no_list:
            # 擷取即時成交價格
            latest_trade_price = twstock.realtime.get(stock_no)['realtime']['latest_trade_price']
            price_rule_message = get_check_price_rule_message(stock_no, high_price, middle_price, low_price, latest_trade_price)
            line_bot_api.push_message(
                to=LINE_USER_ID,
                messages=[
                    TextSendMessage(text=price_rule_message)
                ]
            )
    print('通知結束')
完整程式碼
以下為完整更新資料及判斷預警的定時執行程式，我們可以在本機端執行 python clock.py，若正常設定環境變數的話應該就可以執行我們的專案程式。

注意定期執行的排程會依照您設定的時間週期執行，並不會馬上執行，若要開發測試，可以改成比較短的時間來測試

import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials 
import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler
import twstock

from linebot import (
    LineBotApi
)

from linebot.models import (
    TextSendMessage,
)
# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

# 我們使用 Google API 的範圍為 spreadsheets
gsp_scopes = ['https://spreadsheets.google.com/feeds']
SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')

# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

    return gspread.authorize(credentials)


gsp_client = auth_gsp_client(credential_file_path, gss_scopes)
# 我們透過 open_by_key 這個方法來開啟工作表一 worksheet
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).sheet1


def crawl_for_stock_price(sotck_no):
    print('擷取股票代號:', sotck_no)
    url = f'https://goodinfo.tw/StockInfo/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={sotck_no}&CHT_CAT=YEAR'

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
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

    # 取出最高 EPS 和最低 EPS，將字串轉為 float 浮點數小數
    max_eps = float(max(eps_rows))
    min_eps = float(min(eps_rows))
    # 取出最高本益比和最低本益比，將字串轉為 float 浮點數小數
    max_per = float(max(per_rows))
    min_per = float(min(per_rows))

    # PE = Price / EPS
    high_price = max_eps * max_per
    low_price = min_eps * min_per
    middle_price = (high_price + low_price) / 2
    # 將資料插入第 2 列
    print('開始寫入資料...')
    worksheet.insert_row([sotck_no, high_price, middle_price, low_price], 2)
    print('成功寫入資料...')


# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
@sched.scheduled_job('interval', days=10)
def crawl_for_stock_price_job():
    # 要注意不要太頻繁抓取
    print('每 5 分鐘執行一次程式工作區塊')
    # 每次清除之前資料
    worksheet.clear()
    # 將標頭插入第 1 列
    print('開始寫入標頭...')
    worksheet.insert_row(['stock_no', 'high_price', 'middle_price', 'low_price'], 1)
    print('成功寫入標頭...')
    sotck_no_list = ['2330']
    # 第一筆資料股票代號
    crawl_for_stock_price(sotck_no_list[0])


def get_check_price_rule_message(stock_no, high_price, middle_price, low_price, latest_trade_price):
    """
    目前股價太貴了：成交價 > 昂貴價
    目前股價介於昂貴價和合理價之間：昂貴價 > 成交價 > 合理價
    目前股價介於合理價和便宜價之間：合理價 > 成交價 > 便宜價
    目前股價很便宜：便宜價 > 成交價
    """
    if latest_trade_price > high_price:
        message_str = f'{stock_no}:目前股價太貴了({latest_trade_price})'
    elif high_price > latest_trade_price and latest_trade_price > middle_price:
        message_str = f'{stock_no}:目前股價介於昂貴價和合理價之間({latest_trade_price})'
    elif middle_price > latest_trade_price and latest_trade_price > low_price:
        message_str = f'{stock_no}:目前股價介於合理價和便宜價之間({latest_trade_price})'
    elif low_price > latest_trade_price:
        message_str = f'{stock_no}:目前股價很便宜({latest_trade_price})'

    return message_str


# 設計一個定時執行程式在週間 9-14 整點，每小時執行一次
@sched.scheduled_job('cron', day_of_week='mon-fri', hour='9-14')
def get_notify():
    print('開始讀取資料')
    stock_item_lists = worksheet.get_all_values()
    # 目前以一檔股票為範例
    sotck_no_list = ['2330']
    for stock_item in stock_item_lists:
        stock_no = stock_item[0]
        high_price = stock_item[1]
        middle_price = stock_item[2]
        low_price = stock_item[3]
        if str(stock_no) in sotck_no_list:
            # 擷取即時成交價格
            latest_trade_price = twstock.realtime.get(stock_no)['realtime']['latest_trade_price']
            price_rule_message = get_check_price_rule_message(stock_no, high_price, middle_price, low_price, latest_trade_price)
            line_bot_api.push_message(
                to=LINE_USER_ID,
                messages=[
                    TextSendMessage(text=price_rule_message)
                ]
            )
    print('通知結束')

# 開始執行
sched.start()
常見 Heroku 指令
$ 為終端機提示字元，不用輸入

登入 Heroku
$ heroku login
推送到 Heroku
初始化 Git repository 將目前工作資料夾變成 Git 追蹤的資料夾：

$ git init
將 remote 遠端程式庫位置設定為 heroku app（-a 為 application 意思）：git:remote adds a git remote to an app repo。

$ heroku git:remote -a 你的 heroku app 名稱
將檔案加入 git staging 暫存區：

$ git add xxxx
提交到本地程式庫：

$ git commit -a -m "first commit"
提交到遠端 Heroku（會看到一連串安裝套件和啟動伺服器訊息，若看到 remote: Verifying deploy... done. 代表成功 deploy 部屬）：

$ git push heroku master
在 Heroku App Server 下指令
$ heroku run {終端機指令} -a {heroku app 名稱}
停止定時執行的 Heroku App
$ heroku ps:scale clock=0 -a {heroku app 名稱}
查詢 Heroku App log
--tail 是持續列印

$ heroku logs --tail -a {heroku app 名稱}
總結
經過這次的股票投資聊天機器人專案實作（說真的對於初學者來說有點小複雜，但若成功完成整合過去所學是很有成就感的，大家加油！），我們最後整合成為一個每 10 天固定更新預估股價資料於 Google Sheets 並於週間 9-14 整點，每小時執行一次預警通知，讀取 Google Sheets 資料和即時股價進行比對並推送給使用者。

以上的範例主要為教學使用，同學可以根據自己的需求進行修改設計和調整。在這個專案實作中最重要的是建立定期執行程式的觀念和了解 LINE Messaging Push API 跟 twstock 即時查詢台灣股票資訊等的套件使用方式並掌握如何使用 Google Sheets API 當作儲存資料的儲存地（這部份接下來還有機會使用到）。

事實上，我們只要掌握了 LINE Messaging API 和 Google Sheets API 以及相關套件的使用方式後，我們就可以根據自己的需求開發屬於自己的股票投資聊天機器人專案了！

