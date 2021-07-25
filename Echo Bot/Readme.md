# Web Server 專案部屬基礎

### 前言
在前面的課程中，我們學習了 LINE 聊天機器人基礎並學習如何使用 Git 管理我們的程式碼，將程式上傳到遠端的程式庫中（Github）。然而過去一段時間我們主要使用本機伺服器 （Local Server）的方式進行，若是要一直執行程式的話就必須讓電腦一直開機，十分不便。所以接下來我們將嘗試把我們的 LINE 聊天機器人 Web Server 部屬到雲端伺服器上（Heroku），方便使用者使用（這也是目前許多網路應用服務開發的方式之一）。

### 雲端伺服器（Cloud Server）概要
Cloud Computing 雲端運算一直是過去幾年資訊科技火紅的名詞。事實上，雲端的雲朵代表是的網路的意思（因為一般工程師在溝通時使用雲朵來代表網路），相對於本機或是裝置端而言，雲端就是你即便不知道雲端背後有多少伺服器或運算資源但你還是可以透過網路去使用運算或儲存的資源服務。事實上，雲端運算技術的成熟對於剛成立的新創小公司來說是非常重要的資源，可以讓新創公司更加專注在核心技術上而不用顧慮伺服器設備維護。

一般來說雲端運算由上層到底層主要分為三個層面：
**SaaS（Software as Service）**：軟體即服務，亦即將軟體當作網路服務一樣隨選使用，用多少算多少，而不是買斷一個套裝軟體。例如：我們平常使用的 Gmail 電子信箱服務 VS. 傳統 Outlook 電子郵件軟體，或是 Dropbox 雲端儲存服務。
**PaaS（Platform as Service）**：平台即服務，亦即將提供一個開發平台給開發者/軟體工程師，讓開發者可以很容易擴展自己的服務並專注在程式開發而不用管硬體和基礎建設的維護上。我們這堂課程主要要介紹的 Heroku 就是這樣一個服務，接下來我們會更進一步介紹。
**IaaS（Infrastructure as Service）**：基礎設施即服務，亦即將基礎設計當作服務提供給使用者使用。過往我們在架設伺服器時往往需要自建機房，從採買設備到維護機房、架設伺服器等事情都要處理，耗費不少資源。然而，現在透過雲端服務，我們可以很容易租用到便宜好用的伺服器並省下來維護和擴展成本。目前在市場上有幾家大型廠商 Amazon（AWS）、Google（GCP） 和 Microsoft（Azure） 等佔據了主要市場。


### Heroku 雲端服務初體驗
由於 IaaS 的部分牽涉到許多伺服器設定等網站開發進階議題適合在後端網頁開發的課程作討論，所以我們會專注在使用 PaaS 平台服務，專注在我們的 LINE Bot 聊天機器人應用開發上。由於 Heroku 在一定額度下是免費（額度說明）且容易使用並提供豐富的串接資料庫、add-on 資源，所以我們接下來會使用之前的回聲聊天機器人範例程式將其部屬到 Heroku 雲端伺服器上，這樣一來我們就不用一直將我們本機伺服器和 ngrok 開啟（僅開發時需要）。

#### 註冊使用者帳戶
首先我們先點選 Sign Up 按鈕註冊一個 Heroku 的使用者帳號，若已有帳號直接登入即可。
#### 建立 Heroku App
接著我們點選 New 按鈕，Create new app，新增一個 Heroku App（代表一個網路應用服務）。接著輸入你想要命名的 App 名稱，這個也會影響你之後網址的名稱：`https://{ Heroku App名稱}.herokuapp.com`，國家選擇美國，點選創建 App。
成功建立 App 後會進入 App 的管理後台。此時點選右上角的 Open app 就可以開啟看到你的網頁應用程式。那個網址就是你的應用程式網址。
#### 建立 LINE Chatbot 聊天機器人程式
接著我們可以使用之前的回聲機器人的程式碼並略作修改，其中設定參數改為使用 `os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')` 和 `os.environ.get('LINE_CHANNEL_SECRET')` 其使用 Python 內建的 os 套件取出環境變數。所謂的環境變數就是儲存在電腦系統的暫存常數資料，供系統或是應用程式使用，常見的是一些設定值。

我們先創建一個資料夾，然後新增一個檔案 `line_app.py`：

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
    # event.message.text 為使用者的輸入，把它原封不動回傳回去
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

# __name__ 為內建變數，若程式不是被當作模組引入則為 __main__
if __name__ == "__main__":
    # 此處不使用 reol.it，所以不用設定 IP 和 Port，flask 預設為 5000 port
    app.run()
```

#### Heroku 後台設定環境變數參數
在本機端測試時可以加入本機電腦的環境變數，格式如下，由一個 key 對應一個 value 值（key 為自行命名）：

>環境變數為系統使用的變數，主要用來儲存參數設定值，讓系統中的程式可以讀取使用

$ 為終端機提示字元不用輸入

若是 Windows 作業系統的請於終端機使用指令：
```
$ set KEY=xxxxxxx

# 列印出 %KEY% 看是否有設置成功
$ echo %KEY%
```
若是 MacOS 或是 Linux 作業系統的環境變數設定方式如下：
```
$ export KEY=xxxxxxx

