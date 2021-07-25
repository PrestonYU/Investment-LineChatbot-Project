# 外幣管理聊天機器人專案實作 II

## 前言
在我們外幣管理聊天機器人專案實作中，我們將製作一個的外幣管理聊天機器人，讓我們可以隨時掌握外幣買賣的最新資訊。預計規劃主要功能如下：
1.查詢外幣對新台幣匯率
2.紀錄外匯交易資料、查詢目前損益
在前一堂課程中我們已經建立了專案的基本架構：一個可以查詢匯率的聊天機器人！緊接著我們要整合 Google Sheets API 讓我們可以透過聊天機器人來紀錄我們的外匯交易和損益試算查詢。

## 紀錄外幣交易
### Google Sheets 試算表設定
首先，我先將我們開好的試算表加入標頭 `交易日期, 交易幣別, 買進賣出, 交易單位, 成交金額`，將 工作表一 改成 `transaction`（可以自行命名）。

交易日期 | 交易幣別 |	買進賣出 |	交易單位 | 單位價格 
---------------------------------------------
外幣交易日期 ex. 2020/03/21 |	外幣交易幣別總類 ex. USD | 買進或賣出 ex. 買 | 買賣交易單位 ex. 2000 | 交易單位價格 ex. 30.345


### 整合聊天機器人輸入
在我們的教學範例中我們希望讓使用者可以輸入格式：`買賣/幣別/數量`，例如：`買/USD/2000` 就可以紀錄該筆外幣買賣紀錄。我們拆解使用者輸入後將操作指令當作參數傳入紀錄函式中，最後回傳紀錄成功結果，我們就可以在我們的試算表中看到新增的交易紀錄。
```
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
    # 判斷是否符合格式
    elif '買/' in user_input or '賣/' in user_input:
        # 依序取出 買賣/幣別/數量
        split_user_input = user_input.split('/')
        action = split_user_input[0]
        currency = split_user_input[1]
        unit = split_user_input[2]
        # 呼叫計算函式
        record_currency_transaction(action, currency, unit)

        # 回傳結果
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='紀錄完成'))
```
### 建立計算函式
我們的交易紀錄函式主要是將使用者輸入格式化後將交易日期, 交易幣別, 買進賣出, 交易單位, 單位價格等資料寫入試算表中。我們透過 twder 第三方套件取得該幣別匯率資訊並根據買或賣來決定使用即期賣出或即期買入的單位價格（還記得即期賣出是銀行賣出外幣，即期買入是銀行買回外幣嗎？）。
```
def record_currency_transaction(action, currency, unit):
    """紀錄交易
    :params action: 買/賣
    :params currency: ['CNY', 'THB', 'SEK', 'USD', 'IDR', 'AUD', 'NZD', 'PHP', 'MYR', 'GBP', 'ZAR', 'CHF', 'VND', 'EUR', 'KRW', 'SGD', 'JPY', 'CAD', 'HKD']
    :params unit: 數量
    """
    current_row_length = len(worksheet.get_all_values())
    # 透過 twder 第三方套件取得該幣別匯率資訊
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
    # 目前資料數量 current_row_length 多 + 1 筆
    worksheet.insert_row([transaction_date, currency, action, unit, currency_price], current_row_length + 1)

    return True
```

## 查詢計算損益
由於 reply_message API 回傳有時間限制，若是我們的結果計算太久會來不及回傳，所以我們需要另外使用 push_message API。
我們可以從 LINE App 後台查詢到我們自己的 `User ID`（在 Basic Settings）

若是 Windows 作業系統的請使用：
```
set LINE_USER_ID=xxxxxxx

# 列印出 %LINE_USER_ID% 看是否有設置成功
echo %LINE_USER_ID%
```
若是 MacOS 或是 Linux 作業系統的環境變數設定方式如下：
```
export LINE_USER_ID=xxxxxxx

# 列印出 $環境變數名稱 看是否有成功
echo $LINE_USER_ID
```
同樣於定時執行程式的 Heroku 後台環境變數中：`LINE_USER_ID` 設定。

### 整合聊天機器人輸入
接著我們要讓使用者可以查詢損益，這邊我們教學範例設計當使用者輸入：`@查詢損益` 時（當然你也可以使用圖文選單節省輸入），
會計算目前試算表中的交易總成本和目前查詢的匯率價格所計算的獲利的損益。由於計算時間有可能超過 reply_message 回覆期間 reply_token 有可能會過期，所以我們使用 push_message API。
```
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
        # 由於計算時間有可能超過 reply_message 回覆期間 reply_token 會過期，所以我們使用 push_message
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=currency_net_profit))
```
### 建立計算損益函式
我們建立一個計算損益函式 `get_currency_net_profit` 來計算我們試算表中交易資料的損益。主要計算公式如下：
```
#計算淨利：現在賣出的價格(即期買入) * 剩餘貨幣數量 - 交易總成本
```
用以下交易範例為例：

>美金（USD）的數量最後為 `1522 (2000 - 350 - 128)`，其交易成本 `(2000 * 30.345 - 350 * 30.235 - 128 * 30.235)`。
>假設目前即期買入價格為 `30.205`，賣出的獲利 `(2000 - 350 - 128) * 30.205`。

損益計算: `(2000 - 350 - 128) * 30.205 - (2000 * 30.345 - 350 * 30.235 - 128 * 30.235)`

>日幣（JPY）的數量最後為 `20200 (20000 + 200)`，其交易成本 `(20000 * 0.2753 + 200 * 0.2754)`。
>假設目前即期買入價格為 `0.2713`，賣出的獲利 `(20000 + 200) * 0.2713`。

損益計算: `(20000 + 200) * 0.2713 - (20000 * 0.2753 + 200 * 0.2754)`

```
def get_currency_net_profit():
    # 取出所有試算資料
    records = worksheet.get_all_values()
    currency_statistics_data = {}
    print('計算中...')
    # 將所有列資料取出計算
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
        # 若 即期買入 有值，則計算損益，若為 - 則代表沒值
        if now_currency_data[3] != '-':
            current_price = float(now_currency_data[3])
            net_profit = current_price * currency_data['total_unit'] - currency_data['total_cost']
            # 取到小數第二位
            currency_net_profit_str += f'[{currency}]損益:{net_profit:.2f}\n'

    return currency_net_profit_str
```

## 整合外幣管理聊天機器人專案
在完成了我們專案程式後我們可以利用 Flask 本地端 Server 搭配 ngrok 進行本地端測試，同樣測試沒問題後我們可以推送到 Heroku App 上，在我們的 LINE 進行測試。

### 專案完整程式碼
```
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
SPREAD_SHEETS_KEY = os.environ.get('SPREAD_SHEETS_KEY')

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
```
## 總結
在我們外幣管理聊天機器人專案實作中，我們製作了一個的外幣管理聊天機器人，讓我們可以隨時掌握外幣買賣的最新資訊。包括功能有：
1.查詢外幣對新台幣匯率
2.紀錄外匯交易資料、查詢目前損益
恭喜你已經可以透過程式設計打造一個屬於自己的外幣管理聊天機器人！
