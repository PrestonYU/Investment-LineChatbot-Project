import os

# 引入套件 flask
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
# 引入 linebot 異常處理
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
# 引入 linebot 訊息元件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import requests
from bs4 import BeautifulSoup
# 引用 BlockingScheduler 類別
from apscheduler.schedulers.blocking import BlockingScheduler


app = Flask(__name__)

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('')
LINE_CHANNEL_SECRET = os.environ.get('')
line_bot_api = LineBotApi('')
handler = WebhookHandler('')
to = ""

# 此為歡迎畫面處理函式，當網址後面是 / 時由它處理
@app.route("/", methods=['GET'])
def hello():
    return 'hello heroku'

# 此為 Webhook callback endpoint 處理函式，當網址後面是 /callback 時由它處理
@app.route("/callback", methods=['POST'])
def callback():
    # 取得網路請求的標頭 X-Line-Signature 內容，確認請求是從 LINE Server 送來的
    signature = request.headers['X-Line-Signature']

    # 將請求內容取出
    body = request.get_data(as_text=True)

    # handle webhook body（轉送給負責處理的 handler，ex. handle_message）
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

def crawl_for_stock_price():
    url = 'https://goodinfo.tw/StockInfo/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=2330&CHT_CAT=YEAR'
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


# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
@sched.scheduled_job('interval', minutes=5)
def timed_job():
    # 要注意不要太頻繁抓取
    print('每 5 分鐘執行一次程式工作區塊')
    crawl_for_stock_price()

# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    # event.message.text 為使用者的輸入，把它原封不動回傳回去
#    line_bot_api.reply_message(
#        event.reply_token,
#        TextSendMessage(text=event.message.text))
    #user_id = event.source.user_id
    #print("user_id =", user_id)
        
    url = 'https://goodinfo.tw/StockInfo/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=2330&CHT_CAT=YEAR'
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

    try:
        line_bot_api.push_message(to, TextSendMessage(text='＝＝＝＝＝台積電股價快報＝＝＝＝＝'))
        line_bot_api.push_message(to, TextSendMessage(text='max_eps' + ' : ' + max_eps))
        line_bot_api.push_message(to, TextSendMessage(text='min_eps' + ' : ' + min_eps))
        line_bot_api.push_message(to, TextSendMessage(text='max_per' + ' : ' + max_per))
        line_bot_api.push_message(to, TextSendMessage(text='min_per' + ' : ' + min_per))
        #TextSendMessage(text=)

    except LineBotApiError as e:
        # error handle 
        raise e


# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 開始執行
    sched.start()
    # 此處不使用 reol.it，所以不用設定 IP 和 Port，flask 預設為 5000 port
    app.run()
