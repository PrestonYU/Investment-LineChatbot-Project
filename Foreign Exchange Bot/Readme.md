# 外幣管理聊天機器人專案實作 I

## 前言
許多投資人和企業單位將買賣外幣當作一種投資和避險方式。在合適的價格低買高賣外幣確實有機會可以獲得不錯的報酬。然而隨著交易量的增加，我們往往會忘記當初成交的價格和購買的數量，久而久之就忘記了目前到底投資報酬率是正還是負，白白錯失了獲利機會。所以在我們外幣管理聊天機器人專案實作中，我們將製作一個的外幣管理聊天機器人，讓我們可以隨時掌握外幣買賣的最新資訊。預計規劃主要功能如下：
1.查詢外幣對新台幣匯率
2.紀錄外匯交易資料、查詢目前損益

## 外幣匯率基礎
在開始專案前我們先來認識一下外幣匯率基礎。若是我們想買賣外幣，賺取價差和未來走勢，最重要是看懂銀行匯率。在銀行的各分行和官方網站中有公告牌告匯率資訊方便客戶查詢
（一般最常使用的是台灣銀行網站的匯率），牌告匯率一般常見的有四種：「現金買入」、「現金賣出」、「即期買入」、「即期賣出」這四種牌告利率。
以下介紹四種匯率的差異（注意：一般民眾對於買入賣出很容易搞混，記得這幾種匯率都是以 銀行本行端 為視角）

>將角色換作銀行端來思考就更容易理解牌告匯率的差異

接著我們更進一步來看現金匯率和即期匯率的差異，其實主要差異在於現鈔的部分，因為對於銀行端來說，出現現鈔代表的管理成本上升，
除了要檢驗是否為偽鈔或是處理鈔票破損等問題，所以一般來說現金匯率對於一般民眾來說會比較差。

現金匯率和即期匯率差異比較：
1.現金匯率：交易過程出現現鈔，主要於出差旅行需要買賣外幣現鈔
2.即期匯率：交易過程沒有出現現鈔，主要是在帳戶中買賣外幣

>現金買入匯率:民眾將外幣現鈔賣給銀行換回新台幣（銀行買入）
>現金賣出匯率:民眾用新台幣向銀行買外幣現鈔（銀行賣出）
>即期買入匯率:民眾將帳戶中的外幣賣給銀行換回新台幣（銀行買入）	
>即期賣出匯率:民眾在帳戶中用新台幣向銀行買外幣（銀行賣出）

## 使用 twder 匯率查詢套件
在 Python 中若是我們希望查詢新台幣對外幣匯率，一種方式是使用網路爬蟲方式網路資料，例如：爬取台灣銀行網站的匯率）或是使用第三方套件，例如：twder 匯率查詢套件。在這裡我們使用 twder 這個第三方套件進行教學說明。

### 安裝套件
首先，我們先打開終端機，在指令列中使用以下指令進行安裝套件：
```
pip install twder
```
若是使用 Jupyter Notebook 則使用：
```
!pip install twder
```
引入套件：
```
import twder
```
### 使用範例
接著，我們來使用看看如何使用 twder 套件：

#### 取得幣別清單列表
```
twder.currencies()
# ['CNY', 'THB', 'SEK', 'USD', 'IDR', 'AUD', 'NZD', 'PHP', 'MYR', 'GBP', 'ZAR', 'CHF', 'VND', 'EUR', 'KRW', 'SGD', 'JPY', 'CAD', 'HKD']
```
#### 取得目前所有幣別匯率
```
twder.now_all()
# {'THB': ('2017/01/06 16:00', '0.7918', '0.9348', '0.8803', '0.9203'), ...}
# {貨幣代碼: (時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...}
```
#### 取得目前特定幣別匯率報價
```
twder.now('JPY')
# ('2017/01/06 16:00', '0.2668', '0.2778', '0.2732', '0.2772')
# (時間, 現金買入, 現金賣出, 即期買入, 即期賣出)
```
#### 取得昨天特定幣別匯率報價
```
twder.past_day('JPY')
# [('2017/01/06 09:02:04', '0.2671', '0.2781', '0.2735', '0.2775'), ...]
# [(時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...]
```
#### 取得過去半年特定幣別匯率報價
```
twder.past_six_month('JPY')
# [('2017/01/06', '0.2668', '0.2778', '0.2732', '0.2772'), ...]
# [(時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...]
```
#### 取得特定期間半年特定幣別匯率報價
注意：有可能太久之前的歷史資料無法抓取。
```
twder.specify_month('JPY', 2019, 12)
# [('2019/12/30', '0.2672', '0.2782', '0.2736', '0.2776'), ...]
# [(時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...]
```


