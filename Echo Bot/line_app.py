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

app = Flask(__name__)


# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('vIEMDW2+VTG81Q5Vt3i3Y70SY89OzMyyQtwqTrtP6ycFMMt5s0oA2P138w+Po9Eble1lDCC7BCRS4kXMyt+gF43ZXYZNDET8drpiiTw4yvD8mgegJjFKdd7dLsium68n8jwPcJeRcIfAa4x9vNzqlgdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.environ.get('2a03f191746f5d8ecc6ab85e50c8b820')
line_bot_api = LineBotApi('vIEMDW2+VTG81Q5Vt3i3Y70SY89OzMyyQtwqTrtP6ycFMMt5s0oA2P138w+Po9Eble1lDCC7BCRS4kXMyt+gF43ZXYZNDET8drpiiTw4yvD8mgegJjFKdd7dLsium68n8jwPcJeRcIfAa4x9vNzqlgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('2a03f191746f5d8ecc6ab85e50c8b820')

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
    app.logger.info("Request body: " + body)
    
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
    # event.message.text 為使用者的輸入，把它原封不動回傳回去
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 此處不使用 reol.it，所以不用設定 IP 和 Port，flask 預設為 5000 port
    app.run()