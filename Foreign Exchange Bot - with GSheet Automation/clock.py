import os

# 引入套件 flask
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
# 引入 linebot 異常處理
from linebot.exceptions import (
    InvalidSignatureError
)
# 引入 linebot 訊息元件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
# 引用查詢匯率套件
import twder

# Spread Sheets API 套件
import gspread
from oauth2client.service_account import ServiceAccountCredentials 

app = Flask(__name__)

# 我們使用 Google API 的範圍為 spreadsheets
gss_scopes = ['https://spreadsheets.google.com/feeds']
GOOGLE_SHEETS_CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDS_JSON')
SPREAD_SHEETS_KEY = ''

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN =''
LINE_CHANNEL_SECRET = ''
LINE_USER_ID = ''
line_bot_api = LineBotApi('')
handler = WebhookHandler('')

def get_all_currencies_rates_str():
    """取得所有幣別目前匯率字串
    """
    all_currencies_rates_str = ''
    # all_currencies_rates 是一個 dict
    all_currencies_rates = twder.now_all()

    # 取出 key, value : {貨幣代碼: (時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...}
    # (時間, 現金買入, 現金賣出, 即期買入, 即期賣出) 是個 tuple
    for currency_code, currency_rates in all_currencies_rates.items():
        # \ 為多行斷行符號，避免組成字串過長
        all_currencies_rates_str += f'[{currency_code}] 現金買入:{currency_rates[1]} \
            現金賣出:{currency_rates[2]} 即期買入:{currency_rates[3]} 即期賣出:{currency_rates[4]} ({currency_rates[0]})\n'
    return all_currencies_rates_str


# 金鑰檔案路徑
credential_file_path = 'credentials.json'

# auth_gsp_client 為我們建立來產生金鑰認證物件回傳給操作 Google Sheet 的客戶端 Client
def auth_gsp_client(file_path, scopes):
    # 從檔案讀取金鑰資料
    credentials = ServiceAccountCredentials.from_json_keyfile_name(file_path, scopes)

    return gspread.authorize(credentials)


gsp_client = auth_gsp_client(credential_file_path, gss_scopes)
# 我們透過 open_by_key 這個方法來開啟工作表一 worksheet
worksheet = gsp_client.open_by_key(SPREAD_SHEETS_KEY).worksheet('transaction')


def record_currency_transaction(action, currency, unit):
    """紀錄交易
    :params action: 買/賣
    :params currency: ['CNY', 'THB', 'SEK', 'USD', 'IDR', 'AUD', 'NZD', 'PHP', 'MYR', 'GBP', 'ZAR', 'CHF', 'VND', 'EUR', 'KRW', 'SGD', 'JPY', 'CAD', 'HKD']
    :params unit: 數量
    """
    current_row_length = len(worksheet.get_all_values())
    currency_data = twder.now(currency)
    # 取出日期
    transaction_date = currency_data[0].split(' ')[0]

    if action == '買':
        # 即期賣出
        currency_price = currency_data[4]
    elif action == '賣':
        # 即期買入
        currency_price = currency_data[3]

    # 寫入試算表欄位：交易日期, 交易幣別, 買進賣出, 交易單位, 單位價格
    worksheet.insert_row([transaction_date, currency, action, unit, currency_price], current_row_length + 1)

    return True


def get_currency_net_profit():
    records = worksheet.get_all_values()
    """
    等同於
    currency_statistics_data = {
        currency: (0, 0)
        for currency in twder.currencies()
    }
    """
    currency_statistics_data = {}
    print('計算中...')
    for index, record in enumerate(records):
        # 若為標頭跳過
        if index == 0:
            continue
        currency = record[1]
        action = record[2]
        unit = float(record[3])
        price = float(record[4])
        # 計算交易成本
        cost = unit * price

        # 建立暫存統計資料
        if currency not in currency_statistics_data:
            currency_statistics_data[currency] = {}
            currency_statistics_data[currency]['total_cost'] = 0
            currency_statistics_data[currency]['total_unit'] = 0
        # 計算交易總成本
        if action == '買':
            currency_statistics_data[currency]['total_cost'] += cost
            currency_statistics_data[currency]['total_unit'] += unit
        elif action == '賣':
            currency_statistics_data[currency]['total_cost'] -= cost
            currency_statistics_data[currency]['total_unit'] -= unit

    currency_net_profit_str = ''
    # calculate net_profit
    for currency, currency_data in currency_statistics_data.items():
        now_currency_data = twder.now(currency)
        # 淨利：現在賣出的價格(即期買入) * 剩餘數量 - 交易總成本
        # EX. USD: (2000 - 350 - 128) * 30.205 - (2000 * 30.345 - 350 * 30.235 - 128 * 30.235)
        # EX. JPY: (20000 + 200) * 0.2713 - (20000 * 0.2753 + 200 * 0.2754)
        # 若 即期買入 有值，則計算損益
        if now_currency_data[3] != '-':
            current_price = float(now_currency_data[3])
            net_profit = current_price * currency_data['total_unit'] - currency_data['total_cost']
            currency_net_profit_str += f'[{currency}]損益:{net_profit:.2f}\n'

    return currency_net_profit_str


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


# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    user_input = event.message.text
    if user_input == '@查詢所有匯率':
        all_currencies_rates_str = get_all_currencies_rates_str()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=all_currencies_rates_str))
    # 輸入格式：買賣/幣別/數量 EX.買/USD/2000
    elif '買/' in user_input or '賣/' in user_input:
        split_user_input = user_input.split('/')
        action = split_user_input[0]
        currency = split_user_input[1]
        unit = split_user_input[2]
        record_currency_transaction(action, currency, unit)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='紀錄完成'))
    elif user_input == '@查詢損益':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='計算中'))
        currency_net_profit = get_currency_net_profit()
        # 由於計算時間有可能超過 reply_message 回覆期間 reply_token 會過期
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=currency_net_profit))

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == '__main__':
    app.run()




