## 建立聊天機器人專案
在過去幾次的專案實作中，相信同學已經掌握了建立聊天機器人專案的基本開發步驟流程：

1.於 LINE 後台建立新的 Bot Channel
2.於 Heroku App 建立新的 App
3.設定環境變數和金鑰（`LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET`）
4.建立一個新的資料夾和專案初始程式碼（`line_app.py`，可自行命名）
5.本機端測試（Flask Server + ngrok），設定 Webhook URL
6.將程式推送到 Heroku 遠端，設定 Webhook URL
7.在 LINE App 上使用

於 Windows 打開終端機設定環境變數：
```
set LINE_CHANNEL_ACCESS_TOKEN={你的 LINE_CHANNEL_ACCESS_TOKEN}
set LINE_CHANNEL_SECRET={你的 LINE_CHANNEL_SECRET}
```
若是 MacOS / Linux 打開終端機設定環境變數：
```
export LINE_CHANNEL_ACCESS_TOKEN={你的 LINE_CHANNEL_ACCESS_TOKEN}
export LINE_CHANNEL_SECRET={你的 LINE_CHANNEL_SECRET}
```
當我們熟悉了匯率查詢套件的使用方式後，我們要將我們的匯率查詢功能整合進入我們的聊天機器人中。首先我們先在 LINE 後台建立新的 Bot Channel、於 Heroku App 建立新的 App 並設定設定環境變數和金鑰，然後於 VS Coder 建立一個聊天機器人專案資料夾並建立專案初始程式碼。

`line_app.py`：
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

app = Flask(__name__)


# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == '__main__':
    app.run()
```

## 建立查詢所有幣別匯率功能
首先我們先建立一個函式，當呼叫這個函式時我們會將 twder 套件查詢到的所有幣別匯率資訊組成字串回傳。由於查詢到的匯率資訊是由一個 dict 所組成（`{str: tuple}`），所以我們需要將其格式化後整理成易於閱讀的字串後回傳，格式如下：
```
[貨幣代號] 現金買入, 現金賣出, 即期買入, 即期賣出, 時間
```
程式碼：
```
def get_all_currencies_rates_str():
    """取得所有幣別目前匯率字串
    """
    all_currencies_rates_str = ''
    # all_currencies_rates 是一個 dict
    all_currencies_rates = twder.now_all()

    # 取出 key, value : {貨幣代碼: (時間, 現金買入, 現金賣出, 即期買入, 即期賣出), ...}
    # (時間, 現金買入, 現金賣出, 即期買入, 即期賣出) 是個 tuple，我們使用 index 取得內含元素
    for currency_code, currency_rates in all_currencies_rates.items():
        # \ 為多行斷行符號，避免組成字串過長
        all_currencies_rates_str += f'[{currency_code}] 現金買入:{currency_rates[1]} \
            現金賣出:{currency_rates[2]} 即期買入:{currency_rates[3]} 即期賣出:{currency_rates[4]} ({currency_rates[0]})\n'
    return all_currencies_rates_str
```
## 整合聊天機器人查詢所有幣別匯率功能
接著我們讓使用者輸入 `@查詢所有匯率`（我們也可以使用圖文選單來節省輸入時間）。查詢所有貨幣對新台幣匯率資訊。

程式碼：
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
```

## 總結
以上我們學習了外幣匯率的基礎知識並整合第三方套件建立一個簡單的查詢外幣對新台幣匯率的聊天機器人。
相信經歷過這幾個動手實作的聊天機器人專案後（若還不熟悉的同學可以持續多練習），同學們會更了解如何整合財務相關資訊開發一個實用的聊天機器人專案的流程。
接下來我們還要讓使用者可以紀錄每次的交易和查詢損益的結果。
