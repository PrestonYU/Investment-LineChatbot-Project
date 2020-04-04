import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials 
import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler
import twstock
import lxml

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
SPREAD_SHEETS_KEY = os.environ.get('1QHX3S95UX2H9tYQh6Coaa5twI3jFND3jwXSGd10I3X0')

# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('nLyCdZ4kzatkPZUUj4ViznwnhOPxgvbShn4kKokNGjGGLBDdwjUUQv6+/OnxUVEO9rYs3Au7Fha78D3tq/tw2dX6YJvKw99dtaTYktJXvcrpBp7IVNkLtJpjzaBXmzMeiveIeTDVgRY6umdZcMzbZwdB04t89/1O/w1cDnyilFU=')
LINE_USER_ID = os.environ.get('U3300261b0de23fe43e93f5f4d63ce4e0')
line_bot_api = LineBotApi('nLyCdZ4kzatkPZUUj4ViznwnhOPxgvbShn4kKokNGjGGLBDdwjUUQv6+/OnxUVEO9rYs3Au7Fha78D3tq/tw2dX6YJvKw99dtaTYktJXvcrpBp7IVNkLtJpjzaBXmzMeiveIeTDVgRY6umdZcMzbZwdB04t89/1O/w1cDnyilFU=')

# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

    return gspread.authorize(credentials)


gsp_client = auth_gsp_client(credential_file_path, gsp_scopes)
# 我們透過 open_by_key 這個方法來開啟工作表一 worksheet
worksheet = gsp_client.open_by_key('1QHX3S95UX2H9tYQh6Coaa5twI3jFND3jwXSGd10I3X0').sheet1


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
#@sched.scheduled_job('cron', day_of_week='mon-fri', hour='9-14')
@sched.scheduled_job('interval', minutes=1)

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
                to='U3300261b0de23fe43e93f5f4d63ce4e0',
                messages=[
                    TextSendMessage(text=price_rule_message)
                ]
            )
    print('通知結束')

# 開始執行
crawl_for_stock_price_job()    
sched.start()