# 列印出 $環境變數名稱 看是否有成功
$ echo $KEY
```

將 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 加入環境變數測試：

Windows：
```
$ set LINE_CHANNEL_ACCESS_TOKEN=xxxxxxx
$ set LINE_CHANNEL_SECRET=xxxxxxx
```
列印出來看看：
```
$ echo %LINE_CHANNEL_ACCESS_TOKEN%
$ echo %LINE_CHANNEL_SECRET%
```
MacOS / Linux：
```
$ export LINE_CHANNEL_ACCESS_TOKEN=xxxxxxx
$ export LINE_CHANNEL_SECRET=xxxxxxx
```
列印出來看看：
```
$ echo LINE_CHANNEL_ACCESS_TOKEN
$ echo LINE_CHANNEL_SECRET
```
此時啟動 `python line_app.py` 應該可以成功啟動本機伺服器。

接著將 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 加入 Heroku 雲端伺服器環境變數，可在後台 `Settings` 設定，這樣我們之後部屬上去的程式就可以讀取到設定參數。


#### 建立 Heroku 部屬相關檔案
目前我們的專案檔案結構如下：
```
line_app.py
```
最後檔案結構會跟下面一樣：
```
line_app.py
requirements.txt
runtime.txt
Procfile
```
其中 `requirements.txt` 為指定要安裝哪些 Python 套件的文件檔案，`runtime.txt` 為指定運行程式語言的版本。`Procfile` 是告訴 Heroku 如何執行你的程式。由於 Flask 網頁框架內建的 Web 伺服器不適合於實際生產環境使用（開發時使用的 `python app.py` 或是 `flask run` 等方式啟動的開發伺服器），所以這邊我們會使用 gunicorn 這個工具來當我們的 Web Server。

`requirements.txt` 則為需要使用到的 Python 套件和版本：
```
gunicorn==20.0.4
Flask==1.1.1
line-bot-sdk==1.16.0
```
`runtime.txt` 為執行程式的版本：
```
python-3.7.3
```
`Procfile` 為告知 Heroku 如何執行網頁應用程式，其格式如下：
```
web: 執行指令 程式檔案名稱:flask app 實例變數名稱
```
`Procfile` 參考範例（–log-file - 為打開顯示除錯訊息）：
```
web: gunicorn line_app:app –log-file -
```
若不想顯示除錯訊息可以使用：
```
web: gunicorn line_app:app
```
#### 部屬到 Heroku 雲端伺服器
進入到 Heroku 後台的 deploy 部屬分頁，我們可以看到下面有指令教學。首先我們需要先安裝一下 Heroku CLI 指令列工具，請根據作業系統安裝對應的工具。

接著我們打開終端機輸入以下指令登入 Heroku，若尚未登入會跳出一個 Heroku 瀏覽器登入視窗。
```
$ heroku login
# heroku: Press any key to open up the browser to login or q to exit:
```
登入成功後即可關掉瀏覽器視窗：

若要登出換帳號可以使用：
```
$ heroku logout
```
接著移動到我們的專案資料夾（已經有）：
```
$ cd 資料夾名稱
```
初始化 Git repository 將工作資料夾變成 Git 追蹤的資料夾：
```
$ git init
```
將 remote 遠端程式庫位置設定為 heroku app（`-a` 為 application 意思）：`git:remote adds a git remote to an app repo`。
```
$ heroku git:remote -a 你的 heroku app 名稱
```
將檔案加入 git staging 暫存區：
```
$ git add xxxx
```
提交到本地程式庫：
```
$ git commit -a -m "first commit"
```
提交到遠端 Heroku（會看到一連串安裝套件和啟動伺服器訊息，若看到 `remote: Verifying deploy... done.` 代表成功 deploy 部屬）：
```
$ git push heroku master
```
若成功完成，此時就已經將我們的程式部屬到 Heroku 伺服器上了！



若要觀看 Heroku 伺服器顯示除錯訊息：
```
# --tail 代表持續印出
$ heroku logs --tail
```
若有修改或新增檔案，只要重複 `git add` 和 `git commit` 後 `git push heroku master` 步驟即可。

#### 設定 LINE Messaging API 的 Webhook URL
將我們的 Heroku App Webhook URL 提交到 LINE Bot 後台的 Webhook URL 區塊
```
https://{你的 heroku app 名稱}.herokuapp.com/callback
```
加入 LINE Bot QR Code 好友，就可以開始互動了！恭喜同學此時的 LINE Bot 聊天機器人就是透過我們的雲端伺服器而非本地端伺服器跟我們互動，就算是關掉電腦也可以用啦！

#### 常見 Heroku 指令
$ 為終端機提示字元，不用輸入

登入 Heroku
```
$ heroku login
```
推送到 Heroku
初始化 Git repository 將目前工作資料夾變成 Git 追蹤的資料夾：
```
$ git init
```
將 remote 遠端程式庫位置設定為 heroku app（`-a` 為 application 意思）：`git:remote adds a git remote to an app repo`。
```
$ heroku git:remote -a 你的 heroku app 名稱
```
將檔案加入 git staging 暫存區：
```
$ git add xxxx
```
提交到本地程式庫：
```
$ git commit -a -m "first commit"
```
提交到遠端 Heroku（會看到一連串安裝套件和啟動伺服器訊息，若看到 `remote: Verifying deploy... done`. 代表成功 deploy 部屬）：
```
$ git push heroku master
```
在 Heroku App Server 下指令
```
$ heroku run {終端機指令} -a {heroku app 名稱}
```
停止定時執行的 Heroku App
```
$ heroku ps:scale clock=0 -a {heroku app 名稱}
```
查詢 Heroku App log
```
$ heroku ps:scale clock=0 -a {heroku app 名稱}
```
總結
以上介紹了雲端伺服器（Cloud Server）概要以及如何使用 git 和 heroku 將我們的 LINE 聊天機器人部屬到 Heroku 雲端伺服器上。
